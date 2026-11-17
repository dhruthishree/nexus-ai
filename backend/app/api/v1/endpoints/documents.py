from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.document_service import DocumentService
from app.schemas.document import DocumentResponse, DocumentDetailResponse, DocumentIngestResult

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentIngestResult, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    service = DocumentService(db)
    doc, is_duplicate = await service.ingest_document(file)
    message = "Document already ingested (duplicate detected by SHA-256)." if is_duplicate else "Document successfully uploaded and chunked."
    return DocumentIngestResult(message=message, document=doc, is_duplicate=is_duplicate)

@router.get("", response_model=List[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    service = DocumentService(db)
    return service.list_documents()

@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    service = DocumentService(db)
    doc = service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc

@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(document_id: str, db: Session = Depends(get_db)):
    service = DocumentService(db)
    success = service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return {"message": "Document deleted successfully", "id": document_id}

