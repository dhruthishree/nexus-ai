import time
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse, RAGUsageMetrics, Citation
from app.services.retrieval_service import RetrievalService
from app.services.llm.base import LLMServiceBase, calculate_rag_cost
from app.services.llm.gemini import GeminiLLMService

RAG_SYSTEM_PROMPT = """You are NEXUS AI, an enterprise-grade technical intelligence assistant.
Your goal is to answer the user's question with uncompromising accuracy, grounded ONLY in the provided document context.

Strict Guidelines:
1. Grounding: Answer strictly using facts stated in the provided context. Do NOT extrapolate or assume unstated facts.
2. In-text Citations: Whenever you state a claim derived from a context chunk, cite it directly using brackets, e.g., [1], [2], or [1, 3].
3. Insufficient Context: If the provided context does NOT contain enough information to answer the question faithfully, state clearly and concisely:
   "The available enterprise documents do not contain sufficient information to answer this question."
4. Tone: Technical, objective, concise, and professional.
"""

class RAGService:
    def __init__(
        self,
        db: Session,
        retrieval_service: Optional[RetrievalService] = None,
        llm_service: Optional[LLMServiceBase] = None
    ):
        self.db = db
        self.retrieval_service = retrieval_service or RetrievalService(db)
        self.llm_service = llm_service or GeminiLLMService()

    def answer_question(self, request: RAGQueryRequest) -> RAGQueryResponse:
        start_time = time.perf_counter()

        # Step 1: Semantic Retrieval
        search_response = self.retrieval_service.search(
            query=request.question,
            top_k=request.top_k,
            document_id=request.document_id
        )

        # Filter chunks by similarity threshold
        relevant_chunks = [
            c for c in search_response.results 
            if c.score >= settings.SIMILARITY_THRESHOLD
        ]

        # Early exit if no relevant context exists
        if not relevant_chunks:
            latency = time.perf_counter() - start_time
            return RAGQueryResponse(
                question=request.question,
                answer="The available enterprise documents do not contain sufficient information to answer this question.",
                citations=[],
                has_sufficient_context=False,
                metrics=RAGUsageMetrics(
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0,
                    latency_seconds=round(latency, 3),
                    estimated_cost_usd=0.0
                ),
                generated_at=datetime.now(timezone.utc)
            )

        # Step 2: Build Context & Citation Map
        citations: List[Citation] = []
        context_blocks: List[str] = []

        for idx, item in enumerate(relevant_chunks, start=1):
            citations.append(Citation(
                citation_id=idx,
                document_id=item.document_id,
                document_filename=item.document_filename,
                chunk_id=item.chunk_id,
                page_number=item.page_number,
                similarity_score=item.score,
                excerpt=item.content[:200] + "..." if len(item.content) > 200 else item.content
            ))
            context_blocks.append(f"[{idx}] Source: {item.document_filename} (Page {item.page_number or 1})\n{item.content}")

        formatted_context = "\n\n".join(context_blocks)
        user_prompt = f"DOCUMENT CONTEXT:\n{formatted_context}\n\nUSER QUESTION:\n{request.question}\n\nGROUNDED ANSWER:"

        # Step 3: LLM Generation
        answer, input_tokens, output_tokens = self.llm_service.generate_response(
            system_instruction=RAG_SYSTEM_PROMPT,
            user_prompt=user_prompt
        )

        latency = time.perf_counter() - start_time
        cost_usd = calculate_rag_cost(input_tokens, output_tokens)

        # Check if model reported lack of context
        has_sufficient = "do not contain sufficient information" not in answer.lower()

        return RAGQueryResponse(
            question=request.question,
            answer=answer,
            citations=citations,
            has_sufficient_context=has_sufficient,
            metrics=RAGUsageMetrics(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                latency_seconds=round(latency, 3),
                estimated_cost_usd=cost_usd
            ),
            generated_at=datetime.now(timezone.utc)
        )

