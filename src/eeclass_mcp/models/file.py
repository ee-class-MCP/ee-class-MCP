from pydantic import BaseModel, Field

class Attachment(BaseModel):
    """Represents a downloadable file attachment."""

    id: str | None = Field(default=None, description="Attachment identifier if available.")
    filename: str = Field(..., description="Display name or filename of the attachment.")
    url: str = Field(..., description="URL or relative path to download the file.")
    saved_path: str = Field(..., description="Absolute local path to the downloaded file.")
    file_size: str | None = Field(default=None, description="Human-readable file size if shown.")