from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Citation(BaseModel):
    citation_id: int
    document_id: str
    document_filename: str
    chunk_id: str
    page_number: Optional[int] = None
    similarity_score: float
    excerpt: str

class RAGQueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000, description="User question to answer using knowledge base")
    document_id: Optional[str] = Field(default=None, description="Optional filter to restrict RAG to a specific document")
    top_k: int = Field(default=5, ge=1, le=10, description="Number of evidence chunks to retrieve")

class RAGUsageMetrics(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_seconds: float
    estimated_cost_usd: float

class RAGQueryResponse(BaseModel):
    question: str
    answer: str
    citations: List[Citation]
    has_sufficient_context: bool
    metrics: RAGUsageMetrics
    generated_at: datetime

