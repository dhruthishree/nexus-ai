import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.core.config import settings
from app.core.logging import logger
from app.services.vector_store.base import VectorStoreBase, VectorSearchResult

class ChromaVectorStore(VectorStoreBase):
    """
    ChromaDB implementation of the VectorStore interface.
    Persists locally in data/chromadb with cosine similarity space.
    """
    def __init__(self, persist_directory: Optional[Path] = None, collection_name: str = "nexus_knowledge"):
        self.persist_dir = persist_directory or settings.CHROMA_PERSIST_DIR
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(
        self,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        if not chunk_ids:
            return
        try:
            self.collection.upsert(
                ids=chunk_ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"Upserted {len(chunk_ids)} chunks into ChromaDB collection '{self.collection.name}'.")
        except Exception as e:
            logger.error(f"Error adding vectors to ChromaDB: {e}", exc_info=True)
            raise

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        try:
            query_params: Dict[str, Any] = {
                "query_embeddings": [query_embedding],
                "n_results": top_k,
                "include": ["documents", "metadatas", "distances"]
            }
            if filter_metadata:
                query_params["where"] = filter_metadata

            results = self.collection.query(**query_params)
            search_results: List[VectorSearchResult] = []

            if not results or not results.get("ids") or not results["ids"][0]:
                return search_results

            ids = results["ids"][0]
            docs = results["documents"][0] if results.get("documents") else []
            metas = results["metadatas"][0] if results.get("metadatas") else []
            distances = results["distances"][0] if results.get("distances") else []

            for i, chunk_id in enumerate(ids):
                # Cosine distance: distance = 1 - cosine_similarity.
                # Similarity score = 1 - distance
                dist = distances[i] if i < len(distances) else 1.0
                similarity_score = max(0.0, min(1.0, 1.0 - dist))
                
                meta = metas[i] if i < len(metas) else {}
                doc_text = docs[i] if i < len(docs) else ""
                
                search_results.append(VectorSearchResult(
                    chunk_id=chunk_id,
                    document_id=meta.get("document_id", ""),
                    content=doc_text,
                    score=round(similarity_score, 4),
                    page_number=meta.get("page_number"),
                    metadata=meta
                ))

            return search_results
        except Exception as e:
            logger.error(f"Error performing ChromaDB vector search: {e}", exc_info=True)
            raise

    def delete_document_chunks(self, document_id: str) -> None:
        try:
            self.collection.delete(where={"document_id": document_id})
            logger.info(f"Deleted vector chunks for document_id '{document_id}'.")
        except Exception as e:
            logger.error(f"Failed to delete document chunks from ChromaDB: {e}", exc_info=True)
            raise

