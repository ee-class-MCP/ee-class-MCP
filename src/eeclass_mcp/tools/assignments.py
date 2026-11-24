"""MCP tools for querying course assignments."""

import logging

from mcp.server.mcpserver import Context, MCPServer

from eeclass_mcp.app_context import get_app_context
from eeclass_mcp.models.assignment import Assignment
from eeclass_mcp.parsers.assignment import parse_assignments

logger = logging.getLogger(__name__)


async def get_course_assignments(ctx: Context, course_id: int) -> list[Assignment]:
    """Get assignments and submission statuses for a specific NCU ee-class course.

    Args:
        course_id: The course ID on ee-class.
    """
    app = get_app_context(ctx)
    # TODO(mcp-team): Confirm the exact ee-class course homework list path.
    html = await app.client.get_html(f"/course/homeworkList/{course_id}")
    assignments = parse_assignments(html, base_url=app.settings.base_url)

    logger.debug("Parsed %d assignments for course %d.", len(assignments), course_id)
    return assignments


def register(mcp: MCPServer) -> None:
    """Register assignment-related tools on the MCPServer."""
    mcp.tool()(get_course_assignments)
