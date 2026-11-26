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

# Per-session tokens and secrets that change on every login or identify the user.
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
    # e-mail addresses
    (re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "redacted@example.com"),
    # Other students' names: "(王小明)" author tags in discussion / event lists
    (
        re.compile(
            r"(<div\s+class=[\"']icon pull-right[\"']\s*>\s*<span[^>]*fs-hint[^>]*>)"
            r"\([^)<]*\)(</span>)"
        ),
        r"\1(REDACTED_AUTHOR)\2",
    ),
    # User-written discussion titles (may mention classmates by name)
    (
        re.compile(
            r"(<a\s+href=[\"']/course/courseDiscuss/\d+[\"'](?:(?!</a>).)*?"
            r"<span\s+class=[\"']\s*text\s*[\"']\s*>)[^<]*(</span>)",
            re.DOTALL,
        ),
        r"\1REDACTED_DISCUSSION\2",
    ),
]


def fixture_name(path: str) -> str:
    """'/dashboard/latestEvent' -> 'dashboard_latestEvent'."""
    name = re.sub(r"[^\w]+", "_", path.split("?", 1)[0].strip("/")).strip("_")
    return name or "index"


def anonymize(html: str, literals: list[str]) -> str:
    """Replace session tokens, e-mails and the given literal strings (ID, name...)."""
    for pattern, repl in _TOKEN_PATTERNS:
        html = pattern.sub(repl, html)
    # Longest first so "王小明" is replaced before a substring like "小明".
    for i, literal in enumerate(sorted({s for s in literals if s}, key=len, reverse=True)):
        html = html.replace(literal, f"REDACTED_{i}")
    return html


async def capture(paths: list[str], extra_literals: list[str], *, offline: bool) -> int:
    settings = Settings()
    setup_logging(settings.log_level)
    literals = [settings.username.strip(), *extra_literals]
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
            clean = anonymize(html, literals)
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
