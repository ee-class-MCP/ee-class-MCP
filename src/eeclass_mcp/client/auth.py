"""Playwright-based headless authentication provider for NCU ee-class.

Maintained by the Headless Browser team.

Login flow (verified against https://ncueeclass.ncu.edu.tw/index/login):
- The page renders ``form#login_form`` with ``input[name=account]``, ``input[name=password]``
  and hidden ``next`` / ``act`` / ``anticsrf`` fields.
- The submit button (``[data-role=form-submit]``) is intercepted by JS, which POSTs the form
  to ``/index/login`` via AJAX and gets back JSON. ``ret.status == "false"`` means the login
  was rejected; otherwise the page JS redirects away from ``/index/login``.
- PHP issues a ``PHPSESSID`` cookie before login, so the cookie alone does not prove success.
  Success is detected by leaving the login page.
"""

import logging
import re
from contextlib import suppress
from typing import Any
from urllib.parse import urlparse

from playwright.async_api import Dialog, Page, Response, async_playwright
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from eeclass_mcp.client.protocol import AuthenticationError
from eeclass_mcp.config import Settings

logger = logging.getLogger(__name__)

LOGIN_PATH = "/index/login"
_FORM = "#login_form"
_ACCOUNT_INPUT = f'{_FORM} input[name="account"]'
_PASSWORD_INPUT = f'{_FORM} input[name="password"]'
_SUBMIT_BUTTON = f'{_FORM} [data-role="form-submit"]'
_MULTI_LOGIN_MODAL = "#checkMultiLogin_modal"
_CLICKABLE = 'button, a, input[type="submit"], input[type="button"]'
_CONFIRM_TEXT = re.compile(r"確定|確認|繼續|登入|是|OK|Yes|Continue|Log ?in", re.IGNORECASE)
_KEEP_LOGIN_TEXT = re.compile(r"保持登入|Keep", re.IGNORECASE)
_LOGOUT_TEXT = re.compile(r"登出|Log ?out|Sign ?out", re.IGNORECASE)
_CANCEL_TEXT = re.compile(r"取消|否|關閉|Cancel|No\b|Close", re.IGNORECASE)
# Describe each clickable element without echoing query strings (they carry ajaxAuth tokens).
_DESCRIBE_CLICKABLES_JS = """(body, selector) => [...body.querySelectorAll(selector)].map(
    (e, i) => ({
        i,
        tag: e.tagName.toLowerCase(),
        type: e.getAttribute('type') || '',
        role: e.dataset.role || '',
        dismiss: e.dataset.dismiss || '',
        text: (e.innerText || e.value || '').trim().slice(0, 40),
        href: (e.getAttribute('href') || '').split('?')[0],
        visible: !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length),
    }))"""
# How long to wait for the page's own JS redirect before looking for the multi-login modal.
_REDIRECT_GRACE_MS = 5000
_MODAL_WAIT_MS = 2000


def _describe_payload(payload: Any) -> str:
    """Summarize the AJAX login response without echoing tokens or credentials."""
    if payload is None:
        return "not JSON"
    if not isinstance(payload, dict):
        return f"JSON {type(payload).__name__}"
    ret = payload.get("ret")
    if not isinstance(ret, dict):
        return f"keys={sorted(payload)}"
    msg = next((ret[k] for k in ("msg", "message", "error") if isinstance(ret.get(k), str)), "")
    summary = f"ret.status={ret.get('status')!r}, ret.msg={msg[:200]!r}, ret.keys={sorted(ret)}"
    action = ret.get("action")
    if isinstance(action, dict):
        # fmc.handleCompleted() in fmc.js acts on these keys (redir, reload, customJs, ...).
        summary += f", action.keys={sorted(action)}"
        for key, value in action.items():
            if isinstance(value, str):
                shown = urlparse(value).path if key in ("redir", "parentUrl") else value[:60]
                summary += f", action.{key}={shown!r}"
            elif isinstance(value, bool | int | list):
                summary += f", action.{key}={value!r}"[:120]
    elif action is not None:
        summary += f", action={type(action).__name__}"
    return summary


async def _confirm_multi_login(page: Page) -> str | None:
    """Confirm ee-class's "already logged in elsewhere" modal if it is shown.

    After a successful AJAX login, the server may answer with ``action.customJs`` that opens
    ``#checkMultiLogin_modal``. Its body is loaded via AJAX from
    ``/ajax/sys.pages.index/checkMultiLogin/`` and offers two links: "登出所有裝置" (log out
    every other session) and "保持登入" (keep them). We click "保持登入" so the user's own
    browser session survives. Returns the modal text if confirmed, otherwise None.
    """
    modal = page.locator(_MULTI_LOGIN_MODAL)
    try:
        await modal.wait_for(state="visible", timeout=_MODAL_WAIT_MS)
    except PlaywrightTimeoutError:
        return None

    body = modal.locator(".modal-body")
    clickables = body.locator(_CLICKABLE)
    try:
        # The body says "loading ..." until the AJAX content arrives.
        await clickables.first.wait_for(state="visible")
    except PlaywrightTimeoutError as exc:
        text = " ".join((await body.inner_text()).split())[:200]
        raise AuthenticationError(
            f"Multi-login modal never showed a button. Modal text: {text!r}"
        ) from exc

    text = " ".join((await body.inner_text()).split())[:200]
    candidates: list[dict[str, Any]] = await body.evaluate(_DESCRIBE_CLICKABLES_JS, _CLICKABLE)
    index = _pick_confirm_button(candidates)
    if index is None:
        raise AuthenticationError(
            "Multi-login modal has no recognizable confirm button. "
            f"Modal text: {text!r}. Buttons: {candidates}"
        )

    logger.info(
        "ee-class says this account is already logged in elsewhere; keeping both sessions. "
        "Modal text: %r, clicking: %s",
        text,
        candidates[index],
    )
    await clickables.nth(index).click()
    return text


def _pick_confirm_button(candidates: list[dict[str, Any]]) -> int | None:
    """Choose the "continue logging in" button among the modal's clickable elements."""

    def is_cancel(c: dict[str, Any]) -> bool:
        return (
            c.get("role") == "form-cancel"
            or bool(c.get("dismiss"))
            or bool(_CANCEL_TEXT.search(c.get("text", "")))
        )

    visible = [c for c in candidates if c.get("visible") and not is_cancel(c)]
    # Prefer "保持登入" (keep both sessions); never pick "登出所有裝置" (logs the user out
    # of their own browser).
    for c in visible:
        if _KEEP_LOGIN_TEXT.search(c.get("text", "")):
            return c["i"]
    visible = [c for c in visible if not _LOGOUT_TEXT.search(c.get("text", ""))]
    for c in visible:
        if c.get("role") == "form-submit" or c.get("type") == "submit":
            return c["i"]
    for c in visible:
        if _CONFIRM_TEXT.search(c.get("text", "")):
            return c["i"]
    return visible[0]["i"] if len(visible) == 1 else None


async def _visible_form_message(page: Page) -> str:
    """Return any error/notice text the login page shows (for diagnostics only)."""
    try:
        texts = await page.locator(
            ".fs-form-message, .help-block, .alert, .text-danger, .has-error"
        ).all_inner_texts()
    except PlaywrightError:
        return ""
    return " | ".join(t.strip() for t in texts if t.strip())[:300]


def _is_login_path(url: str) -> bool:
    return urlparse(url).path.rstrip("/").lower() == LOGIN_PATH


def _is_login_post(response: Response) -> bool:
    return response.request.method == "POST" and _is_login_path(response.url)


def _rejection_message(payload: Any) -> str | None:
    """Return a human-readable reason if the AJAX login response says it failed."""
    if not isinstance(payload, dict):
        return None
    ret = payload.get("ret")
    if not isinstance(ret, dict) or str(ret.get("status")).lower() != "false":
        return None
    for key in ("msg", "message", "error"):
        if isinstance(ret.get(key), str) and ret[key].strip():
            return ret[key].strip()
    return "ee-class rejected the login (wrong account or password?)."


class PlaywrightAuthProvider:
    """Authenticate against NCU ee-class via headless Chromium and export session cookies."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def login(self) -> dict[str, str]:
        """Log in with username/password and return the session cookies (incl. PHPSESSID)."""
        username = self._settings.username.strip()
        password = self._settings.password.get_secret_value()
        if not username or not password:
            raise AuthenticationError(
                "Missing credentials. Set EECLASS_USERNAME and EECLASS_PASSWORD in .env."
            )

        login_url = f"{self._settings.base_url.rstrip('/')}{LOGIN_PATH}"
        timeout_ms = self._settings.request_timeout * 1000
        logger.info(
            "Launching Playwright (headless=%s) to authenticate at %s",
            self._settings.headless,
            login_url,
        )

        dashboard_url = f"{self._settings.base_url.rstrip('/')}/dashboard"
        dialogs: list[str] = []
        notes: list[str] = []

        async def _accept_dialog(dialog: Dialog) -> None:
            # Playwright dismisses dialogs by default, which would cancel a
            # "continue logging in?" confirm. Accept and remember the text instead.
            dialogs.append(f"{dialog.type}: {dialog.message}")
            logger.info("Login page dialog (%s): %s", dialog.type, dialog.message)
            await dialog.accept()

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self._settings.headless)
                try:
                    context = await browser.new_context()
                    context.set_default_timeout(timeout_ms)
                    page = await context.new_page()
                    page.on("dialog", _accept_dialog)
                    await page.goto(login_url, wait_until="domcontentloaded")
                    payload = await self._submit_login_form(page, username, password)

                    # The page JS normally redirects after a successful AJAX login.
                    try:
                        await page.wait_for_url(
                            lambda url: not _is_login_path(url), timeout=_REDIRECT_GRACE_MS
                        )
                    except PlaywrightTimeoutError:
                        # Same account already logged in elsewhere: ee-class shows a modal
                        # whose form must be confirmed before the new session is valid.
                        modal_text = await _confirm_multi_login(page)
                        if modal_text is not None:
                            notes.append(f"multi-login modal confirmed: {modal_text!r}")
                            with suppress(PlaywrightTimeoutError):
                                await page.wait_for_url(lambda url: not _is_login_path(url))

                    if _is_login_path(page.url):
                        # No redirect: ask the server directly whether we are logged in.
                        notice = await _visible_form_message(page)
                        logger.info(
                            "No redirect after login (at %s, page message: %r); probing %s",
                            urlparse(page.url).path,
                            notice,
                            dashboard_url,
                        )
                        await page.goto(dashboard_url, wait_until="domcontentloaded")

                    if _is_login_path(page.url):
                        raise AuthenticationError(
                            "Still on the login page after submitting the form. "
                            f"Login response: {_describe_payload(payload)}. "
                            f"Dialogs: {dialogs or 'none'}. Notes: {notes or 'none'}."
                        )
                    cookies = await context.cookies()
                finally:
                    await browser.close()
        except AuthenticationError:
            raise
        except PlaywrightTimeoutError as exc:
            raise AuthenticationError(
                f"Timed out during Playwright login: {exc}. "
                "Check the selectors in client/auth.py or raise EECLASS_REQUEST_TIMEOUT."
            ) from exc
        except PlaywrightError as exc:
            raise AuthenticationError(f"Playwright login failed: {exc}") from exc

        cookie_map = {cookie["name"]: cookie["value"] for cookie in cookies}
        if "PHPSESSID" not in cookie_map:
            raise AuthenticationError(
                "Login completed without acquiring PHPSESSID cookie. "
                "Verify credentials and login selectors in client/auth.py."
            )

        logger.info("Successfully acquired session cookies (%d cookies).", len(cookie_map))
        return cookie_map

    @staticmethod
    async def _submit_login_form(page: Page, username: str, password: str) -> Any:
        """Fill the login form, submit it, and raise if the AJAX response rejects it.

        Returns the parsed JSON response (or None) for diagnostics.
        """
        await page.fill(_ACCOUNT_INPUT, username)
        await page.fill(_PASSWORD_INPUT, password)

        async with page.expect_response(_is_login_post) as response_info:
            await page.click(_SUBMIT_BUTTON)
        response = await response_info.value

        try:
            payload = await response.json()
        except PlaywrightError, ValueError:
            # Not JSON (e.g. a plain redirect); let the URL check decide.
            payload = None

        logger.debug("Login response: %s", _describe_payload(payload))
        if reason := _rejection_message(payload):
            raise AuthenticationError(f"Login rejected by ee-class: {reason}")
        return payload
