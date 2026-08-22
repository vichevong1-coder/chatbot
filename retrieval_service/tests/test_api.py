from __future__ import annotations

import sys
from pathlib import Path

SERVICE_ROOT = str(Path(__file__).resolve().parents[1])
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["service"] == "retrieval_service"


def test_retrieve_endpoint(client):
    res = client.post(
        "/retrieve",
        json={"query": "water cycle", "grade": 4, "subject": "science", "top_k": 2},
    )
    assert res.status_code == 200
    body = res.json()
    assert "results" in body
    assert body["total_found"] > 0
    assert any("Water" in r["title_eng"] or "ទឹក" in r["title_khmer"] for r in body["results"])


def test_ingest_endpoint(client):
    new_chunk = {
        "id": "custom-1",
        "grade": 3,
        "subject": "math",
        "topic": "addition",
        "title_khmer": "វិធីបូក",
        "title_eng": "Addition",
        "text_khmer": "ការបូកលេខពីរបញ្ចូលគ្នា",
        "text_eng": "Adding two numbers together",
    }
    res = client.post("/ingest", json={"chunks": [new_chunk]})
    assert res.status_code == 200
    assert res.json()["indexed_count"] == 1
