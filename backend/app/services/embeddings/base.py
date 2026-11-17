from abc import ABC, abstractmethod
from typing import List

class EmbeddingServiceBase(ABC):
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a batch of text chunks."""
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Generate a vector embedding for a single user search query."""
        pass

