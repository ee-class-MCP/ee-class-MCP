"""Pydantic data model for courses."""

from pydantic import BaseModel, Field


class Course(BaseModel):
    """Represents a course on NCU ee-class."""

    id: int = Field(..., ge=0, description="Course identifier on ee-class.")
    code: str = Field(..., min_length=1, description="Course code (e.g. CE2013*).")
    name: str = Field(..., min_length=1, description="Course title.")
    semester: str | None = Field(default=None, description="Academic semester (e.g. 114-1).")
    instructor: str | None = Field(default=None, description="Course instructor name.")
    url: str | None = Field(default=None, description="Course homepage URL.")
