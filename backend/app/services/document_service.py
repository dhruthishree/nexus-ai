import hashlib
import os
import shutil
import uuid
from pathlib import Path
from typing import Tuple, List, Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status

from app.core.config import settings
from app.core.logging import logger
from app.models.document import Document, DocumentChunk, IngestionStatus
from app.services.extractor import DocumentExtractorFactory
from app.services.chunker import RecursiveChunker
from app.services.vector_store.base import VectorStoreBase
from app.services.vector_store.chroma import ChromaVectorStore
from app.services.embeddings.base import EmbeddingServiceBase
from app.services.embeddings.gemini import GeminiEmbeddingService

class DocumentService:
    def __init__(
        self,
        db: Session,
        vector_store: Optional[VectorStoreBase] = None,
        embedding_service: Optional[EmbeddingServiceBase] = None
    ):
        self.db = db
        self.vector_store = vector_store or ChromaVectorStore()
        self.embedding_service = embedding_service or GeminiEmbeddingService()
        self.chunker = RecursiveChunker(
            chunk_size=settings.DEFAULT_CHUNK_SIZE,
            chunk_overlap=settings.DEFAULT_CHUNK_OVERLAP
        )

    def calculate_sha256(self, file_path: Path) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    async def save_uploaded_file(self, upload_file: UploadFile) -> Tuple[Path, str, int]:
        ext = Path(upload_file.filename).suffix.lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        unique_filename = f"{uuid.uuid4()}{ext}"
        target_path = settings.STORAGE_DIR / unique_filename

        total_bytes = 0
        sha256 = hashlib.sha256()

        try:
            with open(target_path, "wb") as buffer:
                while content := await upload_file.read(1024 * 64):
                    total_bytes += len(content)
                    if total_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES / (1024*1024):.1f} MB."
                        )
                    sha256.update(content)
                    buffer.write(content)
        except Exception:
            if target_path.exists():
                target_path.unlink()
            raise

        return target_path, sha256.hexdigest(), total_bytes

    async def ingest_document(self, upload_file: UploadFile) -> Tuple[Document, bool]:
        """
        Processes document upload: SHA-256 deduplication, extraction, chunking,
        generating vector embeddings and indexing into the vector store.
        """
        temp_path, sha256_hash, file_size = await self.save_uploaded_file(upload_file)
        
        # Check for existing document by hash
        existing = self.db.query(Document).filter(Document.sha256_hash == sha256_hash).first()
        if existing:
            if temp_path.exists():
                target = Path(temp_path)
                target.unlink()
            return existing, True

        ext = Path(upload_file.filename).suffix.lower()
        doc = Document(
            filename=upload_file.filename,
            stored_path=str(temp_path),
            file_type=ext,
            file_size_bytes=file_size,
            sha256_hash=sha256_hash,
            status=IngestionStatus.PROCESSING
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)

        try:
            extractor = DocumentExtractorFactory.get_extractor(ext)
            sections = extractor.extract(temp_path)

            all_chunks: List[DocumentChunk] = []
            chunk_texts: List[str] = []
            chunk_counter = 0

            for sec in sections:
                sub_chunks = self.chunker.chunk_text(
                    text=sec.text,
                    page_number=sec.page_number,
                    start_index=chunk_counter
                )
                for sc in sub_chunks:
                    chunk_entity = DocumentChunk(
                        document_id=doc.id,
                        chunk_index=sc.chunk_index,
                        content=sc.content,
                        char_count=sc.char_count,
                        estimated_tokens=sc.estimated_tokens,
                        page_number=sc.page_number
                    )
                    all_chunks.append(chunk_entity)
                    chunk_texts.append(sc.content)
                chunk_counter += len(sub_chunks)

            self.db.add_all(all_chunks)
            self.db.flush()

            # Vector indexing
            if all_chunks and settings.GEMINI_API_KEY:
                logger.info(f"Generating embeddings for {len(chunk_texts)} chunks...")
                embeddings = self.embedding_service.embed_texts(chunk_texts)
                
                chunk_ids = [c.id for c in all_chunks]
                metadatas = [
                    {
                        "document_id": doc.id,
                        "chunk_index": c.chunk_index,
                        "page_number": c.page_number or 1,
                        "filename": doc.filename
                    }
                    for c in all_chunks
                ]
                self.vector_store.add_chunks(
                    chunk_ids=chunk_ids,
                    embeddings=embeddings,
                    documents=chunk_texts,
                    metadatas=metadatas
                )

            doc.chunk_count = len(all_chunks)
            doc.status = IngestionStatus.COMPLETED
            self.db.commit()
            self.db.refresh(doc)
            logger.info(f"Successfully ingested & indexed {doc.filename}: {doc.chunk_count} chunks.")
            return doc, False

        except Exception as e:
            logger.error(f"Failed to ingest document {doc.filename}: {e}", exc_info=True)
            doc.status = IngestionStatus.FAILED
            doc.error_message = str(e)
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Document parsing/indexing failed: {str(e)}"
            )

    def list_documents(self) -> List[Document]:
        return self.db.query(Document).order_by(Document.created_at.desc()).all()

    def get_document(self, doc_id: str) -> Optional[Document]:
        return self.db.query(Document).filter(Document.id == doc_id).first()

    def delete_document(self, doc_id: str) -> bool:
        doc = self.get_document(doc_id)
        if not doc:
            return False

        # Clean from vector store
        try:
            self.vector_store.delete_document_chunks(doc_id)
        except Exception as e:
            logger.warning(f"Vector cleanup error for {doc_id}: {e}")

        # Remove physical file
        try:
            path = Path(doc.stored_path)
            if path.exists():
                path.unlink()
        except Exception as e:
            logger.warning(f"Failed to delete stored file {doc.stored_path}: {e}")

        self.db.delete(doc)
        self.db.commit()
        return True
