import pytest

from eeclass_mcp.client.auth import PlaywrightAuthProvider
from eeclass_mcp.client.protocol import AuthenticationError
from eeclass_mcp.config import Settings


async def test_login_refuses_while_lock_file_exists(tmp_path):
    """After a rejected login, no further attempt may reach ee-class (account lock risk)."""
    lock = tmp_path / "LOGIN_FAILED"
    lock.write_text("rejected", encoding="utf-8")
    settings = Settings(_env_file=None, username="s", password="p", login_lock_file=lock)

    with pytest.raises(AuthenticationError, match="previous login was rejected"):
        await PlaywrightAuthProvider(settings).login()
