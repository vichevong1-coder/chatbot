# Architecture & Repository Structure

Replaces `k12-tutor-bot-full-structure.md`. For data shapes and endpoint signatures see
`contracts.md`; for build order see `plan.md`.

---

## 1. Request flow

```
                    ┌─────────────────────────────────────────┐
   browser ────────▶│ frontend_tunsay/  (Vite SPA + Express)  │  :3000
                    │  server.ts — serves SPA, proxies /api/* │
                    └────────────────────┬────────────────────┘
                                         │  HTTP
                    ┌────────────────────▼────────────────────┐
                    │ gateway/           cors → auth → limit  │  :8000
                    └───────┬─────────────────────────┬───────┘
                            │                         │
                ┌───────────▼──────────┐   ┌──────────▼───────────┐
                │ auth_service         │   │ orchestrator         │
                │ JWT, students only   │   │ LangGraph state m/c  │
                └──────────────────────┘   └──────────┬───────────┘
                                                      │ service_clients/
    ┌──────────────┬──────────────┬───────────┬───────┴───┬──────────────┐
    ▼              ▼              ▼           ▼           ▼              ▼
 safety_svc    content_svc    solver_svc  grading_svc  pedagogy_svc  retrieval_svc
                                                             │            │
                                  student_profile_svc     Gemini       Qdrant
                                  stt_svc · ocr_svc
```

Rules that keep this from rotting:

1. **The gateway is the only public surface.** No service is exposed to the browser.
   Content admin has no gateway route at all — it is reachable only from inside the compose
   network (`contracts.md` §4).
2. **Only the orchestrator fans out.** Services never call each other. A service that needs
   another service's data is a design smell — the orchestrator composes.
3. **`dal/` is a shared library, not a service.** Imported by everyone; imports nothing local.
4. **`pedagogy_service` is the only place that talks to Gemini.** One prompt, one key, one
   place to change the tutor's voice.

## 2. The orchestrator graph

The LangGraph state machine is the tutor's brain. `state.py` carries `student_id`,
`session_id`, `language`, `mode`, `problem_id`, `active_step_index`, and the transcript.
There is no `role` — every account is a student, and `mode` is the student/parent toggle.

```
input_normalizer ──▶ safety_gate ──(unsafe)──▶ refusal response
        │                 │
        │              (safe)
        │                 ▼
        └──────────▶ intent_router
                          │
     ┌──────────┬─────────┼──────────┬──────────────┐
     ▼          ▼         ▼          ▼              ▼
  clarify     solve  check_answer  explain   recommend_next
```

| Node | Responsibility |
|---|---|
| `input_normalizer` | unify text / transcript / OCR output into one prompt; normalize math notation |
| `safety_gate` | call `safety_service` **before** spending a token; also screens output |
| `intent_router` | classify: asking a question · submitting an answer · asking for a hint · off-topic |
| `clarify` | the input was ambiguous — ask the child one short question back |
| `solve` | `solver_service` computes the answer, for the tutor's eyes only |
| `check_answer` | `grading_service` grades + classifies the misconception |
| `explain` | `pedagogy_service` generates the grade-banded explanation |
| `recommend_next` | `student_profile_service` picks the next problem from mastery data |

`heuristics.py` holds the cheap non-LLM shortcuts (an exact numeric match does not need a
model call). `session_store/cache.py` memoizes repeated explanation requests — the first
real lever against LLM cost, since thirty children in one class ask the same question.

## 3. Repository tree

Legend: **[REAL]** has content · **[EMPTY]** exists, 0 bytes · **[ADD]** does not exist yet ·
**[DELETE]** should be removed.

```
chatbot/
├── .env                              [EMPTY]  see plan.md §0 for required vars
├── .env.example                      [EMPTY]
├── .gitignore                        [EMPTY]  must ignore .env, __pycache__, node_modules, dist
├── README.md                         [EMPTY]
├── docker-compose.yml                [EMPTY]  the ONE compose file — see §4
├── .claude/                          agent documentation (this directory)
│   └── claude.md · architecture.md · contracts.md · plan.md
│
├── frontend_tunsay/                  [REAL]   first-class source in this repo — edit freely
│                                     React 19 · Vite 6 · Tailwind 4 · motion · lucide
│   ├── server.ts                     [REAL]   Express BFF → becomes a gateway proxy
│   ├── src/
│   │   ├── App.tsx                   [REAL]   landing → login → app shell; all state is useState
│   │   ├── types.ts                  [REAL]   ⭐ the real data model — see contracts.md §2
│   │   ├── data/mockProblems.ts      [REAL]   ⭐ 7 problems — the seed corpus.
│   │                                          g4×4, g3×2, g5×1, g6×0 — see plan.md risks
│   │   ├── services/geminiService.ts [REAL]   the one network call; repoint at the gateway
│   │   ├── components/
│   │   │   ├── ChatView.tsx          [REAL]   ⭐ the tutoring loop lives here
│   │   │   ├── StepCard.tsx          [REAL]   mcq / number / text answer widgets
│   │   │   ├── StepTrail.tsx         [REAL]   step 3 of 5 progress rail
│   │   │   ├── HintSheet.tsx         [REAL]   the 3-rung hint ladder
│   │   │   ├── ExplanationCard.tsx   [REAL]   "explain differently" + analogy
│   │   │   ├── HomeworkScanner.tsx   [REAL]   ⚠ fake OCR — picks from MOCK_PROBLEMS
│   │   │   ├── VoiceModal.tsx        [REAL]   ⚠ fake STT — canned transcript on a timer
│   │   │   ├── LoginView.tsx         [REAL]   ⚠ 3 flows, school code + PIN, all discarded
│   │   │   ├── ProfileView.tsx       [REAL]   ⚠ in-memory stars/progress
│   │   │   ├── LandingView.tsx       [REAL]   public marketing page
│   │   │   ├── Header.tsx · TunsayAvatar.tsx · CelebrationOverlay.tsx
│   │   │   ├── GradeSubjectSelector.tsx · HomeView.tsx
│   │   │   ├── LanguageSwitcher.tsx · ModeSwitcher.tsx
│   │   └── utils/language.ts         [REAL]   getDisplayName — splits "សុជា (Sochea)"
│   └── .git/                         [DELETE] clone leftover; blocks root git tracking (D0.2)
│
├── dal/                              shared package — imported by every Python service
│   ├── pyproject.toml                [ADD]    ⚠ WITHOUT THIS, dal/ CANNOT BE IMPORTED
│   ├── models/                       [EMPTY]  SQLAlchemy: User, Problem, Step, Attempt,
│   │                                          StudentProfile, Session
│   ├── schemas/                      [EMPTY]  Pydantic — mirror contracts.md §2 exactly
│   ├── repositories/                 [EMPTY]
│   ├── clients/                      [EMPTY]  Redis, Qdrant, object storage wrappers
│   └── llm_client.py                 [EMPTY]  Gemini wrapper: retry, timeout, token accounting
│
├── gateway/                          the single front door
│   ├── app/routes/                   chat.py · chat_audio.py · auth.py
│   │                                 [ADD] chat_image.py · problems.py · answers.py
│   │                                 (admin.py deleted — never gateway-routed)
│   ├── app/middleware/               cors.py · auth_verify.py · rate_limit.py
│   └── Dockerfile · requirements.txt
│
├── auth_service/
│   ├── app/api/                      register.py · login.py · me.py
│   ├── app/core/                     password_hashing.py · jwt_handler.py
│   ├── app/infrastructure/           repository.py — users (students), schools
│   └── alembic/
│
├── orchestrator/                     the brain
│   ├── app/core/graph/               state.py · builder.py · edges.py
│   │   └── nodes/                    input_normalizer · intent_router · clarify · solve
│   │                                 check_answer · explain · recommend_next · safety_gate
│   ├── app/core/heuristics.py        non-LLM shortcuts
│   ├── app/infrastructure/service_clients/   one typed client per service (10 files)
│   ├── app/session_store/            redis_store · postgres_store · summarizer · cache
│   ├── app/utils/logging.py          structured logging — shared format
│   ├── app/api/                      chat.py · chat_audio.py · health.py [ADD] chat_image.py
│   ├── tests/golden_queries/         frozen routing regressions
│
├── content_service/
│   ├── app/api/admin.py              CRUD for problems — internal network only
│   ├── scripts/seed_exercises.py     ⚠ source is mockProblems.ts — contracts.md §6
│   └── seed_data/                    [ADD] YAML transcoded from mockProblems.ts
│
├── solver_service/       app/core/   math_solver.py · step_formatter.py
├── grading_service/      app/core/   checker.py · misconception_classifier.py
├── pedagogy_service/     app/core/   explanation_generator.py
│   └── app/ai/prompts/               explain_grade4_6.yaml   ← current focus, build first
│                                     explain_grade1_3.yaml   secondary
│                                     explain_grade7_9.yaml   future — keep, leave stubbed
│                                     explain_grade10_12.yaml future — keep, leave stubbed
├── retrieval_service/    app/core/retriever.py · app/ingest/
├── student_profile_service/ app/core/mastery_model.py
│                            app/infrastructure/progress_repository.py
├── stt_service/          app/core/  audio_preprocess · transcriber · language_detect
│                                    math_notation_normalizer
├── ocr_service/          app/core/  image_preprocess.py · math_ocr.py
└── safety_service/       app/core/  age_gate.py · content_filter.py
```

Every Python file above is currently 0 bytes. The directory layout is sound and worth
keeping — it is a good skeleton with no muscle on it.

## 4. Infrastructure

**One compose file, not thirteen.** Each service currently ships its own
`docker-compose.yml` alongside the root one. Twelve services cannot be brought up together
from twelve separate compose files, and the per-service copies will drift within a week.
Consolidate into the root `docker-compose.yml`; keep the per-service `Dockerfile`s, delete
the per-service compose files.

Backing services:

| | Used by | Purpose |
|---|---|---|
| **Postgres** | auth, content, profile, orchestrator | system of record |
| **Redis** | orchestrator | session store, explanation cache, rate-limit counters |
| **Qdrant** | retrieval_service | curriculum embeddings |
| **MinIO** | ocr, stt | uploaded homework images and audio |

Port convention — gateway `8000`, orchestrator `8001`, auth `8002`, content `8003`, solver
`8004`, grading `8005`, pedagogy `8006`, retrieval `8007`, profile `8008`, stt `8009`, ocr
`8010`, safety `8011`, frontend `3000`. Only `3000` and `8000` bind to the host.

## 5. Deferred by decision

Not oversights — record the reason so they are not relitigated each session.

| Deferred | Why | Revisit when |
|---|---|---|
| Kubernetes | docker-compose is enough for one developer | more than one deploy target |
| Notification service | not on the core loop | parents ask for progress digests |
| Multi-tenancy (school/class) | one pilot school | a second school signs |
| Prometheus / Grafana | structured logs suffice | real traffic, real incidents |
| WebSocket audio streaming | blob upload is far simpler | latency becomes a complaint |
| Grades 1–3 and 7–12 | team is building grades 4–6 first; 1–12 is the eventual target | 4–6 is solid end-to-end |
| Offline / low-bandwidth mode | **not yet considered** — likely matters for Cambodian schools | before any field pilot |
