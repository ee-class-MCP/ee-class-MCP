"""Async httpx client with PHPSESSID cookie management, re-auth, and attachment downloads.

Maintained by the Headless Browser team.
"""

import asyncio
import logging
import re
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import httpx

from eeclass_mcp.client.protocol import AuthProvider, EeClassClientError, SessionExpiredError
from eeclass_mcp.config import Settings
from eeclass_mcp.models.download import DownloadedFile

logger = logging.getLogger(__name__)

_FILENAME_STAR_RE = re.compile(r"filename\*\s*=\s*(?:UTF-8|utf-8)''([^;\r\n]+)")
_FILENAME_RE = re.compile(r'filename\s*=\s*"?([^";\r\n]+)"?')


def _sanitize_filename(raw_name: str) -> str:
    """Strip directory components and unsafe characters from a downloaded filename."""
    # Replace backslashes first so Windows/Unix traversal segments are both flattened.
    basename = Path(raw_name.replace("\\", "/")).name.strip()
    if not basename or basename in {".", ".."}:
        return "downloaded_file"
    # Replace characters illegal on Windows/POSIX filesystems.
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", basename)


def _extract_filename(response: httpx.Response, fallback_url: str) -> str:
    """Determine a safe filename from Content-Disposition or the request URL."""
    disposition = response.headers.get("content-disposition", "")
    if match := _FILENAME_STAR_RE.search(disposition):
        return _sanitize_filename(unquote(match.group(1)))
    if match := _FILENAME_RE.search(disposition):
        return _sanitize_filename(unquote(match.group(1)))

    url_path = urlparse(str(response.url) or fallback_url).path
    candidate = Path(url_path).name
    return _sanitize_filename(unquote(candidate)) if candidate else "downloaded_file"


def _resolve_unique_path(directory: Path, filename: str) -> Path:
    """Avoid overwriting existing files by appending a numeric suffix when needed."""
    candidate = directory / filename
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    counter = 1
    while True:
        numbered = directory / f"{stem}_{counter}{suffix}"
        if not numbered.exists():
            return numbered
        counter += 1


class HttpxEeClassClient:
    """HTTP client backed by httpx.AsyncClient and an AuthProvider for PHPSESSID cookies."""

    def __init__(
        self,
        settings: Settings,
        auth_provider: AuthProvider,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = settings
        self._auth_provider = auth_provider
        self._base_url = settings.base_url.rstrip("/")
        self._client = http_client or httpx.AsyncClient(
            base_url=self._base_url,
            timeout=settings.request_timeout,
            follow_redirects=True,
            http2=True,
        )
        self._owns_client = http_client is None
        self._auth_lock = asyncio.Lock()
        self._authenticated = False

    async def ensure_authenticated(self, *, force: bool = False) -> None:
        """Ensure session cookies are loaded, using an async lock to avoid duplicate logins."""
        if self._authenticated and not force:
            return

        async with self._auth_lock:
            if self._authenticated and not force:
                return

            logger.info("Authenticating session (force=%s)...", force)
            cookies = await self._auth_provider.login()
            self._client.cookies.clear()
            for name, value in cookies.items():
                self._client.cookies.set(name, value)
            self._authenticated = True
            logger.debug("Injected %d session cookies into httpx client.", len(cookies))

    def _is_session_expired(self, response: httpx.Response) -> bool:
        """Detect if ee-class rejected the session or redirected back to the login page.

        TODO(browser-team): Refine these checks with real NCU ee-class behavior
        (e.g. specific login URL path or JSON error payload).
        """
        if response.status_code in {401, 403}:
            return True
        final_path = urlparse(str(response.url)).path.lower()
        return "/index/login" in final_path

    async def get_html(self, path: str) -> str:
        """Fetch an authenticated HTML page, automatically re-logging in once on expiry."""
        await self.ensure_authenticated()

        target = (
            path
            if path.startswith(("http://", "https://"))
            else urljoin(f"{self._base_url}/", path.lstrip("/"))
        )
        response = await self._client.get(target)

        if self._is_session_expired(response):
            logger.warning("Session expired while requesting %s; attempting re-login.", target)
            await self.ensure_authenticated(force=True)
            response = await self._client.get(target)
            if self._is_session_expired(response):
                raise SessionExpiredError(
                    f"Session remained unauthenticated after re-login for {target}"
                )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise EeClassClientError(
                f"HTTP {exc.response.status_code} while requesting {target}"
            ) from exc

        return response.text

    async def download_file(
        self,
        url_or_path: str,
        filename: str | None = None,
    ) -> DownloadedFile:
        """Stream an attachment directly into settings.download_dir."""
        await self.ensure_authenticated()

        download_dir = self._settings.download_dir.resolve()
        download_dir.mkdir(parents=True, exist_ok=True)

        target = (
            url_or_path
            if url_or_path.startswith(("http://", "https://"))
            else urljoin(f"{self._base_url}/", url_or_path.lstrip("/"))
        )

        for attempt in range(2):
            async with self._client.stream("GET", target) as response:
                if self._is_session_expired(response):
                    if attempt == 0:
                        logger.warning(
                            "Session expired during download of %s; re-logging in.", target
                        )
                        await self.ensure_authenticated(force=True)
                        continue
                    raise SessionExpiredError(
                        f"Session remained unauthenticated after re-login for {target}"
                    )

                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    raise EeClassClientError(
                        f"HTTP {exc.response.status_code} while downloading {target}"
                    ) from exc

                safe_name = (
                    _sanitize_filename(filename)
                    if filename
                    else _extract_filename(response, target)
                )
                dest_path = _resolve_unique_path(download_dir, safe_name)

                size_bytes = 0
                with dest_path.open("wb") as fp:
                    async for chunk in response.aiter_bytes():
                        fp.write(chunk)
                        size_bytes += len(chunk)

                content_type = response.headers.get("content-type")
                logger.info("Downloaded %s (%d bytes) -> %s", safe_name, size_bytes, dest_path)
                return DownloadedFile(
                    filename=dest_path.name,
                    saved_path=str(dest_path),
                    size_bytes=size_bytes,
                    content_type=content_type,
                    source_url=str(response.url),
                )

        raise SessionExpiredError(f"Failed to download {target} after re-authentication.")

    async def close(self) -> None:
        """Close the underlying httpx.AsyncClient if owned by this instance."""
        if self._owns_client:
            await self._client.aclose()
