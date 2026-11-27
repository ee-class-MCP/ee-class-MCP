from pathlib import Path

import pytest

from eeclass_mcp.models.assignment import AssignmentStatus
from eeclass_mcp.parsers import parse_assignment_detail, parse_assignments, parse_latest_events

BASE = "https://ncueeclass.ncu.edu.tw"


def _load(name: str) -> str:
    return (Path(__file__).parent / "fixtures" / name).read_text(encoding="utf-8")


def _list_html(score: str, check: bool = True) -> str:
    icon = '<span class="fa-check"></span>' if check else ""
    return f"""<table id="homeworkListTable"><thead><tr>
<th>項次</th><th>名稱</th><th></th><th>分組作業</th><th>開放繳交</th><th>期限</th><th>繳交</th>
<th>分數</th><th>評語</th></tr></thead><tbody><tr><td>1</td>
<td><a href="/course/homework/9" title="HW"><span class="text">HW</span></a></td>
<td></td><td></td><td>10-01 00:00</td><td>10-02 00:00</td><td>{icon}</td><td>{score}</td><td></td>
</tr></tbody></table>"""


def test_homework_list_rows():
    items = parse_assignments(_load("course_homeworkList_40286.html"))
    assert [a.id for a in items] == ["73772", "75166", "75167"]
    first = items[0]
    assert first.title == "BA1 code上傳區"
    assert str(first.url) == f"{BASE}/course/homework/73772"
    assert first.open_at == "10-14 00:00"
    assert first.due_at == "10-15 13:00"
    assert first.status == AssignmentStatus.SUBMITTED
    assert first.score is None
    for item in items[1:]:
        assert item.status == AssignmentStatus.NOT_SUBMITTED
        assert item.score is None


def test_homework_list_course_id_passthrough():
    items = parse_assignments(_load("course_homeworkList_40286.html"), course_id=40286)
    assert {a.course_id for a in items} == {40286}


def test_homework_list_empty():
    assert parse_assignments(_load("course_homeworkList_42511.html")) == []


def test_homework_list_graded_numeric_score():
    (item,) = parse_assignments(_list_html("95"))
    assert item.status == AssignmentStatus.GRADED
    assert item.score == "95"
    assert item.open_at == "10-01 00:00"


def test_homework_list_not_submitted_inline():
    (item,) = parse_assignments(_list_html("-", check=False))
    assert item.status == AssignmentStatus.NOT_SUBMITTED
    assert item.score is None


@pytest.mark.parametrize(
    ("name", "hw_id", "title", "allow_late", "due", "weight"),
    [
        ("course_homework_72152.html", "72152", "Exercise 1", True, "2026-10-02 12:00", "5%"),
        (
            "course_homework_75575.html",
            "75575",
            "First Presentation – Slide Upload",
            False,
            "2026-12-03",
            "20%",
        ),
    ],
)
def test_homework_detail(name, hw_id, title, allow_late, due, weight):
    a = parse_assignment_detail(_load(name), hw_id)
    assert a.id == hw_id
    assert a.title == title
    assert str(a.url) == f"{BASE}/course/homework/{hw_id}"
    assert a.open_at
    assert a.due_at == due
    assert a.allow_late is allow_late
    assert a.weight == weight
    assert a.description
    assert "測試作業說明 1" in a.description
    assert "\n" in a.description
    assert a.attachments == []


def test_homework_detail_attachments():
    html = """<div class="app-course_homework-show">
<div class="fs-page-header"><div class="title">T</div></div>
<div class="fs-filelist"><a href="/filedownload/1/a.pdf"><span> a.pdf </span><small>1MB</small></a>
</div></div>"""
    (att,) = parse_assignment_detail(html, "1").attachments
    assert att.filename == "a.pdf"
    assert att.download_url == f"{BASE}/filedownload/1/a.pdf"


def test_homework_detail_missing_root():
    with pytest.raises(ValueError):
        parse_assignment_detail("<html><body></body></html>", "1")


def test_latest_events():
    items = parse_latest_events(_load("dashboard_latestEvent.html"))
    assert items
    first = items[0]
    assert first.id == "75575"
    assert first.course_id == 40304
    assert first.course_name == "圖探勘與最佳化 Graph Mining and Optimization"
    assert first.due_at == "2026-12-03 23:59:59"
    assert str(first.url) == f"{BASE}/course/homework/75575"


def test_latest_events_skips_non_homework_rows():
    html = """<table><tbody>
<tr><td><a href="/course/exam/5"><span class="text">Exam</span></a></td>
<td><a href="/course/1"><span class="text">C</span></a></td>
<td class="col-date"><div title="2026-01-01 00:00:00">2026-01-01</div></td></tr>
<tr><td>沒有資料</td></tr>
<tr><td><a href="/course/homework/7"><span class="text">HW</span></a></td>
<td><a href="/course/2"><span class="text">C2</span></a></td>
<td class="col-date"><div>2026-02-02</div></td></tr>
</tbody></table>"""
    items = parse_latest_events(html)
    assert [(a.id, a.due_at) for a in items] == [("7", "2026-02-02")]
