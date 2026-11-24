"""HTML parser for NCU ee-class course announcements.

Maintained by the MCP team.
TODO(mcp-team): Verify CSS selectors against anonymized real ee-class HTML fixtures.
"""

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from eeclass_mcp.models.announcement import Announcement


def parse_announcements(html: str, base_url: str = "") -> list[Announcement]:
    """Parse course announcements from ee-class HTML."""
    soup = BeautifulSoup(html, "lxml")
    announcements: list[Announcement] = []

    for item in soup.select(".announcement-item[data-announcement-id]"):
        ann_id = str(item.get("data-announcement-id", "")).strip()
        title_el = item.select_one(".announcement-title")
        if not ann_id or title_el is None:
            continue

        author_el = item.select_one(".announcement-author")
        date_el = item.select_one(".announcement-date")
        content_el = item.select_one(".announcement-content")
        href = title_el.get("href")
        full_url = (
            urljoin(base_url, str(href)) if href and base_url else (str(href) if href else None)
        )

        announcements.append(
            Announcement(
                id=ann_id,
                title=title_el.get_text(strip=True),
                author=author_el.get_text(strip=True) if author_el else None,
                published_at=date_el.get_text(strip=True) if date_el else None,
                content=content_el.get_text(strip=True) if content_el else None,
                url=full_url,
            )
        )

    return announcements
