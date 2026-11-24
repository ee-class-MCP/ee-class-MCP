"""Interface contract between the Headless Browser team (client) and MCP team (tools).

Both teams develop against these Protocols and exceptions so work can proceed in parallel.
"""

from typing import Protocol, runtime_checkable

from eeclass_mcp.models.download import DownloadedFile


class EeClassClientError(Exception):
    """Base exception for ee-class client failures."""


class AuthenticationError(EeClassClientError):
    """Raised when login credentials are missing or rejected."""


class SessionExpiredError(EeClassClientError):
    """Raised when session cookies expire and re-authentication fails."""


@runtime_checkable
class AuthProvider(Protocol):
    """Contract for acquiring authenticated session cookies (e.g. PHPSESSID)."""

    async def login(self) -> dict[str, str]:
        """Perform login and return session cookies mapped by cookie name."""
        ...


@runtime_checkable
class EeClassClient(Protocol):
    """Contract for fetching ee-class pages and downloading attachments."""

    async def get_html(self, path: str) -> str:
        """Fetch an authenticated HTML page by relative path or full URL."""
        ...

    async def download_file(
        self,
        url_or_path: str,
        filename: str | None = None,
    ) -> DownloadedFile:
        """Download an attachment to the local download directory."""
        ...

    async def close(self) -> None:
        """Release underlying HTTP/browser resources."""
        ...
