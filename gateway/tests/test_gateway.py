"""End-to-end gateway behavior against mocked upstreams.

Covers every acceptance item in plan.md P1.9, with the forged-student_id
overwrite as the security-critical centerpiece.
"""

from __future__ import annotations

import json

from tests.conftest import FRONTEND_ORIGIN, KHMER_REPLY, bearer, make_token

KHMER_PROMPT = "ហេតុអ្វីខ្ញុំត្រូវគុណ? ១២ ÷ ៣"


def _assert_bilingual_detail(payload: dict) -> None:
    detail = payload["detail"]
    assert detail["messageKhmer"].strip()
    assert detail["messageEng"].strip()


# ---------------------------------------------------------------------------
# Auth enforcement
# ---------------------------------------------------------------------------


class TestAuthVerify:
    def test_chat_without_token_is_401_bilingual(self, client, upstreams):
        response = client.post("/chat", json={"prompt": "hi"})
        assert response.status_code == 401
        _assert_bilingual_detail(response.json())
        assert upstreams.requests == []  # never reached the orchestrator

    def test_chat_with_valid_token_is_200_and_upstream_received_it(self, client, upstreams):
        response = client.post(
            "/chat",
            json={"prompt": "hi", "sessionId": "sess-9"},
            headers=bearer(make_token()),
        )
        assert response.status_code == 200
        assert len(upstreams.requests) == 1
        assert upstreams.requests[0].url.path == "/chat"

    def test_expired_token_is_401(self, client):
        token = make_token(expires_in_seconds=-60)
        response = client.post("/chat", json={"prompt": "hi"}, headers=bearer(token))
        assert response.status_code == 401
        _assert_bilingual_detail(response.json())

    def test_tampered_signature_is_401(self, client):
        token = make_token(secret="a-completely-different-secret-key-000000")
        response = client.post("/chat", json={"prompt": "hi"}, headers=bearer(token))
        assert response.status_code == 401
        _assert_bilingual_detail(response.json())

    def test_problems_requires_token(self, client):
        assert client.get("/problems").status_code == 401

    def test_profile_requires_token(self, client):
        assert client.get("/profile/student-1").status_code == 401

    def test_auth_me_requires_token_and_forwards_authorization(self, client, upstreams):
        assert client.get("/auth/me").status_code == 401
        token = make_token()
        response = client.get("/auth/me", headers=bearer(token))
        assert response.status_code == 200
        assert upstreams.requests[-1].headers["authorization"] == f"Bearer {token}"


# ---------------------------------------------------------------------------
# THE security-critical behavior: student_id comes from the JWT, never the body
# ---------------------------------------------------------------------------


class TestStudentIdInjection:
    def test_forged_student_id_is_overwritten_by_jwt_sub(self, client, upstreams):
        response = client.post(
            "/chat",
            json={"prompt": "hi", "studentId": "classmate-i-am-impersonating"},
            headers=bearer(make_token("student-real")),
        )
        assert response.status_code == 200
        sent = upstreams.last_json()
        assert sent["student_id"] == "student-real"
        assert "classmate-i-am-impersonating" not in json.dumps(sent)

    def test_snake_case_forgery_also_overwritten(self, client, upstreams):
        client.post(
            "/chat",
            json={"prompt": "hi", "student_id": "forged"},
            headers=bearer(make_token("student-real")),
        )
        assert upstreams.last_json()["student_id"] == "student-real"

    def test_student_id_injected_even_when_body_omits_it(self, client, upstreams):
        client.post("/chat", json={"prompt": "hi"}, headers=bearer(make_token("student-42")))
        assert upstreams.last_json()["student_id"] == "student-42"


# ---------------------------------------------------------------------------
# camelCase boundary
# ---------------------------------------------------------------------------


class TestCaseBoundary:
    def test_camel_in_upstream_sees_snake(self, client, upstreams):
        client.post(
            "/chat",
            json={
                "prompt": KHMER_PROMPT,
                "sessionId": "sess-1",
                "problemId": "math-g4-apples",
                "activeStepIndex": 0,
            },
            headers=bearer(make_token()),
        )
        sent = upstreams.last_json()
        assert sent["session_id"] == "sess-1"
        assert sent["problem_id"] == "math-g4-apples"
        assert sent["active_step_index"] == 0
        assert "sessionId" not in sent and "problemId" not in sent

    def test_upstream_snake_out_client_gets_camel(self, client):
        response = client.post(
            "/chat", json={"prompt": "hi"}, headers=bearer(make_token())
        )
        body = response.json()
        assert "textKhmer" in body and "isSafetyRefusal" in body
        assert "text_khmer" not in body and "is_safety_refusal" not in body

    def test_khmer_values_byte_identical_through_both_translations(self, client, upstreams):
        client.post(
            "/chat", json={"prompt": KHMER_PROMPT}, headers=bearer(make_token())
        )
        # Inbound: the orchestrator received the exact Khmer bytes.
        assert upstreams.last_json()["prompt"].encode("utf-8") == KHMER_PROMPT.encode("utf-8")
        # Outbound: the client received the mock's Khmer reply byte-identical.
        response = client.post(
            "/chat", json={"prompt": KHMER_PROMPT}, headers=bearer(make_token())
        )
        assert response.json()["textKhmer"].encode("utf-8") == KHMER_REPLY.encode("utf-8")

    def test_login_public_and_response_camelcased(self, client, upstreams):
        response = client.post(
            "/auth/login",
            json={"studentName": "សុជា (Sochea)", "schoolCode": "TUNSAY-G4-DEMO", "pin": "1234"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["accessToken"] == "issued-token"
        assert body["userProfile"]["studentName"] == "សុជា (Sochea)"
        assert "access_token" not in body
        # And the upstream saw snake_case.
        sent = upstreams.last_json()
        assert sent["student_name"] == "សុជា (Sochea)"
        assert sent["school_code"] == "TUNSAY-G4-DEMO"


# ---------------------------------------------------------------------------
# /problems
# ---------------------------------------------------------------------------


class TestProblems:
    def test_query_params_forwarded_and_response_camelcased(self, client, upstreams):
        response = client.get(
            "/problems", params={"grade": "4", "subject": "math"}, headers=bearer(make_token())
        )
        assert response.status_code == 200
        sent = upstreams.requests[-1]
        assert sent.url.params["grade"] == "4"
        assert sent.url.params["subject"] == "math"
        body = response.json()
        assert body[0]["titleKhmer"] == "ចែកផ្លែប៉ោម"
        assert "title_khmer" not in body[0]
        assert body[0]["steps"][0]["stepNumber"] == 1

    def test_problem_by_id(self, client, upstreams):
        response = client.get("/problems/math-g4-apples", headers=bearer(make_token()))
        assert response.status_code == 200
        assert upstreams.requests[-1].url.path == "/problems/math-g4-apples"
        assert response.json()["id"] == "math-g4-apples"


# ---------------------------------------------------------------------------
# Rate limiting — /chat* only, per verified student
# ---------------------------------------------------------------------------


class TestRateLimit:
    def test_21st_rapid_chat_request_is_429_with_retry_after(self, client):
        headers = bearer(make_token("student-limited"))
        for _ in range(20):
            assert client.post("/chat", json={"prompt": "hi"}, headers=headers).status_code == 200
        response = client.post("/chat", json={"prompt": "hi"}, headers=headers)
        assert response.status_code == 429
        assert int(response.headers["Retry-After"]) >= 1
        _assert_bilingual_detail(response.json())

    def test_problems_not_rate_limited_at_same_volume(self, client):
        headers = bearer(make_token("student-limited"))
        for _ in range(25):
            assert client.get("/problems", headers=headers).status_code == 200

    def test_students_have_independent_buckets(self, client):
        headers_a = bearer(make_token("student-a"))
        headers_b = bearer(make_token("student-b"))
        for _ in range(20):
            client.post("/chat", json={"prompt": "hi"}, headers=headers_a)
        assert client.post("/chat", json={"prompt": "hi"}, headers=headers_a).status_code == 429
        assert client.post("/chat", json={"prompt": "hi"}, headers=headers_b).status_code == 200

    def test_window_expiry_resets_the_bucket(self, client, clock):
        headers = bearer(make_token("student-limited"))
        for _ in range(21):
            client.post("/chat", json={"prompt": "hi"}, headers=headers)
        clock.advance(61)
        assert client.post("/chat", json={"prompt": "hi"}, headers=headers).status_code == 200


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------


class TestCors:
    PREFLIGHT = {
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Authorization, Content-Type",
    }

    def test_evil_origin_preflight_gets_no_allow_origin(self, client):
        response = client.options(
            "/chat", headers={"Origin": "http://evil.example", **self.PREFLIGHT}
        )
        assert "access-control-allow-origin" not in response.headers

    def test_frontend_origin_preflight_allowed(self, client):
        response = client.options(
            "/chat", headers={"Origin": FRONTEND_ORIGIN, **self.PREFLIGHT}
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == FRONTEND_ORIGIN
        assert response.headers["access-control-allow-credentials"] == "true"


# ---------------------------------------------------------------------------
# No admin surface
# ---------------------------------------------------------------------------


class TestNoAdmin:
    def test_admin_anything_is_404(self, client, upstreams):
        assert client.get("/admin/anything").status_code == 404
        assert client.post("/admin/problems", json={}).status_code == 404
        assert (
            client.get("/admin/anything", headers=bearer(make_token())).status_code == 404
        )
        assert upstreams.requests == []  # nothing proxied anywhere


# ---------------------------------------------------------------------------
# Failure paths and health
# ---------------------------------------------------------------------------


class TestFailureAndHealth:
    def test_upstream_down_is_structured_bilingual_502(self, down_client):
        response = down_client.post(
            "/chat", json={"prompt": "hi"}, headers=bearer(make_token())
        )
        assert response.status_code == 502
        payload = response.json()
        _assert_bilingual_detail(payload)
        assert "Traceback" not in response.text
        assert "ConnectError" not in response.text

    def test_health_reports_per_service_status(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok" and body["service"] == "gateway"
        assert body["auth_service"] == "ok"
        assert body["orchestrator"] == "ok"
        assert body["content_service"] == "ok"

    def test_health_still_200_when_everything_is_down(self, down_client):
        response = down_client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["auth_service"] == "down"
        assert body["orchestrator"] == "down"
        assert body["content_service"] == "down"

    def test_chat_audio_proxies_multipart_through(self, client, upstreams):
        response = client.post(
            "/chat/audio",
            files={"file": ("q.webm", b"\x1aE\xdf\xa3fake-audio-bytes", "audio/webm")},
            data={"session_id": "sess-1", "language": "km"},
            headers=bearer(make_token()),
        )
        # The fake orchestrator has no /chat/audio route -> its 404 passes
        # through untouched; the gateway's job is only to proxy.
        assert response.status_code == 404
        sent = upstreams.requests[-1]
        assert sent.url.path == "/chat/audio"
        assert sent.headers["content-type"].startswith("multipart/form-data")
        assert b"fake-audio-bytes" in sent.content


# ---------------------------------------------------------------------------
# /profile
# ---------------------------------------------------------------------------


class TestProfile:
    def test_profile_requires_token(self, client):
        assert client.get("/profile/student-1").status_code == 401
        assert client.post("/profile/hints", json={"rung": 1}).status_code == 401
        assert client.post("/profile/attempts", json={"problemId": "p1", "isCorrect": True}).status_code == 401

    def test_get_profile_injects_verified_student_id_and_camelcases(self, client, upstreams):
        token = make_token("student-real")
        # Even if client requests a forged student_id in path, gateway injects verified student_id
        response = client.get("/profile/impersonated-student", headers=bearer(token))
        assert response.status_code == 200
        sent = upstreams.requests[-1]
        assert sent.url.path == "/profile/student-real"
        body = response.json()
        assert body["studentId"] == "student-real"
        assert body["completedProblemsCount"] == 5
        assert "completed_problems_count" not in body
        assert body["masteryLevels"] == {"fractions": 0.8}

    def test_profile_hints_injects_verified_student_id(self, client, upstreams):
        token = make_token("student-real")
        response = client.post(
            "/profile/hints",
            json={"rung": 2, "studentId": "impersonated", "problemId": "p-1", "stepId": "s-1"},
            headers=bearer(token),
        )
        assert response.status_code == 200
        sent = upstreams.last_json()
        assert sent["student_id"] == "student-real"
        assert sent["rung"] == 2
        body = response.json()
        assert body["remainingStars"] == 14
        assert "remaining_stars" not in body

    def test_profile_attempts_injects_verified_student_id(self, client, upstreams):
        token = make_token("student-real")
        response = client.post(
            "/profile/attempts",
            json={"studentId": "fake", "problemId": "p-1", "stepId": "s-1", "isCorrect": True},
            headers=bearer(token),
        )
        assert response.status_code == 201
        sent = upstreams.last_json()
        assert sent["student_id"] == "student-real"
        assert sent["is_correct"] is True
