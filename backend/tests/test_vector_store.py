import pytest
from app.services.vector_store.chroma import ChromaVectorStore

def test_chroma_vector_store_crud(tmp_path):
    store = ChromaVectorStore(persist_directory=tmp_path / "chroma_test", collection_name="test_collection")
    
    # 1. Add chunks with dummy normalized vectors
    chunk_ids = ["chunk-1", "chunk-2"]
    # 3-dim vectors: [1, 0, 0] and [0, 1, 0]
    embeddings = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    documents = ["Multi-agent systems improve reasoning.", "PostgreSQL handles relational data."]
    metadatas = [
        {"document_id": "doc-alpha", "page_number": 1},
        {"document_id": "doc-beta", "page_number": 2}
    ]

    store.add_chunks(chunk_ids, embeddings, documents, metadatas)

    # 2. Search exact match for first vector
    results = store.search(query_embedding=[1.0, 0.0, 0.0], top_k=1)
    assert len(results) == 1
    assert results[0].chunk_id == "chunk-1"
    assert results[0].document_id == "doc-alpha"
    assert results[0].score > 0.95  # Cosine similarity for identical vector is ~1.0

    # 3. Test filtering by metadata
    results_filtered = store.search(
        query_embedding=[1.0, 0.0, 0.0],
        top_k=2,
        filter_metadata={"document_id": "doc-beta"}
    )
    assert len(results_filtered) == 1
    assert results_filtered[0].chunk_id == "chunk-2"

    # 4. Delete document chunks
    store.delete_document_chunks("doc-alpha")
    results_after_delete = store.search(query_embedding=[1.0, 0.0, 0.0], top_k=2)
    assert len(results_after_delete) == 1
    assert results_after_delete[0].document_id == "doc-beta"

