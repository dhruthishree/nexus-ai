from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pathlib import Path

class Settings(BaseSettings):
    # App Information
    PROJECT_NAME: str = "NEXUS AI - Enterprise Knowledge & Workflow Intelligence"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # Security & CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    MAX_UPLOAD_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB limit
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt", ".csv"]

    # Storage & DB
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    STORAGE_DIR: Path = BASE_DIR / "data" / "uploads"
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'nexus.db'}"
    CHROMA_PERSIST_DIR: Path = BASE_DIR / "data" / "chromadb"

    # AI & Embeddings
    GEMINI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-004"
    EMBEDDING_DIMENSION: int = 768
    SIMILARITY_TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.35

    # Generation & RAG
    GENERATION_MODEL: str = "gemini-2.5-flash"
    TEMPERATURE: float = 0.2
    MAX_OUTPUT_TOKENS: int = 2048

    # Pricing (USD per 1M tokens) - gemini-2.5-flash tier
    # Used for deterministic, real-time cost tracking
    COST_PER_1M_INPUT_TOKENS: float = 0.075
    COST_PER_1M_OUTPUT_TOKENS: float = 0.30

    # Chunking Configuration
    DEFAULT_CHUNK_SIZE: int = 800  # Character count guideline
    DEFAULT_CHUNK_OVERLAP: int = 150

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
