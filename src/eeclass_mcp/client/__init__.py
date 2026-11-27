"""Client layer (Playwright auth + httpx session & downloads)."""

from .auth import PlaywrightAuthProvider
from .homework import (
    LATEST_EVENT_PATH,
    fetch_homework_html,
    fetch_homework_list_html,
    fetch_latest_event_html,
    homework_list_path,
    homework_path,
)
from .http_client import HttpxEeClassClient
from .protocol import (
    AuthenticationError,
    AuthProvider,
    EeClassClient,
    EeClassClientError,
    SessionExpiredError,
)

__all__ = [
    "LATEST_EVENT_PATH",
    "AuthProvider",
    "AuthenticationError",
    "EeClassClient",
    "EeClassClientError",
    "HttpxEeClassClient",
    "PlaywrightAuthProvider",
    "SessionExpiredError",
    "fetch_homework_html",
    "fetch_homework_list_html",
    "fetch_latest_event_html",
    "homework_list_path",
    "homework_path",
]
