from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/rag", tags=["RAG Assistant"])

@router.post("/query", response_model=RAGQueryResponse)
def query_knowledge_base(
    payload: RAGQueryRequest,
    db: Session = Depends(get_db)
):
    try:
        service = RAGService(db)
        return service.answer_question(payload)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG query generation failed: {str(e)}"
        )

