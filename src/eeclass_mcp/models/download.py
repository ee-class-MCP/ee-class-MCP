"""Pydantic data model for locally downloaded files."""

from pydantic import BaseModel, Field

from file import Attachment


class DownloadedFile(BaseModel, Attachment):
    """Metadata returned after downloading an attachment locally."""

    saved_path: str = Field(..., description="Absolute local path to the downloaded file.")
    size_bytes: int = Field(..., ge=0, description="File size in bytes.")
    content_type: str | None = Field(default=None, description="HTTP Content-Type header.")