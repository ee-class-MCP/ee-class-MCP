from pydantic import BaseModel, Field
from src.eeclass_mcp.models.file import Attachment


class Submission(BaseModel):
    """
    A model representing a "submission". Things that can use embedded text editor like
    announcements, assignments, discussions and more should inherit this class.
    """

    title: str = Field(..., description="The title of the Submission.", exclude=True)
    content: str | None = Field(..., description="The content ofSubmission.")
    attachments: list[Attachment] = Field(
        default_factory=list,
        description="List of attached files."
    )
