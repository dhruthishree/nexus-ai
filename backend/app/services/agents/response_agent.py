from typing import Dict, Any, List
from datetime import datetime, timezone

from app.core.logging import logger
from app.services.agents.state import AgentState
from app.services.llm.base import LLMServiceBase, calculate_rag_cost

RESPONSE_SYSTEM_PROMPT = """You are the Response Agent in NEXUS AI.
Your role: Synthesize the verified facts and notes into an elegant, accurate final answer.

Rules:
1. Grounding: Rely strictly on the verified facts and evidence provided.
2. Citations: Add bracketed citation references (e.g. [1], [2]) pointing to the source chunks.
3. If the context does not contain sufficient information, state:
   "The available enterprise documents do not contain sufficient information to answer this question."
4. Deliver high-clarity technical prose formatted with markdown where helpful.
"""

def response_agent(state: AgentState, llm_service: LLMServiceBase) -> Dict[str, Any]:
    logger.info("Executing Response Agent...")
    chunks = state.get("retrieved_chunks", [])
    facts = state.get("analyzed_facts", [])
    notes = state.get("synthesis_notes", "")
    question = state["question"]
    is_verified = state.get("is_verified", True)
    logs = list(state.get("workflow_logs", []))

    if not chunks or (not is_verified and state.get("retrieval_retry_count", 0) >= 1):
        log_entry = {
            "step_name": "final_synthesis",
            "agent_name": "ResponseAgent",
            "status": "COMPLETED",
            "details": "Returned insufficient context response.",
            "timestamp_utc": datetime.now(timezone.utc).isoformat()
        }
        logs.append(log_entry)
        return {
            "final_answer": "The available enterprise documents do not contain sufficient information to answer this question.",
            "citations": [],
            "has_sufficient_context": False,
            "workflow_logs": logs
        }

    # Construct citations
    citations = []
    chunk_blocks = []
    for idx, c in enumerate(chunks, start=1):
        citations.append({
            "citation_id": idx,
            "document_id": c["document_id"],
            "document_filename": c["document_filename"],
            "chunk_id": c["chunk_id"],
            "page_number": c.get("page_number"),
            "similarity_score": c.get("score", 1.0),
            "excerpt": c["content"][:200] + "..." if len(c["content"]) > 200 else c["content"]
        })
        chunk_blocks.append(f"[{idx}] Source: {c['document_filename']} (Page {c.get('page_number') or 1})\n{c['content']}")

    user_prompt = (
        f"QUESTION: {question}\n\n"
        f"VERIFIED FACTS:\n" + "\n".join([f"- {f}" for f in facts]) + "\n\n"
        f"SYNTHESIS NOTES:\n{notes}\n\n"
        f"SOURCE CONTEXT:\n" + "\n\n".join(chunk_blocks) + "\n\n"
        "FINAL SYNTHESIZED ANSWER:"
    )

    answer, in_tokens, out_tokens = llm_service.generate_response(
        system_instruction=RESPONSE_SYSTEM_PROMPT,
        user_prompt=user_prompt
    )

    cost = calculate_rag_cost(in_tokens, out_tokens)
    has_sufficient = "do not contain sufficient information" not in answer.lower()

    log_entry = {
        "step_name": "final_synthesis",
        "agent_name": "ResponseAgent",
        "status": "COMPLETED",
        "details": f"Generated final answer with {len(citations)} citations. (In: {in_tokens}, Out: {out_tokens})",
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }
    logs.append(log_entry)

    return {
        "final_answer": answer,
        "citations": citations,
        "has_sufficient_context": has_sufficient,
        "total_input_tokens": state.get("total_input_tokens", 0) + in_tokens,
        "total_output_tokens": state.get("total_output_tokens", 0) + out_tokens,
        "total_cost_usd": round(state.get("total_cost_usd", 0.0) + cost, 6),
        "workflow_logs": logs
    }

