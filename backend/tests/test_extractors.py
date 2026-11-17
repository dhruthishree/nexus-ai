import pytest
from pathlib import Path
from app.services.extractor import TextExtractor, CSVExtractor

def test_text_extractor(tmp_path: Path):
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text("Hello enterprise multi-agent system!\nThis is a clean line.", encoding="utf-8")
    
    extractor = TextExtractor()
    sections = extractor.extract(txt_file)
    assert len(sections) == 1
    assert "enterprise multi-agent" in sections[0].text
    assert sections[0].page_number == 1

def test_csv_extractor(tmp_path: Path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("id,agent,status\n1,retrieval,active\n2,verification,active", encoding="utf-8")
    
    extractor = CSVExtractor()
    sections = extractor.extract(csv_file)
    assert len(sections) == 1
    assert "retrieval" in sections[0].text
    assert "verification" in sections[0].text
    assert sections[0].metadata["rows"] == 2

