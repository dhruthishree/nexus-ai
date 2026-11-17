from typing import List
from google import genai
from google.genai import types
from app.core.config import settings
from app.core.logging import logger
from app.services.embeddings.base import EmbeddingServiceBase

class GeminiEmbeddingService(EmbeddingServiceBase):
    """
    Production-grade Google Gemini Embedding service using google-genai SDK.
    Supports task_type specialization (RETRIEVAL_DOCUMENT vs RETRIEVAL_QUERY).
    """
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.EMBEDDING_MODEL
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set. Gemini API calls will fail unless provided.")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if not self.client:
            raise ValueError("GEMINI_API_KEY is missing. Please configure it in your environment or backend/.env file.")

        embeddings: List[List[float]] = []
        batch_size = 50  # Respect API payload limits

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                response = self.client.models.embed_content(
                    model=self.model,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        task_type="RETRIEVAL_DOCUMENT",
                        output_dimensionality=settings.EMBEDDING_DIMENSION
                    )
                )
                for emb in response.embeddings:
                    embeddings.append(emb.values)
            except Exception as e:
                logger.error(f"Error generating Gemini embeddings: {e}", exc_info=True)
                raise

        return embeddings

    def embed_query(self, query: str) -> List[float]:
        if not self.client:
            raise ValueError("GEMINI_API_KEY is missing. Please configure it in your environment or backend/.env file.")
        try:
            response = self.client.models.embed_content(
                model=self.model,
                contents=query,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_QUERY",
                    output_dimensionality=settings.EMBEDDING_DIMENSION
                )
            )
            return response.embeddings[0].values
        except Exception as e:
            logger.error(f"Error generating Gemini query embedding: {e}", exc_info=True)
            raise

