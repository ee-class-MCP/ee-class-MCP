"""Shared application lifespan context passed to MCP tools."""

from dataclasses import dataclass

from mcp.server.mcpserver import Context

from eeclass_mcp.client.protocol import EeClassClient
from eeclass_mcp.config import Settings


@dataclass(slots=True)
class AppContext:
    """Resources initialized once during MCP server lifespan."""

    settings: Settings
    client: EeClassClient


def get_app_context(ctx: Context) -> AppContext:
    """Extract the typed AppContext from an MCP tool Context."""
    lifespan_ctx = ctx.request_context.lifespan_context
    if not isinstance(lifespan_ctx, AppContext):
        raise RuntimeError("Server lifespan context is not initialized.")
    return lifespan_ctx
