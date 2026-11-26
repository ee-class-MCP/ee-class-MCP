"""Playwright-based headless authentication provider for NCU ee-class.

Maintained by the Headless Browser team.
"""

import logging

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from eeclass_mcp.client.protocol import AuthenticationError
from eeclass_mcp.config import Settings

logger = logging.getLogger(__name__)

# Verified against the live login page on 2026-11-19 (Playwright-Practice#1).
ACCOUNT_INPUT = "#login_form input[name=account]"
PASSWORD_INPUT = "#login_form input[name=password]"
SUBMIT_BUTTON = "#login_form button[type=submit]"
LOGIN_WAIT_SECONDS = 15


class PlaywrightAuthProvider:
    """Authenticate against NCU ee-class via headless Chromium and export session cookies."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def login(self) -> dict[str, str]:
        """Log in with username/password and return cookies including PHPSESSID.

        Success = the page leaves /index/login within LOGIN_WAIT_SECONDS.
        If ee-class asks whether to log out other devices, only "keep login" is clicked.
        A rejected login writes the lock file and every later call stops before trying,
        because NCU locks the account after repeated failures.
        """
        lock_file = self._settings.login_lock_file
        if lock_file.exists():
            raise AuthenticationError(
                f"A previous login was rejected ({lock_file}). Check the password, "
                "then delete this file to allow login again."
            )

        username = self._settings.username.strip()
        password = self._settings.password.get_secret_value()
        if not username or not password:
            raise AuthenticationError(
                "Missing credentials. Set EECLASS_USERNAME and EECLASS_PASSWORD in .env."
            )

        login_url = f"{self._settings.base_url.rstrip('/')}/index/login"
        logger.info(
            "Launching Playwright (headless=%s) to authenticate at %s",
            self._settings.headless,
            login_url,
        )

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self._settings.headless)
                try:
                    context = await browser.new_context()
                    page = await context.new_page()
                    await page.goto(login_url, wait_until="domcontentloaded")

                    await page.fill(ACCOUNT_INPUT, username)
                    await page.fill(PASSWORD_INPUT, password)
                    await page.click(SUBMIT_BUTTON)

                    # "Log out other devices?" dialog: click only "保持登入" (keep login),
                    # never "登出所有裝置". exact=True skips the "保持登入狀態" checkbox.
                    keep_button = page.get_by_text("保持登入", exact=True)
                    clicked_keep = False
                    left_login_page = False
                    for _ in range(LOGIN_WAIT_SECONDS * 2):  # check every 0.5 s
                        await page.wait_for_timeout(500)
                        if "/index/login" not in page.url:
                            left_login_page = True
                            break
                        if not clicked_keep and await keep_button.is_visible():
                            await keep_button.click()
                            clicked_keep = True

                    if left_login_page:
                        cookies = await context.cookies()
                    else:
                        page_text = await page.locator("body").inner_text()
                finally:
                    await browser.close()
        except PlaywrightTimeoutError as exc:
            raise AuthenticationError(f"Timed out during Playwright login: {exc}") from exc
        except Exception as exc:
            raise AuthenticationError(f"Playwright login failed: {exc}") from exc

        if not left_login_page:
            lock_file.write_text(page_text, encoding="utf-8")
            raise AuthenticationError(
                f"Still on the login page after {LOGIN_WAIT_SECONDS} s; the password was "
                f"probably rejected. Page text saved to {lock_file}; login is blocked until "
                "you delete it."
            )

        cookie_map = {cookie["name"]: cookie["value"] for cookie in cookies}
        if "PHPSESSID" not in cookie_map:
            raise AuthenticationError(
                "Login completed without acquiring PHPSESSID cookie. "
                "Verify credentials and login selectors in client/auth.py."
            )

        logger.info("Successfully acquired session cookies (%d cookies).", len(cookie_map))
        return cookie_map
