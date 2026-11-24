"""Pydantic data model for locally downloaded files."""

from pydantic import BaseModel, Field


class DownloadedFile(BaseModel):
    """Metadata returned after downloading an attachment locally."""

    filename: str = Field(..., description="Sanitized filename saved on disk.")
    saved_path: str = Field(..., description="Absolute local path to the downloaded file.")
    size_bytes: int = Field(..., ge=0, description="File size in bytes.")
    content_type: str | None = Field(default=None, description="HTTP Content-Type header.")
    source_url: str = Field(..., description="Original URL or path downloaded from.")
