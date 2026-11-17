import io
from fastapi import status

def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"

def test_document_upload_and_deduplication(client):
    file_content = b"Enterprise Knowledge System specification document for testing deduplication."
    file_tuple = ("spec.txt", io.BytesIO(file_content), "text/plain")

    # 1. First upload
    response = client.post("/api/v1/documents/upload", files={"file": file_tuple})
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["is_duplicate"] is False
    assert data["document"]["filename"] == "spec.txt"
    assert data["document"]["chunk_count"] > 0
    doc_id = data["document"]["id"]

    # 2. Duplicate upload of same content
    file_tuple_2 = ("spec_renamed.txt", io.BytesIO(file_content), "text/plain")
    response_dup = client.post("/api/v1/documents/upload", files={"file": file_tuple_2})
    assert response_dup.status_code == status.HTTP_201_CREATED
    data_dup = response_dup.json()
    assert data_dup["is_duplicate"] is True
    assert data_dup["document"]["id"] == doc_id

    # 3. Retrieve document by ID
    response_get = client.get(f"/api/v1/documents/{doc_id}")
    assert response_get.status_code == status.HTTP_200_OK
    detail = response_get.json()
    assert len(detail["chunks"]) > 0

    # 4. List documents
    response_list = client.get("/api/v1/documents")
    assert response_list.status_code == status.HTTP_200_OK
    assert len(response_list.json()) == 1

    # 5. Delete document
    response_del = client.delete(f"/api/v1/documents/{doc_id}")
    assert response_del.status_code == status.HTTP_200_OK

    # 6. Verify deletion
    response_verify = client.get(f"/api/v1/documents/{doc_id}")
    assert response_verify.status_code == status.HTTP_404_NOT_FOUND

