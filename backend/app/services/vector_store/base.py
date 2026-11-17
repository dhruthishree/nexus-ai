from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class VectorSearchResult(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    score: float
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = {}

class VectorStoreBase(ABC):
    """
    Abstract Vector Store interface to decouple vector search implementations.
    Allows local ChromaDB for development and seamless migration to 
    Google Cloud Vertex AI Vector Search / pgvector in production.
    """
    @abstractmethod
    def add_chunks(
        self,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """Add embedded chunks to the vector database."""
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """Perform semantic search using a query vector."""
        pass

    @abstractmethod
    def delete_document_chunks(self, document_id: str) -> None:
        """Remove all indexed chunks belonging to a document."""
        pass

