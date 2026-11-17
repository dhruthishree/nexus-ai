import json
from typing import Dict, Any, List
from datetime import datetime, timezone

from app.core.logging import logger
from app.services.agents.state import AgentState
from app.services.llm.base import LLMServiceBase, calculate_rag_cost

ANALYSIS_SYSTEM_PROMPT = """You are the Analysis Agent in NEXUS AI.
Your role: Examine the user's question and the retrieved evidence chunks.
Tasks:
1. Extract atomic factual statements directly supported by the context.
2. Group related facts and identify key technical relationships.
3. Formulate synthesis notes connecting the facts to the user's question.

Return output strictly in valid JSON format:
{
  "facts": ["fact 1", "fact 2"],
  "synthesis_notes": "Synthesis summary connecting facts to question"
}
"""

def analysis_agent(state: AgentState, llm_service: LLMServiceBase) -> Dict[str, Any]:
    logger.info("Executing Analysis Agent...")
    chunks = state.get("retrieved_chunks", [])
    question = state["question"]

    logs = list(state.get("workflow_logs", []))

    if not chunks:
        log_entry = {
            "step_name": "analysis_evaluation",
            "agent_name": "AnalysisAgent",
            "status": "SKIPPED",
            "details": "No chunks available to analyze.",
            "timestamp_utc": datetime.now(timezone.utc).isoformat()
        }
        logs.append(log_entry)
        return {
            "analyzed_facts": [],
            "synthesis_notes": "No evidence chunks available.",
            "workflow_logs": logs
        }

    formatted_evidence = "\n\n".join([f"Chunk [{i+1}] ({c['document_filename']}): {c['content']}" for i, c in enumerate(chunks)])
    user_prompt = f"USER QUESTION: {question}\n\nEVIDENCE CHUNKS:\n{formatted_evidence}"

    raw_response, in_tokens, out_tokens = llm_service.generate_response(
        system_instruction=ANALYSIS_SYSTEM_PROMPT,
        user_prompt=user_prompt
    )

    cost = calculate_rag_cost(in_tokens, out_tokens)

    facts: List[str] = []
    notes = ""
    try:
        cleaned = raw_response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned.replace("```json", "", 1).rstrip("`").strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned.replace("```", "", 1).rstrip("`").strip()
            
        parsed = json.loads(cleaned)
        facts = parsed.get("facts", [])
        notes = parsed.get("synthesis_notes", "")
    except Exception as e:
        logger.warning(f"Failed to parse JSON from Analysis Agent response: {e}. Fallback to raw text.")
        facts = [line.strip("- ") for line in raw_response.split("\n") if line.strip().startswith("-")]
        notes = raw_response

    log_entry = {
        "step_name": "analysis_evaluation",
        "agent_name": "AnalysisAgent",
        "status": "COMPLETED",
        "details": f"Extracted {len(facts)} key facts from context. (In: {in_tokens}, Out: {out_tokens})",
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }
    logs.append(log_entry)

    return {
        "analyzed_facts": facts,
        "synthesis_notes": notes,
        "total_input_tokens": state.get("total_input_tokens", 0) + in_tokens,
        "total_output_tokens": state.get("total_output_tokens", 0) + out_tokens,
        "total_cost_usd": round(state.get("total_cost_usd", 0.0) + cost, 6),
        "workflow_logs": logs
    }

