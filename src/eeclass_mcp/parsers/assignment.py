"""HTML parsers for NCU ee-class homework pages (list, detail and latest events)."""

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from eeclass_mcp.models.assignment import Assignment, AssignmentStatus
from eeclass_mcp.models.material import Attachment

# Assignment.url is HttpUrl, so relative hrefs must be resolved against an absolute base.
DEFAULT_BASE_URL = "https://ncueeclass.ncu.edu.tw"

_HOMEWORK_HREF = re.compile(r"^/course/homework/(\d+)")
_COURSE_HREF = re.compile(r"^/course/(\d+)$")
_NO_SCORE = {"", "-", "尚未批改"}

# Fallback positions in /course/homeworkList when the thead cannot be read.
_DEFAULT_COLUMNS = {"名稱": 1, "開放繳交": 4, "期限": 5, "繳交": 6, "分數": 7}


def _text(el: Tag | None) -> str | None:
    if el is None:
        return None
    text = el.get_text(strip=True)
    return text or None


def _column_map(table: Tag) -> dict[str, int]:
    headers = [th.get_text(strip=True) for th in table.select("thead th")]
    found = {name: headers.index(name) for name in _DEFAULT_COLUMNS if name in headers}
    return {**_DEFAULT_COLUMNS, **found}


def _cell(cells: list[Tag], index: int) -> Tag | None:
    return cells[index] if index < len(cells) else None


def _list_status(submitted: bool, score: str | None) -> AssignmentStatus:
    # List dates carry no year, so MISSED / NOT_STARTED are not derived here: doing so
    # would need a clock and a guessed year.
    if score is not None:
        return AssignmentStatus.GRADED
    return AssignmentStatus.SUBMITTED if submitted else AssignmentStatus.NOT_SUBMITTED


def parse_assignments(
    html: str, base_url: str = DEFAULT_BASE_URL, course_id: int | None = None
) -> list[Assignment]:
    """Parse `/course/homeworkList/{course_id}` into assignments."""
    soup = BeautifulSoup(html, "lxml")
    table = soup.select_one("#homeworkListTable")
    if table is None:
        return []
    columns = _column_map(table)
    assignments: list[Assignment] = []

    for row in table.select("tbody tr"):
        cells = row.find_all("td", recursive=False)
        link = row.select_one('a[href^="/course/homework/"]')
        match = _HOMEWORK_HREF.match(str(link.get("href"))) if link else None
        if link is None or match is None:
            continue

        title = _text(link.select_one("span.text")) or str(link.get("title") or "")
        score = _text(_cell(cells, columns["分數"]))
        if score in _NO_SCORE:
            score = None
        submit_cell = _cell(cells, columns["繳交"])
        submitted = submit_cell is not None and submit_cell.select_one(".fa-check") is not None

        assignments.append(
            Assignment(
                id=match.group(1),
                title=title or link.get_text(strip=True),
                url=urljoin(base_url, str(link.get("href"))),
                open_at=_text(_cell(cells, columns["開放繳交"])),
                due_at=_text(_cell(cells, columns["期限"])),
                score=score,
                status=_list_status(submitted, score),
                course_id=course_id,
            )
        )

    return assignments


def _detail_fields(root: Tag) -> dict[str, Tag]:
    fields: dict[str, Tag] = {}
    for dt in root.select(".fs-description dl.dl-horizontal > dt"):
        dd = dt.find_next_sibling("dd")
        if isinstance(dd, Tag):
            fields[dt.get_text(strip=True)] = dd
    return fields


def _parse_attachments(root: Tag, base_url: str) -> list[Attachment]:
    attachments: list[Attachment] = []
    for link in root.select('.fs-filelist a[href^="/filedownload/"]'):
        name = next(link.stripped_strings, None)
        if name:
            attachments.append(
                Attachment(filename=name, download_url=urljoin(base_url, str(link.get("href"))))
            )
    return attachments


def parse_assignment_detail(
    html: str, assignment_id: str, base_url: str = DEFAULT_BASE_URL
) -> Assignment:
    """Parse a single `/course/homework/{id}` page."""
    soup = BeautifulSoup(html, "lxml")
    root = soup.select_one(".app-course_homework-show")
    if root is None:
        raise ValueError("Not a homework page: .app-course_homework-show not found")

    fields = _detail_fields(root)
    description_el = fields.get("說明")
    description = "\n".join(description_el.stripped_strings) if description_el else None

    return Assignment(
        id=assignment_id,
        title=_text(root.select_one(".fs-page-header .title")) or "",
        url=urljoin(base_url, f"/course/homework/{assignment_id}"),
        open_at=_text(fields.get("開放繳交")),
        due_at=_text(fields.get("繳交期限")),
        allow_late=_text(fields.get("允許遲交")) == "是",
        weight=_text(fields.get("成績比重")),
        description=description or None,
        attachments=_parse_attachments(root, base_url),
    )


def parse_latest_events(html: str, base_url: str = DEFAULT_BASE_URL) -> list[Assignment]:
    """Parse `/dashboard/latestEvent`, keeping only homework events."""
    soup = BeautifulSoup(html, "lxml")
    assignments: list[Assignment] = []

    for row in soup.select("table tbody tr"):
        links = row.select("a[href]")
        date_el = row.select_one("td.col-date div")
        if len(links) < 2 or date_el is None:
            continue
        hw_match = _HOMEWORK_HREF.match(str(links[0].get("href")))
        course_match = _COURSE_HREF.match(str(links[1].get("href")))
        if hw_match is None or course_match is None:
            continue

        assignments.append(
            Assignment(
                id=hw_match.group(1),
                title=_text(links[0].select_one("span.text")) or links[0].get_text(strip=True),
                url=urljoin(base_url, str(links[0].get("href"))),
                course_id=int(course_match.group(1)),
                course_name=_text(links[1].select_one("span.text")) or _text(links[1]),
                due_at=str(date_el.get("title") or "") or _text(date_el),
            )
        )

    return assignments
