from fastapi import APIRouter
from app.api.v1.endpoints import documents, health, search, rag, workflow

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(documents.router)
api_router.include_router(search.router)
api_router.include_router(rag.router)
api_router.include_router(workflow.router)


