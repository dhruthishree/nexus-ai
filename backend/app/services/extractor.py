from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any
import pypdf
import docx
import pandas as pd
from app.core.logging import logger

class ExtractedSection:
    def __init__(self, text: str, page_number: int | None = None, metadata: Dict[str, Any] | None = None):
        self.text = text
        self.page_number = page_number
        self.metadata = metadata or {}

class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: Path) -> List[ExtractedSection]:
        """Extract text content and page/section metadata from file."""
        pass

class PDFExtractor(BaseExtractor):
    def extract(self, file_path: Path) -> List[ExtractedSection]:
        sections: List[ExtractedSection] = []
        try:
            reader = pypdf.PdfReader(str(file_path))
            for idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                text = text.strip()
                if text:
                    sections.append(ExtractedSection(text=text, page_number=idx + 1))
        except Exception as e:
            logger.error(f"Failed to extract PDF {file_path}: {e}")
            raise ValueError(f"Error parsing PDF file: {str(e)}")
        return sections

class DocxExtractor(BaseExtractor):
    def extract(self, file_path: Path) -> List[ExtractedSection]:
        sections: List[ExtractedSection] = []
        try:
            doc = docx.Document(str(file_path))
            full_text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text.strip())
            
            # Also extract tables cleanly
            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_text:
                        full_text.append(" | ".join(row_text))

            combined = "\n\n".join(full_text)
            if combined:
                sections.append(ExtractedSection(text=combined, page_number=1))
        except Exception as e:
            logger.error(f"Failed to extract DOCX {file_path}: {e}")
            raise ValueError(f"Error parsing DOCX file: {str(e)}")
        return sections

class TextExtractor(BaseExtractor):
    def extract(self, file_path: Path) -> List[ExtractedSection]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read().strip()
                if content:
                    return [ExtractedSection(text=content, page_number=1)]
                return []
        except Exception as e:
            logger.error(f"Failed to read TXT {file_path}: {e}")
            raise ValueError(f"Error reading TXT file: {str(e)}")

class CSVExtractor(BaseExtractor):
    def extract(self, file_path: Path) -> List[ExtractedSection]:
        try:
            df = pd.read_csv(file_path)
            # Format as clean tabular markdown representation
            markdown_table = df.to_markdown(index=False)
            if markdown_table:
                return [ExtractedSection(text=markdown_table, page_number=1, metadata={"rows": len(df), "cols": len(df.columns)})]
            return []
        except Exception as e:
            logger.error(f"Failed to read CSV {file_path}: {e}")
            raise ValueError(f"Error reading CSV file: {str(e)}")

class DocumentExtractorFactory:
    _extractors = {
        ".pdf": PDFExtractor(),
        ".docx": DocxExtractor(),
        ".txt": TextExtractor(),
        ".csv": CSVExtractor(),
    }

    @classmethod
    def get_extractor(cls, extension: str) -> BaseExtractor:
        ext = extension.lower()
        if ext not in cls._extractors:
            raise ValueError(f"Unsupported file format: {ext}")
        return cls._extractors[ext]

