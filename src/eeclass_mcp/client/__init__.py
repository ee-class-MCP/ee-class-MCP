"""Client layer (Playwright auth + httpx session & downloads)."""

from .auth import PlaywrightAuthProvider
from .http_client import HttpxEeClassClient
from .protocol import (
    AuthenticationError,
    AuthProvider,
    EeClassClient,
    EeClassClientError,
    SessionExpiredError,
)

__all__ = [
    "AuthProvider",
    "AuthenticationError",
    "EeClassClient",
    "EeClassClientError",
    "HttpxEeClassClient",
    "PlaywrightAuthProvider",
    "SessionExpiredError",
]
