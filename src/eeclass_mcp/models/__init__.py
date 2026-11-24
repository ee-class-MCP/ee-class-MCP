"""Shared Pydantic models used across client, parsers, and MCP tools."""

from .announcement import Announcement
from .assignment import Assignment
from .course import Course
from .download import DownloadedFile
from .material import Attachment, MaterialItem

__all__ = [
    "Announcement",
    "Assignment",
    "Attachment",
    "Course",
    "DownloadedFile",
    "MaterialItem",
]
