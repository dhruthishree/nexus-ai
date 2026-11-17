import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import tempfile
import shutil

from app.db.session import Base, get_db
from app.main import app
from app.core.config import settings

@pytest.fixture(scope="session")
def test_temp_dir():
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture(scope="function")
def db_session(test_temp_dir):
    test_db_file = test_temp_dir / "test_nexus.db"
    test_engine = create_engine(f"sqlite:///{test_db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def client(db_session, test_temp_dir):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Override upload directory to temporary test folder
    settings.STORAGE_DIR = test_temp_dir / "uploads"
    settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

