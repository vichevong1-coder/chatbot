"""End-to-end auth_service tests over the FastAPI app with a SQLite-backed repository.

Covers the P1.3 verify criteria: school-code registration resolving grade, uniqueness
scoped to the school, PIN semantics (optional / required / wrong / throttled), and the
JWT round-trip through /me — with the Khmer display name surviving unmangled.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt as pyjwt

KHMER_NAME = "សុជា (Sochea)"
DEMO = "TUNSAY-G4-DEMO"
OTHER = "TUNSAY-G5-OTHER"


def register(client, **overrides):
    payload = {"student_name": KHMER_NAME, "school_code": DEMO, "pin": "1234"}
    payload.update(overrides)
    return client.post("/register", json=payload)


def login(client, **overrides):
    payload = {"student_name": KHMER_NAME, "school_code": DEMO, "pin": "1234"}
    payload.update(overrides)
    return client.post("/login", json=payload)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "auth_service"}


def test_register_school_code_resolves_grade_4(client):
    resp = register(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    assert body["profile"]["grade"] == 4  # resolved from TUNSAY-G4-DEMO, not the request
    assert body["profile"]["name"] == KHMER_NAME


def test_register_public_signup_explicit_grade(client):
    resp = register(
        client,
        school_code=None,
        grade=5,
        parent_contact="012-345-678",
        pin="9876",
    )
    assert resp.status_code == 201
    assert resp.json()["profile"]["grade"] == 5


def test_register_unknown_school_code_structured_404(client):
    resp = register(client, school_code="TUNSAY-NOPE")
    assert resp.status_code == 404
    detail = resp.json()["detail"]
    assert detail["error"] == "unknown_school_code"
    assert detail["message_khmer"]
    assert detail["message_eng"]


def test_duplicate_name_same_school_409(client):
    assert register(client).status_code == 201
    resp = register(client)
    assert resp.status_code == 409
    detail = resp.json()["detail"]
    assert detail["error"] == "duplicate_student"
    assert detail["message_khmer"] and detail["message_eng"]


def test_same_name_different_school_both_succeed(client):
    assert register(client).status_code == 201
    resp = register(client, school_code=OTHER)
    assert resp.status_code == 201
    assert resp.json()["profile"]["grade"] == 5  # resolved from the other school


def test_login_right_pin_returns_token(client):
    register(client)
    resp = login(client)
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["profile"]["name"] == KHMER_NAME
    assert body["profile"]["grade"] == 4


def test_login_wrong_pin_401(client):
    register(client)
    resp = login(client, pin="0000")
    assert resp.status_code == 401
    assert resp.json()["detail"]["error"] == "invalid_credentials"


def test_repeated_wrong_pins_throttled_429(client):
    register(client)
    for _ in range(5):
        assert login(client, pin="0000").status_code == 401
    resp = login(client, pin="1234")  # even the right PIN is refused while locked
    assert resp.status_code == 429
    detail = resp.json()["detail"]
    assert detail["error"] == "too_many_attempts"
    assert detail["retry_after_seconds"] > 0
    assert "Retry-After" in resp.headers


def test_no_pin_account_logs_in_without_pin(client):
    register(client, pin=None)
    resp = login(client, pin=None)
    assert resp.status_code == 200
    assert resp.json()["profile"]["grade"] == 4


def test_pin_account_rejects_missing_pin(client):
    register(client)
    resp = login(client, pin=None)
    assert resp.status_code == 401
    assert resp.json()["detail"]["error"] == "invalid_credentials"


def test_unknown_identity_login_401(client):
    resp = login(client)
    assert resp.status_code == 401


def test_me_round_trips_khmer_name(client):
    token = register(client).json()["access_token"]
    resp = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == KHMER_NAME  # byte-for-byte, Khmer + transliteration intact
    assert body["grade"] == 4
    assert body["completed_problems_count"] == 0
    assert body["stars_earned"] == 0


def test_me_expired_token_401(client, monkeypatch):
    import os

    user_id = "does-not-matter"
    now = datetime.now(timezone.utc)
    expired = pyjwt.encode(
        {
            "sub": user_id,
            "student_name": KHMER_NAME,
            "school_code": DEMO,
            "grade": 4,
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
        },
        os.environ["JWT_SECRET"],
        algorithm="HS256",
    )
    resp = client.get("/me", headers={"Authorization": f"Bearer {expired}"})
    assert resp.status_code == 401
    assert resp.json()["detail"]["error"] == "invalid_token"


def test_me_tampered_token_401(client):
    token = register(client).json()["access_token"]
    header, payload, signature = token.split(".")
    tampered = f"{header}.{payload[:-2] + ('AA' if payload[-2:] != 'AA' else 'BB')}.{signature}"
    resp = client.get("/me", headers={"Authorization": f"Bearer {tampered}"})
    assert resp.status_code == 401


def test_me_missing_or_malformed_header_401(client):
    assert client.get("/me").status_code == 401
    assert client.get("/me", headers={"Authorization": "Token abc"}).status_code == 401
