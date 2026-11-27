"""Pydantic data model for course assignments."""

from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl

from eeclass_mcp.models.material import Attachment


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


class Assignment(BaseModel):
    """Represents an assignment or homework item in a course."""

    id: str = Field(..., description="Assignment identifier.")
    title: str = Field(..., description="Assignment title.")
    due_at: str | None = Field(default=None, description="Submission deadline string.")
    allow_late: bool = Field(default=False, description="Whether late submissions are allowed.")
    status: AssignmentStatus | None = Field(
        default=None,
        description="Submission status (e.g. submitted, not_submitted, graded).",
    )
    score: str | None = Field(default=None, description="Grade or score string if available.")
    url: HttpUrl = Field(..., description="Direct URL to the assignment page.")
    course_id: int | None = Field(default=None, description="Course identifier, if known.")
    course_name: str | None = Field(default=None, description="Course name, if known.")
    open_at: str | None = Field(
        default=None, description="Time submissions open, as shown on the page."
    )
    description: str | None = Field(
        default=None, description="Plain-text assignment description, lines joined by newline."
    )
    weight: str | None = Field(default=None, description="Grade weight string, e.g. '5%'.")
    attachments: list[Attachment] = Field(
        default_factory=list, description="Files attached to the assignment description."
    )
