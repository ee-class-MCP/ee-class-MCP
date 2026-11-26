"""Pydantic data models for course materials and attachments."""

from pydantic import BaseModel, Field
from file import Attachment

class MaterialItem(BaseModel, Attachment):
    """Represents a teaching material / lecture entry in a course."""

    id: str = Field(..., description="Material item identifier.")
    title: str = Field(..., description="Material title.")
    published_at: str | None = Field(default=None, description="Publish/update time string.")
    url: str | None = Field(default=None, description="Material detail page URL.")
    attachments: list[Attachment] = Field(
        default_factory=list,
        description="Downloadable attachments associated with this material.",
    )
