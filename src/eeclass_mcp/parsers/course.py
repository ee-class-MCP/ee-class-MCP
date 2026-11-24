"""HTML parser for NCU ee-class course list pages.

Maintained by the MCP team.
"""

import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from eeclass_mcp.models.course import Course

logger = logging.getLogger(__name__)
_COURSE_ID_RE = re.compile(r"/course/(\d+)")


def _extract_after_colon(text: str) -> str:
    """Return the trimmed value after ':' or '：'."""
    for sep in (":", "："):
        if sep in text:
            return text.split(sep, 1)[1].strip()
    return text.strip()


def parse_courses(html: str, base_url: str = "") -> list[Course]:
    """Parse course entries from NCU ee-class HTML."""
    soup = BeautifulSoup(html, "lxml")
    courses: list[Course] = []

    for card in soup.select("ul.clearfix > li .fs-imageEx"):
        link_el = card.select_one(".fs-label a[href]") or card.select_one('a[href*="/course/"]')
        if link_el is None:
            continue

        href = str(link_el.get("href", "")).strip()
        match = _COURSE_ID_RE.search(href)
        if not match:
            continue
        course_id = int(match.group(1))

        label_el = card.select_one(".fs-label a") or link_el
        name = " ".join(label_el.get_text().split())
        if not name:
            continue

        instructor: str | None = None
        code: str | None = None

        for hint_div in card.select(".fs-hint > div"):
            text = " ".join(hint_div.get_text().split())
            if not text:
                continue
            if text.startswith(("老師:", "老師：", "Teacher:", "Instructor:")):
                instructor = _extract_after_colon(text) or None
            elif text.startswith(("代碼:", "代碼：", "Code:", "Course Code:")):
                code = _extract_after_colon(text) or None

        if not code:
            logger.warning("Course %s (%s) missing course code; skipping.", course_id, name)
            continue

        full_url = urljoin(base_url, href) if base_url else href

        courses.append(
            Course(
                id=course_id,
                code=code,
                name=name,
                instructor=instructor,
                url=full_url,
            )
        )

    return courses
