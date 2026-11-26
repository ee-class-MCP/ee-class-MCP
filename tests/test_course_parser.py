"""Tests for parsers.course against a real (anonymized) /dashboard page."""

import pytest

from eeclass_mcp.models.course import Course
from eeclass_mcp.parsers.course import parse_courses

BASE_URL = "https://ncueeclass.ncu.edu.tw"


@pytest.fixture
def courses(load_fixture) -> list[Course]:
    return parse_courses(load_fixture("dashboard.html"), base_url=BASE_URL)


def test_parses_every_course_card(courses: list[Course]) -> None:
    assert len(courses) == 9
    assert len({c.id for c in courses}) == 9


def test_course_fields(courses: list[Course]) -> None:
    compiler = next(c for c in courses if c.id == 40286)
    assert compiler.code == "CE3006*"
    assert compiler.name == "編譯器 Compiler"
    assert compiler.instructor == "鄭永斌, 洪慧儒"
    assert compiler.url == f"{BASE_URL}/course/40286"


def test_every_course_has_code_and_absolute_url(courses: list[Course]) -> None:
    for course in courses:
        assert course.code
        assert course.url == f"{BASE_URL}/course/{course.id}"


def test_course_without_class_line_still_parses(courses: list[Course]) -> None:
    # The homeroom (導師班) card has 老師 and 代碼 but no 班級 line.
    homeroom = next(c for c in courses if c.code == "CE001J")
    assert homeroom.name == "資訊工程學系導師班"
    assert homeroom.instructor == "孫敏德"


def test_semester_is_not_on_dashboard(courses: list[Course]) -> None:
    # /dashboard lists the current courses without a semester label.
    assert all(c.semester is None for c in courses)


def _card(href: str, name: str, hints: list[str]) -> str:
    hint_html = "".join(f"<div>{h}</div>" for h in hints)
    return (
        '<li><div class="fs-imageEx">'
        f'<div class="fs-label"><a href="{href}">{name}</a></div>'
        f'<div class="fs-hint">{hint_html}</div>'
        "</div></li>"
    )


def test_card_without_code_is_skipped() -> None:
    html = '<ul class="clearfix">' + _card("/course/1", "No Code", ["老師: A"]) + "</ul>"
    assert parse_courses(html) == []


def test_english_labels_and_relative_url() -> None:
    html = (
        '<ul class="clearfix">'
        + _card("/course/7", "Compiler", ["Teacher: Alice", "Code: CE3006*"])
        + "</ul>"
    )
    [course] = parse_courses(html)
    assert course == Course(
        id=7, code="CE3006*", name="Compiler", instructor="Alice", url="/course/7"
    )
