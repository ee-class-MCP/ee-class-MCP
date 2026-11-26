"""Pydantic data model for course assignments."""

from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl

from file import Attachment


class AssignmentStatus(StrEnum):
    """Enumeration of possible assignment submission statuses."""

    NOT_STARTED = "not_started"
    """The assignment is present, but has not yet started."""
    NOT_SUBMITTED = "not_submitted"
    """The assignment is available for submission, but has not been submitted."""
    DRAFTED = "drafted"
    """The assignment is a draft."""
    SUBMITTED = "submitted"
    """The assignment has been submitted."""
    MISSED = "missed"
    """The assignment was not submitted before the deadline."""
    GRADED = "graded"
    """The assignment has been graded."""


class Assignment(BaseModel, Attachment):
    """Represents an assignment or homework item in a course."""

    id: str = Field(..., description="Assignment identifier.")
    title: str = Field(..., description="Assignment title.")
    description: str | None = Field(default=None, description="Assignment description or instructions.") 
    download_files: list[Attachment] | None = Field(default=None, description="Local path to the downloaded assignment file.") 
    due_at: str | None = Field(default=None, description="Submission deadline string.")
    allow_late: bool = Field(default=False, description="Whether late submissions are allowed.")
    status: AssignmentStatus | None = Field(
        default=None,
        description="Submission status (e.g. submitted, not_submitted, graded).",
    )
    url: HttpUrl = Field(..., description="Direct URL to the assignment page.")
