import pytest
from app.services.llm.base import LLMServiceBase
from app.services.rag_service import RAGService
from app.schemas.rag import RAGQueryRequest
from app.schemas.search import SearchQueryResponse, SearchResultItem

class MockLLMService(LLMServiceBase):
    def generate_response(self, system_instruction: str, user_prompt: str):
        if "Kubernetes" in user_prompt:
            return "Kubernetes orchestrates containerized workloads [1].", 120, 25
        return "The available enterprise documents do not contain sufficient information to answer this question.", 80, 18

class MockRetrievalService:
    def __init__(self, should_find_chunks: bool = True):
        self.should_find_chunks = should_find_chunks

    def search(self, query: str, top_k: int = 5, document_id = None):
        if not self.should_find_chunks:
            return SearchQueryResponse(query=query, total_results=0, results=[])

        return SearchQueryResponse(
            query=query,
            total_results=1,
            results=[
                SearchResultItem(
                    chunk_id="chunk-k8s",
                    document_id="doc-k8s",
                    document_filename="Cloud_Architecture.pdf",
                    content="Kubernetes is an open-source platform that orchestrates containerized workloads across node pools.",
                    score=0.88,
                    page_number=5,
                    estimated_tokens=20
                )
            ]
        )

def test_rag_service_success(db_session):
    mock_llm = MockLLMService()
    mock_retrieval = MockRetrievalService(should_find_chunks=True)
    rag_service = RAGService(db=db_session, retrieval_service=mock_retrieval, llm_service=mock_llm)

    request = RAGQueryRequest(question="What is Kubernetes?", top_k=3)
    response = rag_service.answer_question(request)

    assert response.has_sufficient_context is True
    assert "[1]" in response.answer
    assert len(response.citations) == 1
    assert response.citations[0].document_filename == "Cloud_Architecture.pdf"
    assert response.citations[0].page_number == 5
    assert response.metrics.input_tokens == 120
    assert response.metrics.output_tokens == 25
    assert response.metrics.total_tokens == 145
    assert response.metrics.estimated_cost_usd > 0.0

def test_rag_service_insufficient_context(db_session):
    mock_llm = MockLLMService()
    mock_retrieval = MockRetrievalService(should_find_chunks=False)
    rag_service = RAGService(db=db_session, retrieval_service=mock_retrieval, llm_service=mock_llm)

    request = RAGQueryRequest(question="What is quantum gravity?", top_k=3)
    response = rag_service.answer_question(request)

    assert response.has_sufficient_context is False
    assert "do not contain sufficient information" in response.answer
    assert len(response.citations) == 0
    assert response.metrics.estimated_cost_usd == 0.0

