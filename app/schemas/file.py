from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

class FileCreate(BaseModel):
    filename: str
    content_type: str
    size_bytes: int
    data: bytes
    note_id: int
