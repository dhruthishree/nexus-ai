import pytest
from app.services.chunker import RecursiveChunker

def test_chunker_basic_split():
    text = "Paragraph 1 is here.\n\nParagraph 2 contains more details about system architecture."
    chunker = RecursiveChunker(chunk_size=40, chunk_overlap=10)
    chunks = chunker.chunk_text(text, page_number=1)
    
    assert len(chunks) >= 2
    assert chunks[0].page_number == 1
    assert chunks[0].chunk_index == 0
    assert chunks[1].chunk_index == 1
    assert chunks[0].char_count > 0
    assert chunks[0].estimated_tokens > 0

def test_chunker_respects_max_size():
    long_sentence = "NEXUS AI architecture guarantees deterministic chunk extraction and reliable semantic search. " * 10
    chunker = RecursiveChunker(chunk_size=120, chunk_overlap=20)
    chunks = chunker.chunk_text(long_sentence)
    
    assert len(chunks) > 1
    for ch in chunks:
        assert len(ch.content) <= 150 # Allows minor margin for word splits

