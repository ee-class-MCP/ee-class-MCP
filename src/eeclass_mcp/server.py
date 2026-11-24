"""MCP Server entry point for NCU ee-class."""

import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from mcp.server.mcpserver import MCPServer

from eeclass_mcp.app_context import AppContext
from eeclass_mcp.client.auth import PlaywrightAuthProvider
from eeclass_mcp.client.http_client import HttpxEeClassClient
from eeclass_mcp.client.protocol import EeClassClient
from eeclass_mcp.config import Settings
from eeclass_mcp.logging_config import setup_logging
from eeclass_mcp.tools import register_tools

logger = logging.getLogger(__name__)


def create_server(
    settings: Settings | None = None,
    client_factory: Callable[[Settings], EeClassClient] | None = None,
) -> MCPServer[AppContext]:
    """Create and configure the ee-class MCPServer instance."""
    resolved_settings = settings or Settings()
    setup_logging(resolved_settings.log_level)

    def _default_client_factory(cfg: Settings) -> EeClassClient:
        auth_provider = PlaywrightAuthProvider(cfg)
        return HttpxEeClassClient(cfg, auth_provider)

    factory = client_factory or _default_client_factory

    @asynccontextmanager
    async def lifespan(_: MCPServer[AppContext]) -> AsyncIterator[AppContext]:
        client = factory(resolved_settings)
        logger.info("eeclass-mcp server initialized (base_url=%s).", resolved_settings.base_url)
        try:
            yield AppContext(settings=resolved_settings, client=client)
        finally:
            await client.close()
            logger.info("eeclass-mcp server shut down cleanly.")

    mcp = MCPServer[AppContext](
        name="eeclass-mcp",
        instructions=(
            "Read-only assistant for National Central University (NCU) ee-class LMS. "
            "Use these tools to browse courses, announcements, assignments, and materials, "
            "or download course attachments locally."
        ),
        log_level=resolved_settings.log_level,
        lifespan=lifespan,
    )
    register_tools(mcp)
    return mcp


# Default module-level server instance for `mcp dev` or direct ASGI/CLI usage.
mcp = create_server()


def main() -> None:
    """CLI entry point running the MCP server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
