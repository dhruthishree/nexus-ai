from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.workflow import WorkflowExecuteRequest, WorkflowExecutionResponse
from app.services.agents.workflow import MultiAgentWorkflowService

router = APIRouter(prefix="/workflow", tags=["Multi-Agent Workflow"])

@router.post("/execute", response_model=WorkflowExecutionResponse)
def execute_workflow(
    payload: WorkflowExecuteRequest,
    db: Session = Depends(get_db)
):
    try:
        service = MultiAgentWorkflowService(db)
        state = service.run_workflow(
            question=payload.question,
            document_id=payload.document_id,
            top_k=payload.top_k
        )

        return WorkflowExecutionResponse(
            question=state["question"],
            final_answer=state["final_answer"],
            citations=state.get("citations", []),
            has_sufficient_context=state.get("has_sufficient_context", False),
            is_verified=state.get("is_verified", False),
            verification_feedback=state.get("verification_feedback", ""),
            analyzed_facts=state.get("analyzed_facts", []),
            workflow_logs=state.get("workflow_logs", []),
            metrics={
                "total_input_tokens": state.get("total_input_tokens", 0),
                "total_output_tokens": state.get("total_output_tokens", 0),
                "total_cost_usd": state.get("total_cost_usd", 0.0),
                "total_latency_seconds": state.get("total_latency_seconds", 0.0),
                "retrieval_retry_count": state.get("retrieval_retry_count", 0)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multi-agent workflow execution failed: {str(e)}"
        )

