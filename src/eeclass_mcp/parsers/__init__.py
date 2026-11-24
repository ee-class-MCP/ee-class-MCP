"""Pure HTML/JSON parsers with no network dependencies."""

from .announcement import parse_announcements
from .assignment import parse_assignments
from .course import parse_courses
from .material import parse_materials

__all__ = [
    "parse_announcements",
    "parse_assignments",
    "parse_courses",
    "parse_materials",
]
