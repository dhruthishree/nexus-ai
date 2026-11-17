import pytest
from app.services.embeddings.base import EmbeddingServiceBase
from app.services.retrieval_service import RetrievalService
from app.services.vector_store.chroma import ChromaVectorStore
from app.models.document import Document, IngestionStatus

class MockDeterministicEmbeddingService(EmbeddingServiceBase):
    """
    Deterministic mock embedding service for unit testing semantic search logic
    without requiring external API keys or incurring costs.
    """
    def embed_texts(self, texts):
        return [self._get_vector(t) for t in texts]

    def embed_query(self, query):
        return self._get_vector(query)

    def _get_vector(self, text):
        t = text.lower()
        if "agent" in t or "orchestration" in t:
            return [1.0, 0.0, 0.0]
        elif "cloud" in t or "gcp" in t:
            return [0.0, 1.0, 0.0]
        return [0.0, 0.0, 1.0]

def test_retrieval_service(db_session, tmp_path):
    # Setup test document in SQLite metadata
    doc = Document(
        id="doc-101",
        filename="MultiAgent_Design.pdf",
        stored_path="dummy.pdf",
        file_type=".pdf",
        file_size_bytes=1024,
        sha256_hash="hash101",
        status=IngestionStatus.COMPLETED
    )
    db_session.add(doc)
    db_session.commit()

    # Setup Chroma Vector Store with Mock Embeddings
    vector_store = ChromaVectorStore(persist_directory=tmp_path / "chroma_retrieval", collection_name="test_retrieval")
    mock_embeddings = MockDeterministicEmbeddingService()

    chunks = [
        "LangGraph manages multi-agent workflows with state machines.",
        "Google Cloud Run enables autoscaling container deployments."
    ]
    embs = mock_embeddings.embed_texts(chunks)
    metadatas = [
        {"document_id": "doc-101", "page_number": 3},
        {"document_id": "doc-101", "page_number": 7}
    ]
    vector_store.add_chunks(["c-1", "c-2"], embs, chunks, metadatas)

    # Execute Retrieval Service
    service = RetrievalService(db=db_session, vector_store=vector_store, embedding_service=mock_embeddings)
    res = service.search(query="How does multi-agent orchestration work?", top_k=1)

    assert res.total_results == 1
    assert res.results[0].chunk_id == "c-1"
    assert res.results[0].document_filename == "MultiAgent_Design.pdf"
    assert res.results[0].page_number == 3
    assert res.results[0].score > 0.9

