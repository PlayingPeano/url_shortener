import os
from pathlib import Path

TEST_DB_PATH = Path("tests/test.db")
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.pop("API_KEY", None)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.api.main as api_main
from app.api.main import app, get_db
from app.db.database import Base

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def secured_client(client):
    original_key = api_main.API_KEY
    api_main.API_KEY = "test-secret-key"
    try:
        yield client
    finally:
        api_main.API_KEY = original_key