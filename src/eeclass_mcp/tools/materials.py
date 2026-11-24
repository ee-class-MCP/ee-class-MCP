"""MCP tools for querying course materials and downloading attachments."""

import logging

from mcp.server.mcpserver import Context, MCPServer

from eeclass_mcp.app_context import get_app_context
from eeclass_mcp.models.download import DownloadedFile
from eeclass_mcp.models.material import MaterialItem
from eeclass_mcp.parsers.material import parse_materials

logger = logging.getLogger(__name__)


async def get_course_materials(ctx: Context, course_id: int) -> list[MaterialItem]:
    """List teaching materials and downloadable attachments for an NCU ee-class course.

    Args:
        course_id: The course ID on ee-class.
    """
    app = get_app_context(ctx)
    # TODO(mcp-team): Confirm the exact ee-class course materials path.
    html = await app.client.get_html(f"/course/material/{course_id}")
    materials = parse_materials(html, base_url=app.settings.base_url)

    logger.debug("Parsed %d materials for course %d.", len(materials), course_id)
    return materials


async def download_attachment(
    ctx: Context,
    download_url: str,
    filename: str | None = None,
) -> DownloadedFile:
    """Download a course attachment directly to the configured local download directory.

    Args:
        download_url: Attachment URL or relative path obtained from course materials.
        filename: Optional custom filename to save as (sanitized automatically).
    """
    app = get_app_context(ctx)
    result = await app.client.download_file(download_url, filename=filename)
    logger.info("Attachment downloaded to %s", result.saved_path)
    return result


def register(mcp: MCPServer) -> None:
    """Register material and download tools on the MCPServer."""
    mcp.tool()(get_course_materials)
    mcp.tool()(download_attachment)
