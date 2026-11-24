"""Pydantic data model for course announcements."""

from pydantic import BaseModel, Field


class Announcement(BaseModel):
    """Represents an announcement inside a course."""

    id: str = Field(..., description="Announcement identifier.")
    title: str = Field(..., description="Announcement title.")
    author: str | None = Field(default=None, description="Author or publisher name.")
    published_at: str | None = Field(default=None, description="Publish date/time string.")
    content: str | None = Field(default=None, description="Announcement body text or summary.")
    url: str | None = Field(default=None, description="Direct URL to the announcement.")
