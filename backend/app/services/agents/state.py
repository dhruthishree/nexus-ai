from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel

class WorkflowStepLog(BaseModel):
    step_name: str
    agent_name: str
    status: str
    details: str
    timestamp_utc: str

class AgentState(TypedDict):
    # User Inputs
    question: str
    document_id: Optional[str]
    top_k: int

    # Retrieval Agent Output
    retrieved_chunks: List[Dict[str, Any]]
    retrieval_retry_count: int

    # Analysis Agent Output
    analyzed_facts: List[str]
    synthesis_notes: str

    # Verification Agent Output
    is_verified: bool
    verification_feedback: str
    unsupported_claims: List[str]

    # Response Agent Output
    final_answer: str
    citations: List[Dict[str, Any]]
    has_sufficient_context: bool

    # Observability & Cost Tracking
    workflow_logs: List[Dict[str, Any]]
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    total_latency_seconds: float

