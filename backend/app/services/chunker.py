from typing import List, Optional
import re

class TextChunk:
    def __init__(self, content: str, chunk_index: int, page_number: Optional[int] = None):
        self.content = content
        self.chunk_index = chunk_index
        self.page_number = page_number
        self.char_count = len(content)
        # Approximate 4 characters per token heuristic standard in LLM engineering
        self.estimated_tokens = max(1, len(content) // 4)

class RecursiveChunker:
    """
    Splits text recursively by paragraphs, sentences, and words to preserve semantic boundaries.
    """
    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
        separators: Optional[List[str]] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", "? ", "! ", " ", ""]

    def chunk_text(self, text: str, page_number: Optional[int] = None, start_index: int = 0) -> List[TextChunk]:
        raw_chunks = self._split_text(text, self.separators)
        results: List[TextChunk] = []
        for i, chunk_str in enumerate(raw_chunks):
            cleaned = chunk_str.strip()
            if cleaned:
                results.append(TextChunk(content=cleaned, chunk_index=start_index + len(results), page_number=page_number))
        return results

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        final_chunks: List[str] = []
        separator = separators[-1]
        new_separators: List[str] = []

        for i, sep in enumerate(separators):
            if sep == "":
                separator = ""
                break
            if sep in text:
                separator = sep
                new_separators = separators[i + 1:]
                break

        splits = text.split(separator) if separator else list(text)

        good_splits: List[str] = []
        for s in splits:
            if not s:
                continue
            if len(s) < self.chunk_size:
                good_splits.append(s)
            else:
                if new_separators:
                    sub_splits = self._split_text(s, new_separators)
                    good_splits.extend(sub_splits)
                else:
                    good_splits.append(s)

        # Merge splits respecting chunk_size and chunk_overlap
        current_chunk: List[str] = []
        current_len = 0

        for piece in good_splits:
            piece_len = len(piece) + (len(separator) if current_chunk else 0)
            if current_len + piece_len > self.chunk_size and current_chunk:
                merged = separator.join(current_chunk)
                final_chunks.append(merged)
                
                # Handle overlap by keeping tail elements
                while current_chunk and current_len > self.chunk_overlap:
                    removed = current_chunk.pop(0)
                    current_len -= (len(removed) + len(separator))
            
            current_chunk.append(piece)
            current_len += piece_len

        if current_chunk:
            final_chunks.append(separator.join(current_chunk))

        return final_chunks

