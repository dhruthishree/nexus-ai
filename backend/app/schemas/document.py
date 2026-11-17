from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.models.document import IngestionStatus

class DocumentChunkResponse(BaseModel):
    id: str
    chunk_index: int
    content: str
    char_count: int
    estimated_tokens: int
    page_number: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size_bytes: int
    sha256_hash: str
    status: IngestionStatus
    error_message: Optional[str] = None
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentDetailResponse(DocumentResponse):
    chunks: List[DocumentChunkResponse] = []

class DocumentIngestResult(BaseModel):
    message: str
    document: DocumentResponse
    is_duplicate: bool = False

