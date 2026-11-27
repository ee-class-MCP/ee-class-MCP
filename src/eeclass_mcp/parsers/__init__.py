"""Pure HTML/JSON parsers with no network dependencies."""

from .announcement import parse_announcements
from .assignment import parse_assignment_detail, parse_assignments, parse_latest_events
from .course import parse_courses
from .material import parse_materials

__all__ = [
    "parse_announcements",
    "parse_assignment_detail",
    "parse_assignments",
    "parse_courses",
    "parse_latest_events",
    "parse_materials",
]
