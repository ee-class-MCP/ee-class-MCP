"""Capture real ee-class pages as anonymized HTML fixtures for unit tests.

Usage (credentials are read from .env, never passed on the command line):

    uv run python scripts/capture_fixtures.py /dashboard
    uv run python scripts/capture_fixtures.py /dashboard /dashboard/latestEvent --redact "王小明"
    uv run python scripts/capture_fixtures.py /dashboard --redact "王小明" --offline  # no login

For every path it writes:
- tests/fixtures/raw/<name>.html  -> the untouched page (gitignored, never commit it)
- tests/fixtures/<name>.html      -> the anonymized copy that is safe to commit

Always open the anonymized file and check it by eye before committing.
"""

import argparse
import asyncio
import re
import sys
from pathlib import Path

from eeclass_mcp.client.auth import PlaywrightAuthProvider
from eeclass_mcp.client.http_client import HttpxEeClassClient
from eeclass_mcp.client.protocol import EeClassClientError
from eeclass_mcp.config import Settings
from eeclass_mcp.logging_config import setup_logging

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
RAW_DIR = FIXTURE_DIR / "raw"

# Replacement values follow tests/fixtures/README.md (#2) so every fixture looks alike.
STUDENT_ID_PLACEHOLDER = "100000000"
PHONE_PLACEHOLDER = "0900000000"
HASH_PLACEHOLDER = "0000000000000000"

# Per-session tokens, contact details and IDs that identify the user.
_TOKEN_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # ajaxAuth=xxx in URLs, "ajaxAuth":"xxx" / ajaxAuth: 'xxx' in inline JS
    (re.compile(r"(ajaxAuth[\"']?\s*[=:]\s*[\"']?)[^\"'&\s<>,;)]+"), r"\1REDACTED"),
    # ?auth=xxx / &auth=xxx download tokens
    (re.compile(r"([?&](?:amp;)?auth=)[^\"'&\s<>]+"), r"\1REDACTED"),
    # <input name="anticsrf" value="xxx"> in either attribute order, and JSON forms
    (re.compile(r"(name=[\"']anticsrf[\"'][^>]*?value=[\"'])[^\"']*"), r"\1REDACTED"),
    (re.compile(r"(value=[\"'])[^\"']*([\"'][^>]*?name=[\"']anticsrf[\"'])"), r"\1REDACTED\2"),
    (re.compile(r"([\"']?anticsrf[\"']?\s*[=:]\s*[\"'])[^\"']*"), r"\1REDACTED"),
    (re.compile(r"(PHPSESSID[\"']?\s*[=:]\s*[\"']?)[^\"'&\s<>;]+"), r"\1REDACTED"),
    (re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "redacted@example.com"),
    (re.compile(r"\b09\d{8}\b"), PHONE_PLACEHOLDER),
    # userId=123 / "poster":123 / ouid: '123' in URLs and inline JS
    (re.compile(r"((?:userId|poster|ouid)[\"']?\s*[=:]\s*[\"']?)\d+"), r"\g<1>0"),
    # Per-file hashes in /download/<hash> and /sysdata/.../<hash>
    (
        re.compile(r"(/(?:download|sysdata)/(?:[^\"'\s<>?]*/)?)[0-9a-f]{16,}"),
        rf"\1{HASH_PLACEHOLDER}",
    ),
    # Level and badge points on the dashboard sidebar ("等級 7", "7537 分")
    (re.compile(r"等級\s*\d+"), "等級 0"),
    (re.compile(r"\d+(\s*分\s*<span[^>]*fa-chevron-right)"), r"0\1"),
]

# Other students' names: "(王小明)" author tags in discussion / event lists
_AUTHOR_TAG = re.compile(
    r"(<div\s+class=[\"']icon pull-right[\"']\s*>\s*<span[^>]*fs-hint[^>]*>)\([^)<]*\)(</span>)"
)
# User-written discussion titles (may mention classmates by name)
_DISCUSSION_TITLE = re.compile(
    r"(<a\s+href=[\"']/course/courseDiscuss/\d+[\"'](?:(?!</a>).)*?"
    r"<span\s+class=[\"']\s*text\s*[\"']\s*>)[^<]*(</span>)",
    re.DOTALL,
)


def fixture_name(path: str) -> str:
    """'/dashboard/latestEvent' -> 'dashboard_latestEvent'."""
    name = re.sub(r"[^\w]+", "_", path.split("?", 1)[0].strip("/")).strip("_")
    return name or "index"


def anonymize(html: str, student_id: str, names: list[str]) -> str:
    """Replace tokens, contact details, the student ID, and every person's name.

    The user's own names (``--redact``) become 使用者01, 使用者02... and other people's
    author tags continue the numbering. Discussion titles become 測試討論 N.
    """
    for pattern, repl in _TOKEN_PATTERNS:
        html = pattern.sub(repl, html)
    if student_id:
        html = html.replace(student_id, STUDENT_ID_PLACEHOLDER)

    # Longest first so "王小明" is replaced before a substring like "小明".
    unique_names = sorted({n for n in names if n}, key=len, reverse=True)
    for i, name in enumerate(unique_names, start=1):
        html = html.replace(name, f"使用者{i:02d}")

    counter = iter(range(len(unique_names) + 1, 10_000))
    html = _AUTHOR_TAG.sub(lambda m: f"{m[1]}(使用者{next(counter):02d}){m[2]}", html)
    titles = iter(range(1, 10_000))
    return _DISCUSSION_TITLE.sub(lambda m: f"{m[1]}測試討論 {next(titles)}{m[2]}", html)


async def capture(paths: list[str], extra_literals: list[str], *, offline: bool) -> int:
    settings = Settings()
    setup_logging(settings.log_level)
    student_id = settings.username.strip()
    literals = [student_id, *extra_literals]
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    client = None if offline else HttpxEeClassClient(settings, PlaywrightAuthProvider(settings))
    leaks = 0
    try:
        for path in paths:
            name = fixture_name(path)
            raw_path = RAW_DIR / f"{name}.html"
            if client is None:
                html = raw_path.read_text(encoding="utf-8")
            else:
                html = await client.get_html(path)
                raw_path.write_text(html, encoding="utf-8")
            clean = anonymize(html, student_id, extra_literals)
            (FIXTURE_DIR / f"{name}.html").write_text(clean, encoding="utf-8")

            remaining = [s for s in literals if s and s in clean]
            status = f"LEAK: {len(remaining)} literal(s) still present" if remaining else "ok"
            leaks += len(remaining)
            print(f"{path} -> tests/fixtures/{name}.html ({len(clean)} chars) [{status}]")
    finally:
        if client is not None:
            await client.close()
    return 1 if leaks else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="+", help="ee-class paths, e.g. /dashboard")
    parser.add_argument(
        "--redact",
        action="append",
        default=[],
        metavar="TEXT",
        help="extra literal to scrub (your name, etc.); repeatable",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="re-anonymize the saved tests/fixtures/raw/ copies instead of logging in",
    )
    args = parser.parse_args()
    try:
        sys.exit(asyncio.run(capture(args.paths, args.redact, offline=args.offline)))
    except EeClassClientError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
