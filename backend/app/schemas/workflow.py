from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.schemas.rag import Citation

class WorkflowExecuteRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000, description="Enterprise question for multi-agent investigation")
    document_id: Optional[str] = Field(default=None, description="Optional document filter")
    top_k: int = Field(default=5, ge=1, le=10, description="Base retrieval chunk budget")

class AgentLogItem(BaseModel):
    step_name: str
    agent_name: str
    status: str
    details: str
    timestamp_utc: str

class WorkflowExecutionResponse(BaseModel):
    question: str
    final_answer: str
    citations: List[Citation]
    has_sufficient_context: bool
    is_verified: bool
    verification_feedback: str
    analyzed_facts: List[str]
    workflow_logs: List[AgentLogItem]
    metrics: Dict[str, Any]

