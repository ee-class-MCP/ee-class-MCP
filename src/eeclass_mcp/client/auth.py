"""Playwright-based headless authentication provider for NCU ee-class.

Maintained by the Headless Browser team.
"""

import logging

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from eeclass_mcp.client.protocol import AuthenticationError
from eeclass_mcp.config import Settings

logger = logging.getLogger(__name__)


class PlaywrightAuthProvider:
    """Authenticate against NCU ee-class via headless Chromium and export session cookies."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def login(self) -> dict[str, str]:
        """Log in with username/password and return cookies including PHPSESSID.

        TODO(browser-team): Inspect https://eeclass.ncu.edu.tw login form and update:
        - login URL path (if not '/index/login')
        - input selectors for account/password and submit button
        - post-login success check (URL redirect / DOM selector / PHPSESSID presence)
        """
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

                    # TODO(browser-team): Replace these placeholder selectors with actual selectors.
                    await page.fill('input[name="account"]', username)
                    await page.fill('input[name="password"]', password)
                    await page.click('button[type="submit"]')
                    await page.wait_for_load_state("networkidle")

                    cookies = await context.cookies()
                finally:
                    await browser.close()
        except PlaywrightTimeoutError as exc:
            raise AuthenticationError(f"Timed out during Playwright login: {exc}") from exc
        except Exception as exc:
            raise AuthenticationError(f"Playwright login failed: {exc}") from exc

        cookie_map = {cookie["name"]: cookie["value"] for cookie in cookies}
        if "PHPSESSID" not in cookie_map:
            raise AuthenticationError(
                "Login completed without acquiring PHPSESSID cookie. "
                "Verify credentials and login selectors in client/auth.py."
            )

        logger.info("Successfully acquired session cookies (%d cookies).", len(cookie_map))
        return cookie_map
