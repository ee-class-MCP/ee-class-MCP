"""HTML parser for NCU ee-class course assignments.

Maintained by the MCP team.
TODO(mcp-team): Verify CSS selectors against anonymized real ee-class HTML fixtures.
"""

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from eeclass_mcp.models.assignment import Assignment, AssignmentStatus


def parse_assignments(html: str, base_url: str = "") -> list[Assignment]:
    """Parse course assignments from ee-class HTML."""
    soup = BeautifulSoup(html, "lxml")
    assignments: list[Assignment] = []

    for row in soup.select(".assignment-row[data-assignment-id]"):
        hw_id = str(row.get("data-assignment-id", "")).strip()
        title_el = row.select_one(".assignment-title")
        if not hw_id or title_el is None:
            continue

        due_el = row.select_one(".assignment-due")
        status_el = row.select_one(".assignment-status")
        score_el = row.select_one(".assignment-score")
        href = title_el.get("href")
        full_url = (
            urljoin(base_url, str(href)) if href and base_url else (str(href) if href else None)
        )

        score_text = score_el.get_text(strip=True) if score_el else None
        if score_text == "-":
            score_text = None

        assignments.append(
            Assignment(
                id=hw_id,
                title=title_el.get_text(strip=True),
                due_at=due_el.get_text(strip=True) if due_el else None,
                status=status_el.get_text(strip=True) if status_el else None,
                score=score_text,
                url=full_url,
            )
        )

    return assignments
