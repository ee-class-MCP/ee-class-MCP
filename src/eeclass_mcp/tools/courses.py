"""MCP tools for querying enrolled courses."""

import logging

from mcp.server.mcpserver import Context, MCPServer

from eeclass_mcp.app_context import get_app_context
from eeclass_mcp.models.course import Course
from eeclass_mcp.parsers.course import parse_courses

logger = logging.getLogger(__name__)


async def list_courses(ctx: Context, semester: str | None = None) -> list[Course]:
    """List courses enrolled by the current user on NCU ee-class.

    Args:
        semester: Optional semester filter (e.g. "114-1"). Returns all courses if omitted.
    """
    app = get_app_context(ctx)
    html = await app.client.get_html("/dashboard")
    courses = parse_courses(html, base_url=app.settings.base_url)

    if semester:
        courses = [c for c in courses if c.semester == semester]

    logger.debug("Parsed %d courses (semester=%s).", len(courses), semester)
    return courses


def register(mcp: MCPServer) -> None:
    """Register course-related tools on the MCPServer."""
    mcp.tool()(list_courses)
