"""
Test fixtures.

Tests never touch PostgreSQL: an in-memory SQLite database is created per test
and injected through FastAPI's dependency override for `get_db`.
"""

import os

os.environ["DATABASE_URL"] = "sqlite://"  # must be set before app modules import settings

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = testing_session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_ticket():
    return {
        "subject": "Laptop will not boot",
        "description": "Black screen after the latest firmware update.",
        "category": "HARDWARE",
        "priority": "HIGH",
        "requester": "asha.menon@example.com",
    }
