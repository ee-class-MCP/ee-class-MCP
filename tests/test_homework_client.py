"""Offline tests for the homework page fetchers."""

from pathlib import Path

import httpx
import pytest
import respx

from eeclass_mcp.client import (
    LATEST_EVENT_PATH,
    EeClassClientError,
    HttpxEeClassClient,
    fetch_homework_html,
    fetch_homework_list_html,
    fetch_latest_event_html,
    homework_list_path,
    homework_path,
)
from eeclass_mcp.config import Settings

BASE_URL = "https://ncueeclass.ncu.edu.tw"
FIXTURES = Path(__file__).parent / "fixtures"
ERROR_PAGE = "<html><body>權限不足</body></html>"


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class FakeClient:
    def __init__(self, html: str) -> None:
        self.html = html
        self.requested: list[str] = []

    async def get_html(self, path: str) -> str:
        self.requested.append(path)
        return self.html

    async def download_file(self, url_or_path, filename=None):
        raise NotImplementedError

    async def close(self) -> None:
        return None


class FakeAuth:
    def __init__(self) -> None:
        self.calls = 0

    async def login(self) -> dict[str, str]:
        self.calls += 1
        return {"PHPSESSID": "x"}


def test_path_builders() -> None:
    assert homework_list_path(40286) == "/course/homeworkList/40286"
    assert homework_path(72152) == "/course/homework/72152"
    assert LATEST_EVENT_PATH == "/dashboard/latestEvent"


@pytest.mark.parametrize("bad", [-1, True])
def test_path_builders_reject_invalid_ids(bad: int) -> None:
    with pytest.raises(ValueError):
        homework_list_path(bad)
    with pytest.raises(ValueError):
        homework_path(bad)


@pytest.mark.parametrize(
    "fixture", ["course_homeworkList_40286.html", "course_homeworkList_42511.html"]
)
async def test_fetch_homework_list_html(fixture: str) -> None:
    html = load_fixture(fixture)
    client = FakeClient(html)
    assert await fetch_homework_list_html(client, 40286) == html
    assert client.requested == ["/course/homeworkList/40286"]


async def test_fetch_homework_html() -> None:
    html = load_fixture("course_homework_72152.html")
    client = FakeClient(html)
    assert await fetch_homework_html(client, 72152) == html
    assert client.requested == ["/course/homework/72152"]


async def test_fetch_latest_event_html() -> None:
    html = load_fixture("dashboard_latestEvent.html")
    client = FakeClient(html)
    assert await fetch_latest_event_html(client) == html
    assert client.requested == ["/dashboard/latestEvent"]


async def test_unexpected_page_raises() -> None:
    client = FakeClient(ERROR_PAGE)
    with pytest.raises(EeClassClientError):
        await fetch_homework_list_html(client, 1)
    with pytest.raises(EeClassClientError):
        await fetch_homework_html(client, 1)
    with pytest.raises(EeClassClientError):
        await fetch_latest_event_html(client)


def make_client(auth: FakeAuth) -> tuple[HttpxEeClassClient, httpx.AsyncClient]:
    settings = Settings(_env_file=None, username="u", password="p", base_url=BASE_URL)
    http = httpx.AsyncClient(base_url=BASE_URL, follow_redirects=True)
    return HttpxEeClassClient(settings, auth, http_client=http), http


@respx.mock
async def test_fetch_with_real_client_sends_session_cookie() -> None:
    html = load_fixture("course_homework_72152.html")
    route = respx.get(f"{BASE_URL}/course/homework/72152").mock(
        return_value=httpx.Response(200, text=html)
    )
    auth = FakeAuth()
    client, http = make_client(auth)
    try:
        assert await fetch_homework_html(client, 72152) == html
    finally:
        await client.close()
        await http.aclose()

    assert "PHPSESSID=x" in route.calls.last.request.headers["cookie"]
    assert auth.calls == 1


@respx.mock
async def test_fetch_relogins_once_on_session_expiry() -> None:
    html = load_fixture("course_homework_72152.html")
    respx.get(f"{BASE_URL}/course/homework/72152").mock(
        side_effect=[
            httpx.Response(302, headers={"location": "/index/login"}),
            httpx.Response(200, text=html),
        ]
    )
    respx.get(f"{BASE_URL}/index/login").mock(
        return_value=httpx.Response(200, text="<html>login</html>")
    )
    auth = FakeAuth()
    client, http = make_client(auth)
    try:
        assert await fetch_homework_html(client, 72152) == html
    finally:
        await client.close()
        await http.aclose()

    assert auth.calls == 2
