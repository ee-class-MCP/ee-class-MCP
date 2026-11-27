"""Fetch the raw HTML of ee-class homework pages.

Maintained by the Headless Browser team. Parsing lives in ``parsers/``.
"""

import logging
import re

from eeclass_mcp.client.protocol import EeClassClient, EeClassClientError

logger = logging.getLogger(__name__)

LATEST_EVENT_PATH = "/dashboard/latestEvent"

_HOMEWORK_LIST_MARKER = re.compile(r"""\bid\s*=\s*["']homeworkListTable["']""")
_HOMEWORK_PAGE_MARKER = re.compile(r"""\bclass\s*=\s*["'][^"']*\bapp-course_homework-show\b""")
_LATEST_EVENT_MARKER = re.compile(r"<table\b", re.IGNORECASE)


def _validate_id(value: int, name: str) -> int:
    # bool is an int subclass, so True would otherwise slip through as id 1.
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer, got {value!r}")
    return value


def homework_list_path(course_id: int) -> str:
    """Path of one course's homework list page."""
    return f"/course/homeworkList/{_validate_id(course_id, 'course_id')}"


def homework_path(homework_id: int) -> str:
    """Path of a single homework page."""
    return f"/course/homework/{_validate_id(homework_id, 'homework_id')}"


async def _fetch_checked(
    client: EeClassClient, path: str, marker: re.Pattern[str], description: str
) -> str:
    html = await client.get_html(path)
    logger.debug("Fetched %s (%d chars)", path, len(html))
    # ee-class can answer 200 with an error/permission page (e.g. a course the user is not
    # enrolled in); handing that to parsers would silently yield empty results.
    if not marker.search(html):
        raise EeClassClientError(
            f"Response for {path} does not look like {description}; "
            "the page may be an error or permission page."
        )
    return html


async def fetch_homework_list_html(client: EeClassClient, course_id: int) -> str:
    """Fetch the homework list page HTML of a course."""
    return await _fetch_checked(
        client, homework_list_path(course_id), _HOMEWORK_LIST_MARKER, "a homework list page"
    )


async def fetch_homework_html(client: EeClassClient, homework_id: int) -> str:
    """Fetch the HTML of a single homework page."""
    return await _fetch_checked(
        client, homework_path(homework_id), _HOMEWORK_PAGE_MARKER, "a homework page"
    )


async def fetch_latest_event_html(client: EeClassClient) -> str:
    """Fetch the dashboard's upcoming events/deadlines HTML."""
    return await _fetch_checked(
        client, LATEST_EVENT_PATH, _LATEST_EVENT_MARKER, "the latest events page"
    )
