"""Pytest fixtures for retrieval_service."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SERVICE_ROOT = str(Path(__file__).resolve().parents[1])
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)

from app.core.retriever import VectorRetriever
from app.ingest.seed_textbooks import DEFAULT_CHUNKS
from app.main import create_app


@pytest.fixture
def retriever():
    return VectorRetriever()


@pytest.fixture
def client(retriever):
    app = create_app(retriever=retriever)
    with TestClient(app) as test_client:
        yield test_client
