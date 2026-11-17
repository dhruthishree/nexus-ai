import pytest
import json
from app.services.llm.base import LLMServiceBase
from app.services.agents.workflow import MultiAgentWorkflowService
from app.schemas.search import SearchQueryResponse, SearchResultItem

class MockAgentLLMService(LLMServiceBase):
    def generate_response(self, system_instruction: str, user_prompt: str):
        if "Analysis Agent" in system_instruction:
            out = {
                "facts": ["FastAPI provides high performance async REST endpoints.", "Pydantic validates payload schemas."],
                "synthesis_notes": "Both frameworks build reliable enterprise microservices."
            }
            return json.dumps(out), 150, 40
        elif "Verification & Hallucination Guard" in system_instruction:
            out = {
                "is_verified": True,
                "feedback": "All assertions are verified against documentation.",
                "unsupported_claims": []
            }
            return json.dumps(out), 180, 25
        elif "Response Agent" in system_instruction:
            return "FastAPI delivers high-performance async REST endpoints validated by Pydantic [1].", 200, 30
        return "Generic response", 10, 10

class MockAgentRetrievalService:
    def search(self, query: str, top_k: int = 5, document_id = None):
        return SearchQueryResponse(
            query=query,
            total_results=1,
            results=[
                SearchResultItem(
                    chunk_id="chk-arch",
                    document_id="doc-arch",
                    document_filename="FastAPI_Architecture.pdf",
                    content="FastAPI is an async web framework for building APIs with Python, based on standard Python type hints.",
                    score=0.92,
                    page_number=1,
                    estimated_tokens=25
                )
            ]
        )

def test_multi_agent_workflow_success(db_session):
    mock_llm = MockAgentLLMService()
    mock_retrieval = MockAgentRetrievalService()

    workflow_service = MultiAgentWorkflowService(
        db=db_session,
        retrieval_service=mock_retrieval,
        llm_service=mock_llm
    )

    state = workflow_service.run_workflow(
        question="What are the technical capabilities of FastAPI?",
        top_k=3
    )

    # 1. State verification
    assert state["question"] == "What are the technical capabilities of FastAPI?"
    assert state["is_verified"] is True
    assert len(state["analyzed_facts"]) == 2
    assert "FastAPI" in state["final_answer"]
    assert "[1]" in state["final_answer"]

    # 2. Workflow logs auditability
    logs = state["workflow_logs"]
    agent_names = [log["agent_name"] for log in logs]
    assert "RetrievalAgent" in agent_names
    assert "AnalysisAgent" in agent_names
    assert "VerificationAgent" in agent_names
    assert "ResponseAgent" in agent_names

    # 3. Aggregated token & cost telemetry across all agents
    assert state["total_input_tokens"] > 0
    assert state["total_output_tokens"] > 0
    assert state["total_cost_usd"] > 0.0
    assert state["total_latency_seconds"] >= 0.0

