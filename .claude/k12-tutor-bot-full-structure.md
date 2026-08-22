# K-12 Tutor Bot — Full Structure (v3: + auth, gateway, seeding)

Assumption: `dal/` is a **shared package**, imported by every service rather than deployed standalone.
Flag if your GDCE `dal/` is actually its own deployed microservice.

```
k12-tutor-bot/
│
├── .env
├── .env.example
├── .gitignore
├── docker-compose.yml               # wires every service + Postgres, Redis, Qdrant, minio
├── README.md
│
├── frontend_tunsay/                        # NEW — web app
│   ├── src/
│   │   ├── api/
│   │   │   └── client.ts            # fetch wrapper, hits gateway/ endpoints only, never services directly
│   ├── package.json
│   └── .env.example
│
├── gateway/                         # single front door, routes to all services
│   ├── app/
│   │   ├── routes/
│   │   │   ├── chat.py              # proxies to orchestrator /chat
│   │   │   ├── chat_audio.py        # proxies to orchestrator /chat/audio — accepts multipart upload
│   │   │   ├── auth.py              # proxies to auth_service
│   │   │   └── admin.py             # proxies to content_service admin endpoints
│   │   ├── middleware/
│   │   │   ├── cors.py              # NEW — allows frontend origin only
│   │   │   ├── rate_limit.py        # per-student rate limiting on LLM-cost-heavy endpoints
│   │   │   └── auth_verify.py       # validates JWT/session before forwarding
│   │   └── main.py
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── requirements.txt
│
├── auth_service/                    # NEW — students, parents, teachers
│   ├── app/
│   │   ├── api/
│   │   │   ├── register.py
│   │   │   ├── login.py
│   │   │   └── me.py
│   │   ├── core/
│   │   │   ├── password_hashing.py
│   │   │   └── jwt_handler.py
│   │   ├── infrastructure/
│   │   │   └── repository.py        # users table: student | parent | teacher role
│   │   ├── schemas/
│   │   └── main.py
│   ├── alembic/                     # users, roles, parent_student_link tables
│   ├── tests/
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── requirements.txt
│
├── dal/                             # shared data-access-layer package
│   ├── __init__.py
│   ├── models/                      # SQLAlchemy: Exercise, StudentAnswer, StudentProfile, Session, User
│   ├── schemas/                     # Pydantic: Problem, StudentAnswer, GradeLevel, TutorState
│   ├── repositories/
│   ├── clients/                     # Redis, Qdrant, minio client wrappers
│   └── llm_client.py
│
├── orchestrator/
│   ├── app/
│   │   ├── ai/
│   │   │   └── prompts/
│   │   ├── api/
│   │   │   ├── chat.py
│   │   │   ├── chat_audio.py
│   │   │   └── health.py
│   │   ├── core/
│   │   │   ├── graph/
│   │   │   │   ├── state.py         # + student_id, role (auth-aware now)
│   │   │   │   ├── builder.py
│   │   │   │   ├── edges.py
│   │   │   │   └── nodes/
│   │   │   │       ├── input_normalizer.py
│   │   │   │       ├── intent_router.py
│   │   │   │       ├── clarify.py
│   │   │   │       ├── solve.py
│   │   │   │       ├── check_answer.py
│   │   │   │       ├── explain.py
│   │   │   │       ├── recommend_next.py
│   │   │   │       └── safety_gate.py
│   │   │   └── heuristics.py
│   │   ├── infrastructure/
│   │   │   ├── db.py
│   │   │   ├── redis_client.py
│   │   │   └── service_clients/
│   │   │       ├── auth_client.py   # NEW — validates student_id, fetches grade/role
│   │   │       ├── content_client.py
│   │   │       ├── solver_client.py
│   │   │       ├── grading_client.py
│   │   │       ├── pedagogy_client.py
│   │   │       ├── retrieval_client.py
│   │   │       ├── stt_client.py
│   │   │       ├── profile_client.py
│   │   │       ├── ocr_client.py
│   │   │       └── safety_client.py
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── session_store/
│   │   │   ├── redis_store.py
│   │   │   ├── postgres_store.py
│   │   │   ├── summarizer.py
│   │   │   └── cache.py             # NEW — caches repeated explanation requests, cuts LLM cost
│   │   ├── utils/
│   │   │   └── logging.py           # NEW — structured logging, shared format across services
│   │   ├── __init__.py
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   │   └── golden_queries/
│   ├── conftest.py
│   ├── alembic.ini
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── pytest.ini
│   └── requirements.txt
│
├── content_service/
│   ├── app/
│   │   ├── api/
│   │   │   └── admin.py             # NEW — CRUD endpoints for adding/editing exercises
│   │   ├── core/
│   │   │   └── models.py
│   │   ├── infrastructure/
│   │   │   └── repository.py
│   │   ├── schemas/
│   │   └── main.py
│   ├── scripts/
│   │   └── seed_exercises.py        # NEW — CSV/YAML import convention, run on deploy/setup
│   ├── seed_data/
│   │   └── grade4_fractions.yaml    # NEW — example seed file format
│   ├── alembic/
│   ├── tests/
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── requirements.txt
│
├── solver_service/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   │   ├── math_solver.py
│   │   │   └── step_formatter.py
│   │   └── main.py
│   ├── tests/
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── requirements.txt
│
├── grading_service/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   │   ├── checker.py
│   │   │   └── misconception_classifier.py
│   │   └── main.py
│   ├── tests/
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── requirements.txt
│
├── pedagogy_service/
│   ├── app/
│   │   ├── ai/
│   │   │   └── prompts/
│   │   │       ├── explain_grade1_3.yaml
│   │   │       ├── explain_grade4_6.yaml
│   │   │       ├── explain_grade7_9.yaml
│   │   │       └── explain_grade10_12.yaml
│   │   ├── api/
│   │   ├── core/
│   │   │   └── explanation_generator.py
│   │   └── main.py
│   ├── tests/
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── requirements.txt
│
├── retrieval_service/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   │   └── retriever.py
│   │   ├── ingest/
│   │   └── main.py
│   ├── tests/
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── requirements.txt
│
├── stt_service/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   │   ├── audio_preprocess.py
│   │   │   ├── transcriber.py
│   │   │   ├── language_detect.py
│   │   │   └── math_notation_normalizer.py
│   │   └── main.py
│   ├── tests/
│   │   └── test_stt_normalization.py
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── requirements.txt
│
├── student_profile_service/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   │   └── mastery_model.py
│   │   ├── infrastructure/
│   │   │   └── progress_repository.py
│   │   └── main.py
│   ├── tests/
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── requirements.txt
│
├── ocr_service/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   │   ├── image_preprocess.py
│   │   │   └── math_ocr.py
│   │   └── main.py
│   ├── tests/
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── requirements.txt
│
└── safety_service/
    ├── app/
    │   ├── api/
    │   ├── core/
    │   │   ├── age_gate.py
    │   │   └── content_filter.py
    │   └── main.py
    ├── tests/
    ├── docker-compose.yml
    ├── Dockerfile
    └── requirements.txt
```

## What changed from v2

| Addition | Where | Why |
|---|---|---|
| `gateway/` | new top-level service | Single front door, rate limiting, auth verification before requests hit orchestrator |
| `auth_service/` | new top-level service | Students/parents/teachers need identity; `student_profile_service` needs a reliable key |
| `auth_client.py` | `orchestrator/infrastructure/service_clients/` | Orchestrator validates who's talking before routing |
| `student_id`, `role` | `orchestrator/core/graph/state.py` | TutorState becomes auth-aware |
| `content_service/app/api/admin.py` + `scripts/seed_exercises.py` + `seed_data/` | content_service | Concrete answer to "how do exercises get in" — seed files + admin CRUD, not left undefined |
| `session_store/cache.py` | orchestrator | Caches repeated explanation requests — first real lever against LLM cost blowup |
| `utils/logging.py` | orchestrator | Structured logging convention, shared format — start this now, not after your first cross-service debugging nightmare |

## Still deliberately NOT built (don't let Fable over-scope)

- Kubernetes — docker-compose is enough solo
- Notification service — not core loop
- Multi-tenancy (school/class grouping) — add once you have more than one pilot
- Full observability stack (Prometheus/Grafana) — `utils/logging.py` structured logs are enough for now, revisit once you have real traffic

## Frontend decision: web-based (confirmed)

- **Audio**: browser records via `VoiceRecorder.tsx`, sends the recorded blob as a `multipart/form-data`
  upload to `gateway/chat_audio.py` — no websocket/streaming needed for v1. Simpler to build, add
  streaming later only if latency becomes a real problem.
- **CORS**: `gateway/app/middleware/cors.py` allows only the frontend's origin.
- **Auth**: JWT issued by `auth_service`, stored client-side (httpOnly cookie preferred over
  localStorage for XSS safety), attached to every request via `client.ts`.
- **Frontend never calls services directly** — always through `gateway/`, same as everything else.

## Build order (unchanged core, auth + frontend pulled forward)

Phase 1: `dal/` → `auth_service` (bare register/login) → `content_service` (seed script + hardcoded
problems) → `solver_service` → bare `orchestrator` (text only, auth-aware) → `gateway` (thin proxy)
→ `frontend` minimal chat UI hitting gateway `/chat` — get ONE real end-to-end turn visible in a
browser before adding anything else.

Everything else follows the same phase plan as before — `stt_service` and `VoiceRecorder.tsx` stay a
late addition (Phase 3+), once the text loop works end-to-end in the browser.
