from typing import Dict, Any, List
from datetime import datetime, timezone

from app.core.logging import logger
from app.services.agents.state import AgentState
from app.services.retrieval_service import RetrievalService

def retrieval_agent(state: AgentState, retrieval_service: RetrievalService) -> Dict[str, Any]:
    """
    Retrieval Agent:
    Searches the vector database for relevant semantic chunks.
    Adjusts query expansion or top_k dynamically if triggered on retry.
    """
    logger.info("Executing Retrieval Agent...")
    question = state["question"]
    doc_id = state.get("document_id")
    retry_count = state.get("retrieval_retry_count", 0)

    # If retrying because verification failed, retrieve more chunks
    effective_top_k = state.get("top_k", 5) + (retry_count * 2)

    search_result = retrieval_service.search(
        query=question,
        top_k=effective_top_k,
        document_id=doc_id
    )

    chunks_data = []
    for item in search_result.results:
        chunks_data.append({
            "chunk_id": item.chunk_id,
            "document_id": item.document_id,
            "document_filename": item.document_filename,
            "content": item.content,
            "score": item.score,
            "page_number": item.page_number
        })

    log_entry = {
        "step_name": f"retrieval_attempt_{retry_count + 1}",
        "agent_name": "RetrievalAgent",
        "status": "COMPLETED",
        "details": f"Retrieved {len(chunks_data)} candidate chunks with top_k={effective_top_k}.",
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }

    logs = list(state.get("workflow_logs", []))
    logs.append(log_entry)

    return {
        "retrieved_chunks": chunks_data,
        "workflow_logs": logs
    }

