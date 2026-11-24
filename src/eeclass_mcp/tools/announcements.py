"""MCP tools for querying course announcements."""

import logging

from mcp.server.mcpserver import Context, MCPServer

from eeclass_mcp.app_context import get_app_context
from eeclass_mcp.models.announcement import Announcement
from eeclass_mcp.parsers.announcement import parse_announcements

logger = logging.getLogger(__name__)


async def get_course_announcements(ctx: Context, course_id: int) -> list[Announcement]:
    """Get announcements for a specific NCU ee-class course.

    Args:
        course_id: The course ID on ee-class.
    """
    app = get_app_context(ctx)
    # TODO(mcp-team): Confirm the exact ee-class course announcements path.
    html = await app.client.get_html(f"/course/bulletin/{course_id}")
    announcements = parse_announcements(html, base_url=app.settings.base_url)

    logger.debug("Parsed %d announcements for course %d.", len(announcements), course_id)
    return announcements


def register(mcp: MCPServer) -> None:
    """Register announcement-related tools on the MCPServer."""
    mcp.tool()(get_course_announcements)
