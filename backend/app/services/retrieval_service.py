from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.models.document import Document
from app.schemas.search import SearchResultItem, SearchQueryResponse
from app.services.vector_store.base import VectorStoreBase
from app.services.vector_store.chroma import ChromaVectorStore
from app.services.embeddings.base import EmbeddingServiceBase
from app.services.embeddings.gemini import GeminiEmbeddingService

class RetrievalService:
    """
    Orchestrates semantic search:
    1. Embeds user natural language query using the embedding service.
    2. Queries the vector database (cosine distance).
    3. Ground truth mapping back to SQL relational metadata (document title, page number).
    """
    def __init__(
        self,
        db: Session,
        vector_store: Optional[VectorStoreBase] = None,
        embedding_service: Optional[EmbeddingServiceBase] = None
    ):
        self.db = db
        self.vector_store = vector_store or ChromaVectorStore()
        self.embedding_service = embedding_service or GeminiEmbeddingService()

    def search(
        self,
        query: str,
        top_k: int = 5,
        document_id: Optional[str] = None
    ) -> SearchQueryResponse:
        logger.info(f"Executing semantic retrieval for query: '{query}' with top_k={top_k}")
        query_vector = self.embedding_service.embed_query(query)

        filter_metadata = {"document_id": document_id} if document_id else None
        raw_results = self.vector_store.search(
            query_embedding=query_vector,
            top_k=top_k,
            filter_metadata=filter_metadata
        )

        results: List[SearchResultItem] = []
        # Pre-fetch document names for citation display
        doc_cache = {}

        for item in raw_results:
            if item.document_id not in doc_cache:
                doc = self.db.query(Document).filter(Document.id == item.document_id).first()
                doc_cache[item.document_id] = doc.filename if doc else "Unknown Document"

            results.append(SearchResultItem(
                chunk_id=item.chunk_id,
                document_id=item.document_id,
                document_filename=doc_cache[item.document_id],
                content=item.content,
                score=item.score,
                page_number=item.page_number,
                estimated_tokens=max(1, len(item.content) // 4)
            ))

        return SearchQueryResponse(
            query=query,
            total_results=len(results),
            results=results
        )

