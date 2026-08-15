"""API tests via FastAPI TestClient."""

from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app())


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "solver_service"}


def test_solve_ok():
    response = client.post("/solve", json={"expression": "5*8"})
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "40"
    assert body["expression"] == "5*8"
    assert isinstance(body["steps"], list) and body["steps"]
    assert all(isinstance(step, str) for step in body["steps"])


def test_solve_fraction_exact():
    response = client.post("/solve", json={"expression": "1/2 + 1/4"})
    assert response.status_code == 200
    assert response.json()["answer"] == "3/4"


def test_solve_khmer_numerals():
    response = client.post("/solve", json={"expression": "៥*៨"})
    assert response.status_code == 200
    assert response.json()["answer"] == "40"


def test_solve_invalid_expression_is_422_with_structured_detail():
    response = client.post("/solve", json={"expression": "__import__('os')"})
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "error" in detail and "expression" in detail
    assert "Traceback" not in response.text


def test_solve_division_by_zero_is_422_not_500():
    response = client.post("/solve", json={"expression": "5/0"})
    assert response.status_code == 422
    assert "error" in response.json()["detail"]


def test_solve_missing_body_field_is_422():
    response = client.post("/solve", json={})
    assert response.status_code == 422
