"""Pydantic data models for course materials and attachments."""

from pydantic import BaseModel, Field


class Attachment(BaseModel):
    """Represents a downloadable file attachment."""

    id: str | None = Field(default=None, description="Attachment identifier if available.")
    filename: str = Field(..., description="Display name or filename of the attachment.")
    download_url: str = Field(..., description="URL or relative path to download the file.")
    file_size: str | None = Field(default=None, description="Human-readable file size if shown.")


class MaterialItem(BaseModel):
    """Represents a teaching material / lecture entry in a course."""

    id: str = Field(..., description="Material item identifier.")
    title: str = Field(..., description="Material title.")
    category: str | None = Field(default=None, description="Week, chapter, or unit label.")
    published_at: str | None = Field(default=None, description="Publish/update time string.")
    url: str | None = Field(default=None, description="Material detail page URL.")
    attachments: list[Attachment] = Field(
        default_factory=list,
        description="Downloadable attachments associated with this material.",
    )
