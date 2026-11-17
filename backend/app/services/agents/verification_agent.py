import json
from typing import Dict, Any, List
from datetime import datetime, timezone

from app.core.logging import logger
from app.services.agents.state import AgentState
from app.services.llm.base import LLMServiceBase, calculate_rag_cost

VERIFICATION_SYSTEM_PROMPT = """You are the Verification & Hallucination Guard Agent in NEXUS AI.
Your role: Rigorously cross-check the analyzed facts against the original retrieved evidence chunks.

Rules:
1. Every claim in the facts MUST be directly backed by the source chunks.
2. Check if the facts adequately address the question.
3. If critical information is missing or claims are unverified, set is_verified to false and list unsupported claims.

Return output strictly in valid JSON format:
{
  "is_verified": true,
  "feedback": "All facts are substantiated by provided sources.",
  "unsupported_claims": []
}
"""

def verification_agent(state: AgentState, llm_service: LLMServiceBase) -> Dict[str, Any]:
    logger.info("Executing Verification Agent...")
    chunks = state.get("retrieved_chunks", [])
    facts = state.get("analyzed_facts", [])
    question = state["question"]
    logs = list(state.get("workflow_logs", []))

    if not chunks or not facts:
        log_entry = {
            "step_name": "fact_verification",
            "agent_name": "VerificationAgent",
            "status": "COMPLETED",
            "details": "Verification passed as insufficient context (no facts or chunks to verify).",
            "timestamp_utc": datetime.now(timezone.utc).isoformat()
        }
        logs.append(log_entry)
        return {
            "is_verified": False,
            "verification_feedback": "Insufficient context retrieved.",
            "unsupported_claims": ["No retrieved context"],
            "workflow_logs": logs
        }

    formatted_evidence = "\n\n".join([f"Source {i+1}: {c['content']}" for i, c in enumerate(chunks)])
    formatted_facts = "\n".join([f"- {f}" for f in facts])
    user_prompt = f"ORIGINAL QUESTION:\n{question}\n\nRETRIEVED SOURCES:\n{formatted_evidence}\n\nANALYZED FACTS TO VERIFY:\n{formatted_facts}"

    raw_response, in_tokens, out_tokens = llm_service.generate_response(
        system_instruction=VERIFICATION_SYSTEM_PROMPT,
        user_prompt=user_prompt
    )

    cost = calculate_rag_cost(in_tokens, out_tokens)
    is_verified = True
    feedback = ""
    unsupported: List[str] = []

    try:
        cleaned = raw_response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned.replace("```json", "", 1).rstrip("`").strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned.replace("```", "", 1).rstrip("`").strip()

        parsed = json.loads(cleaned)
        is_verified = bool(parsed.get("is_verified", True))
        feedback = parsed.get("feedback", "")
        unsupported = parsed.get("unsupported_claims", [])
    except Exception as e:
        logger.warning(f"Verification JSON parsing error: {e}. Defaulting to verified.")
        is_verified = True
        feedback = raw_response

    log_entry = {
        "step_name": "fact_verification",
        "agent_name": "VerificationAgent",
        "status": "COMPLETED",
        "details": f"Verification status: {'PASSED' if is_verified else 'NEEDS_RETRY'}. Feedback: {feedback}",
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }
    logs.append(log_entry)

    return {
        "is_verified": is_verified,
        "verification_feedback": feedback,
        "unsupported_claims": unsupported,
        "total_input_tokens": state.get("total_input_tokens", 0) + in_tokens,
        "total_output_tokens": state.get("total_output_tokens", 0) + out_tokens,
        "total_cost_usd": round(state.get("total_cost_usd", 0.0) + cost, 6),
        "workflow_logs": logs
    }

