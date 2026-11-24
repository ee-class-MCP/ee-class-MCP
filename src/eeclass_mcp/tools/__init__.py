"""MCP tools registration entry point."""

from mcp.server.mcpserver import MCPServer

from . import announcements, assignments, courses, materials


def register_tools(mcp: MCPServer) -> None:
    """Register all ee-class MCP tools on the given MCPServer instance."""
    courses.register(mcp)
    announcements.register(mcp)
    assignments.register(mcp)
    materials.register(mcp)
