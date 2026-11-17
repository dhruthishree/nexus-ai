from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SearchQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000, description="Semantic search query")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to retrieve")
    document_id: Optional[str] = Field(default=None, description="Optional document filter")

class SearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    document_filename: str
    content: str
    score: float
    page_number: Optional[int] = None
    estimated_tokens: int

class SearchQueryResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResultItem]

