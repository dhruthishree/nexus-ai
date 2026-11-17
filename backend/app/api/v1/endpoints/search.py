from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.schemas.search import SearchQueryRequest, SearchQueryResponse
from app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/search", tags=["Semantic Search"])

@router.post("", response_model=SearchQueryResponse)
def search_documents(
    payload: SearchQueryRequest,
    db: Session = Depends(get_db)
):
    service = RetrievalService(db)
    return service.search(
        query=payload.query,
        top_k=payload.top_k,
        document_id=payload.document_id
    )

