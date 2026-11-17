from langgraph.graph import StateGraph, END
from typing import Dict, Any, Optional
import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.services.agents.state import AgentState
from app.services.agents.retrieval_agent import retrieval_agent
from app.services.agents.analysis_agent import analysis_agent
from app.services.agents.verification_agent import verification_agent
from app.services.agents.response_agent import response_agent
from app.services.retrieval_service import RetrievalService
from app.services.llm.base import LLMServiceBase
from app.services.llm.gemini import GeminiLLMService

def should_retry_retrieval(state: AgentState) -> str:
    """
    Conditional Edge:
    Evaluates whether verification passed or if another retrieval pass is needed.
    Prevents infinite loops by capping retry count to 1.
    """
    is_verified = state.get("is_verified", True)
    retry_count = state.get("retrieval_retry_count", 0)
    has_chunks = bool(state.get("retrieved_chunks", []))

    if not is_verified and retry_count < 1 and has_chunks:
        logger.info("Verification indicated missing evidence. Routing back to RetrievalAgent for retry pass.")
        return "retry_retrieval"
    return "generate_response"

class MultiAgentWorkflowService:
    """
    Coordinates Retrieval, Analysis, Verification, and Response agents
    via a LangGraph directed state graph with conditional retry edges.
    """
    def __init__(
        self,
        db: Session,
        retrieval_service: Optional[RetrievalService] = None,
        llm_service: Optional[LLMServiceBase] = None
    ):
        self.db = db
        self.retrieval_service = retrieval_service or RetrievalService(db)
        self.llm_service = llm_service or GeminiLLMService()
        self.workflow = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(AgentState)

        # Wrap nodes with dependencies
        def run_retrieval(state: AgentState) -> Dict[str, Any]:
            return retrieval_agent(state, self.retrieval_service)

        def run_retry_retrieval(state: AgentState) -> Dict[str, Any]:
            retries = state.get("retrieval_retry_count", 0) + 1
            updated_state = dict(state)
            updated_state["retrieval_retry_count"] = retries
            out = retrieval_agent(updated_state, self.retrieval_service)
            out["retrieval_retry_count"] = retries
            return out

        def run_analysis(state: AgentState) -> Dict[str, Any]:
            return analysis_agent(state, self.llm_service)

        def run_verification(state: AgentState) -> Dict[str, Any]:
            return verification_agent(state, self.llm_service)

        def run_response(state: AgentState) -> Dict[str, Any]:
            return response_agent(state, self.llm_service)

        # Register Nodes
        graph.add_node("retrieval", run_retrieval)
        graph.add_node("analysis", run_analysis)
        graph.add_node("verification", run_verification)
        graph.add_node("retry_retrieval", run_retry_retrieval)
        graph.add_node("response", run_response)

        # Define Edges & Flow
        graph.set_entry_point("retrieval")
        graph.add_edge("retrieval", "analysis")
        graph.add_edge("analysis", "verification")

        # Conditional Edge after Verification
        graph.add_conditional_edges(
            "verification",
            should_retry_retrieval,
            {
                "retry_retrieval": "retry_retrieval",
                "generate_response": "response"
            }
        )

        # After retry retrieval, run analysis again
        graph.add_edge("retry_retrieval", "analysis")
        graph.add_edge("response", END)

        return graph.compile()

    def run_workflow(
        self,
        question: str,
        document_id: Optional[str] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()

        initial_state: AgentState = {
            "question": question,
            "document_id": document_id,
            "top_k": top_k,
            "retrieved_chunks": [],
            "retrieval_retry_count": 0,
            "analyzed_facts": [],
            "synthesis_notes": "",
            "is_verified": False,
            "verification_feedback": "",
            "unsupported_claims": [],
            "final_answer": "",
            "citations": [],
            "has_sufficient_context": False,
            "workflow_logs": [],
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost_usd": 0.0,
            "total_latency_seconds": 0.0
        }

        final_state = self.workflow.invoke(initial_state)
        latency = time.perf_counter() - start_time
        final_state["total_latency_seconds"] = round(latency, 3)

        return final_state

