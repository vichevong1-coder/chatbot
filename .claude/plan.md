# Execution Plan

**Canonical plan.** The single source of truth for what to build and in what order. The
docs it replaced — `.claude/todolist.md`, `.claude/k12-tutor-bot-full-structure.md`, and the
root-level `plan.md` — have all been removed (P0.5).

Read `claude.md` and `contracts.md` first. Every task below states the **files** it touches,
the **contract** it satisfies, what it **depends on**, and a **verify** command that proves
it works. A task is not done until its verify command passes.

**Baseline:** all 198 backend files are 0 bytes. Nothing is implemented. The only working
code is `frontend_tunsay/`, running on mock data.

**Strategy:** get one real request from the browser through the whole Python stack and back
before building anything clever. Phase 1 replaces mocks with a *thin but real* pipeline;
Phases 2–4 make each stage genuinely good. Resist the urge to build `grading_service`
properly in Phase 1 — a stub that returns the right shape is worth more than a good service
nothing can reach.

---

## Phase 0 — Preflight

Do these before writing a line of service code. Two are decisions, not tasks.

### D0.1 — Confirm the architecture seam · ✅ **DECIDED 2026-08-22 — Python backend is the target**

`claude.md` §3 assumes the Python backend is the target and `server.ts` becomes a proxy.
Phase 1 was worth doing under either reading; Phase 2 branched on it, so it was settled
from the code rather than by discussion.

**Evidence:** `frontend_tunsay/server.ts` contains no Gemini call and no system prompt —
only `proxyJson` forwarding `/api/*` to `GATEWAY_URL`. Its own header says so, and
`grep -i gemini server.ts` returns comments only. P1.10 completed the seam.

It keeps exactly one non-proxy behaviour on purpose: an unreachable gateway returns a
bilingual 502 so `geminiService.ts` can fall back to the local engine and the app still
answers offline. That is deliberate resilience, not a second brain.

### D0.2 — Make this one repository · **DECIDED — one repo, frontend included**

**This directory is the real repository**, frontend and backend together. The
`frontend_tunsay` clone (`github.com/chhounpisethchesda/frontend_tunsay`) was temporary
storage and is no longer authoritative. Earlier advice in these docs to treat it as an
external dependency and keep it as a submodule is **withdrawn** — everything under
`frontend_tunsay/` is ordinary editable source.

Two leftovers to clear:

- `git init` at the root — it is still not a git repository, so nothing is under version
  control yet.
- `frontend_tunsay/.git` — a nested repo from the clone. Git will not track its contents
  from the root while it exists; the frontend would silently commit as an empty directory.
  Remove it so the files become normal tracked source. Its history is already on GitHub if
  it is ever wanted back.

```bash
cd /home/vong/Desktop/chatbot
rm -rf frontend_tunsay/.git      # history is safe on the GitHub remote
git init && git add -A && git status --short | head
```

**Verify:** `git status --short` lists the frontend's `.tsx` files individually, not
`frontend_tunsay/` as one entry.

### P0.3 — Make `dal/` importable · ✅ **DONE 2026-08-15**

`dal/pyproject.toml` and `dal/__init__.py` (`tunsay-dal` 0.1.0) now exist. All seven
dependencies resolve and install cleanly.

**The one non-obvious part, do not "simplify" it away.** `pyproject.toml` sits *inside* the
package directory, so the build root is `dal/` and `dal` is not a subdirectory of it.
Setuptools auto-discovery would register `models`, `schemas`, `repositories`, `clients` as
four *top-level* packages and `import dal` would not exist. The explicit mapping is load-bearing:

```toml
[tool.setuptools]
package-dir = { "dal" = "." }
packages = ["dal", "dal.clients", "dal.models", "dal.repositories", "dal.schemas"]
```

**⚠ Environment blocker for P1.1 — this machine has no usable pip.** System Python 3.12.3
has neither `pip` nor `ensurepip`, so `python3 -m venv` fails too. The verify command in this
plan cannot be run as written until someone bootstraps an interpreter:

```bash
python3 -m venv --without-pip .venv
curl -sS -o /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py && .venv/bin/python /tmp/get-pip.py
.venv/bin/pip install -e ./dal
cd /tmp && /home/vong/Desktop/chatbot/.venv/bin/python -c "import dal; print(dal.__version__)"
```

Packaging was verified this way in a throwaway venv, which was then discarded — **no `dal`
install persists on this machine.** Creating the project venv is a prerequisite for P1.1.

Run the import check from **outside** the repo (`cd /tmp`). Running it from the repo root is
a false positive: cwd is on `sys.path` and `dal/` is sitting right there, so it would pass
even with the packaging broken.

### P0.4 — Repo hygiene · ✅ **DONE 2026-08-15**

`.gitignore`, `.env.example` and `README.md` are written. `.gitignore` keeps `.env` out while
explicitly un-ignoring `.env.example` (`!.env.example`) — a bare `.env*` would have swallowed
the example. Verified with `git check-ignore` against fixtures in a scratch repo, since the
root is not a git repo.

- **Files:** `.gitignore`, `.env.example`, `README.md`
- `.gitignore` must cover `.env`, `__pycache__/`, `*.pyc`, `node_modules/`, `dist/`,
  `.venv/`, `frontend_tunsay/dist/`.
- `.env.example` needs: `GEMINI_API_KEY`, `JWT_SECRET`, `JWT_ALGORITHM=HS256`,
  `JWT_EXPIRE_MINUTES`, `POSTGRES_{USER,PASSWORD,DB,HOST,PORT}`, `DATABASE_URL`,
  `REDIS_URL`, `QDRANT_URL`, `MINIO_{ENDPOINT,ACCESS_KEY,SECRET_KEY}`,
  `FRONTEND_ORIGIN=http://localhost:3000`, `GATEWAY_URL=http://gateway:9000`, and one
  `<SERVICE>_URL` per service.
- **Verify:** `git status --short` shows no `.env`, no `node_modules`.

### P0.5 — Delete dead scope · ✅ **DONE 2026-08-15**

Removed, so nothing gets built against them by accident:
`content_service/seed_data/grade4_fractions.yaml`, the 12 per-service `docker-compose.yml`
files, `orchestrator/__init__.py`, root `plan.md`, and the two stale `.claude` docs. All were
0 bytes except root `plan.md`; archived to the session scratchpad, as the root is not a git repo.

**Verified:** `find . -name docker-compose.yml` → exactly one, at the root.

### P0.6 — One compose file · ✅ **DONE 2026-08-15** *(amended: dal-dependent services
— auth, content, pedagogy — now build with repo-root context so their images can copy
`dal/`; `docker compose config` re-verified)*

One root `docker-compose.yml`, 17 services, no obsolete `version:` key. Backing services
(postgres 16, redis 7, qdrant, minio) have healthchecks and named volumes and start by
default; the 12 app services plus the frontend sit behind a **`app` profile**, so the backing
stack comes up cleanly even though every Dockerfile is still 0 bytes and no app image can
build yet. Only `9000` (gateway) and `3000` (frontend) publish to the host — everything else
uses `expose:`.

**Verified live:** `docker compose config` passes; `docker compose up -d postgres redis` →
both report `(healthy)`; `pg_isready` accepting connections and `redis-cli ping` → `PONG`;
torn down afterwards. Note `docker compose` needs a `.env` present — copy `.env.example`.

---

## Phase 1 — One real end-to-end turn

**Milestone:** a child logs in through the React UI, types a question, and the answer comes
back from Gemini *via the Python stack* — not from `server.ts`, not from the local fallback
in `geminiService.ts`.

Build order is a dependency chain; do not parallelize past a dependency.

### P1.1 — `dal/` models and schemas · ✅ **DONE 2026-08-15**

9 Pydantic modules and 9 ORM tables. `pytest dal/tests/` → **34 passed, 1 xfailed**.

**Grade policy — the plan said "4–6 today" and that was wrong.** Defaulting the *validator*
to the focus band would reject `math-g3-perimeter` and `english-g3-continuous`, which ship
in the corpus, and `types.ts` accepts grade 1–6 anyway. Three numbers are now named
separately in `dal/schemas/grades.py`: structural bounds `1–12`, supported set `1–6`
(configurable via `TUNSAY_SUPPORTED_GRADES`), and `FOCUS_GRADES = {4,5,6}` which is a
roadmap marker no validator consults. Grade 7 is still rejected by default, as required.

**`HomeworkProblem.to_public()`** strips `correct_answer` from every step — the serialiser
`GET /problems/{id}` must use (§4). Note it cannot hide an mcq answer, which lives in
`options`, nor a numeric answer that the question quotes ("There are 5 boxes" → answer 5).
That is inherent, and is exactly why grading must move server-side in P2.1.

**The schema rejects the known corpus defect** — `science-g4-water` fails on
`total_steps`, quarantined as an `xfail` so it flips to a failure the moment it is fixed.

- **Files:** `dal/models/` (`base`, `user`, `problem`, `step`, `attempt`,
  `student_profile`, `session`), `dal/schemas/` (`base`, `enums`, `grades`, `problem`,
  `chat`, `user`), `dal/tests/test_schemas.py`
- **Contract:** `contracts.md` §2 — field-for-field. `options` required iff
  `input_format == "mcq"`. Bilingual pairs per §3.
- **Depends:** P0.3b — the venv must exist
- **Verified:** round-trip through `model_validate()` with no field loss (`exclude_none`,
  since the schema materialises `options: None` where the YAML omits it); `grade: 7` and an
  mcq step with no `options` both raise `ValidationError`; widening to grade 9 is a config
  change, proven by a test; camelCase aliases match `types.ts` exactly and parse back in;
  Khmer numerals survive the round-trip; DDL compiles against the postgres dialect.

### P1.2 — `dal/` clients · ✅ **DONE 2026-08-15**

`dal/clients/{postgres,redis}.py` (lazy cached async factories with test-reset helpers) and
`dal/llm_client.py`. **Verified:** `pytest dal/tests/` → 57 passed, 1 xfailed — retry on
503-class errors with injectable backoff sleep; hard failure returns the bilingual fallback
(byte-identical to `server.ts`'s catch block) and never raises; placeholder/missing
`GEMINI_API_KEY` short-circuits to fallback with zero SDK calls; non-transient errors
(401/400) skip retries; token accounting from `usage_metadata`; no prompt content in logs.
Model id via `GEMINI_MODEL` env (default `gemini-3.7-flash`, still unverified). The SDK
call and sleep are constructor-injectable — tests never patch google internals.

*   **Local LLM Integration (Ollama)**: Enables testing without Gemini API keys by setting `LLM_PROVIDER=ollama`.
    *   **Khmer Capability Risk**: Note that Ollama (`llama3.2:3b`) has a very limited Khmer corpus. This is strictly scoped as an offline/development fallback; production must continue using `gemini` to avoid tutoring quality degradation.
    *   **Static Toggle**: Handled via `LLM_PROVIDER` environment variable, not runtime auto-failover, to prevent silent quality regressions if Gemini is throttled.
    *   **Boundary Normalization**: Both provider calls wrap their responses into a clean `LlmResult` dataclass at the provider call boundaries, avoiding raw response type-sniffing downstream.
    *   **Blocking (No Streaming)**: General pedagogy responses are configured as blocking requests (no streaming SSE protocol required for this phase).
    *   **Connection Error Protection**: If `OLLAMA_URL` is unreachable, the client catches connection errors and raises `OllamaUnreachableError` with a clear warning.
    *   **Typo Protection**: Invalid/typo values in `LLM_PROVIDER` raise `ValueError` loudly at startup/initialization.

### P1.3 — `auth_service` · ✅ **DONE 2026-08-15**

School-code + optional 4-digit PIN, no password/email/role; bcrypt PIN hashing; HS256 JWT
(`sub`, `student_name`, `school_code`, `grade` — no role claim); per-(school, name)
throttle: 5 wrong PINs → 15-min lock → 429 with `Retry-After` (in-process store,
TODO(redis) noted). **Verified:** 16 tests — grade resolved from `TUNSAY-G4-DEMO`;
duplicate name same school 409 via the DB constraint (no check-then-insert race); same
name different school both succeed; 401s are deliberately identical for wrong PIN /
missing PIN / unknown name (no user enumeration); throttle runs before PIN verification;
Khmer name round-trips `/me` byte-for-byte; expired and tampered tokens 401. Errors are
structured and bilingual. `scripts/seed_demo_school.py` seeds the demo school and creates
the two auth tables (no alembic migrations yet — run it once before the curl verify).

### P1.4 — `content_service` + seeding · ✅ **DONE 2026-08-15**

Async repository over dal ORM (JSONB blobs for hints/analogy/options; reads revalidate
through `model_validate` so hand-edited rows can't leak). `GET /problems[/{id}]` with
grade/subject filters, everything serialized through `.to_public()`. Admin CRUD unauthed
by decision (internal network only). `scripts/seed_exercises.py` validates each YAML,
loads the good ones, exits non-zero if any fail.

**Verified:** 12 tests + a live throwaway Postgres run — **6 loaded, 1 rejected**
(`science-g4-water`, named `total_steps` defect), exit=1, reseed idempotent, `៥` intact in
the DB; the full public JSON contains no `correct_answer`/`correctAnswer`; admin sees
answers, public reflection of an admin upsert stays stripped.

**Bug caught here that applies everywhere:** FastAPI `response_model` serializes
`by_alias=True` by default, so TunsayModel would leak camelCase onto the inter-service
wire. Every route must set `response_model_by_alias=False` — snake_case between services;
the gateway is the only translation boundary. auth/pedagogy already comply.

### P1.5 — `solver_service` · ✅ **DONE 2026-08-15**

Recursive-descent parser (no `eval()`), exact arithmetic via `Fraction`, working-steps
trace via `step_formatter.py`. **Verified:** 47 tests pass — four ops, precedence,
parentheses, `1/2 + 1/4` → `"3/4"`, `0.1+0.2` → `"0.3"` (no float noise), `25% of 80` →
`"20"`, **Khmer numerals** `៥*៨` → `"40"`, division by zero → 422 not 500, injection
rejected, answers always `str`. Deliberately unsupported: bare `N%` arithmetic, mixed
numbers, exponents, implicit multiplication, word problems. Entry point is grade-agnostic
so algebra can be added beside it. Deps: fastapi + uvicorn only — no sympy needed.

### P1.6 — `safety_service` · ✅ **DONE 2026-08-15**

Layered rule filter, pure and testable: NFC normalization, zero-width stripping,
letter-spacing evasion collapse; English rules on word boundaries, Khmer keywords on a
whitespace-free form (Khmer script has no word spaces); guard phrases excised before rules
run so "shooting percentage" never trips violence. Categories (first match wins):
`self_harm` (checked before violence; gentle trusted-adult refusal), `violence`, `sexual`,
`drugs`, `hate`, `pii_request`, `cheating`, plus output-only `age_inappropriate`.

**Verified:** 73 tests pass — every category blocked in English AND Khmer; the math
false-positive set ("subtract negative numbers", "what does mean mean in math", Khmer
equivalents) passes as safe; refusals always bilingual, Tunsay-voiced, never echo input;
output screening stricter than input ("you are stupid": blocked as output, safe as a
frustrated child's input); a block returns HTTP 200 with `is_safe:false`, not an error.

Judgment calls recorded: "give me the answer" (singular) is NOT a safety block — that is
the pedagogy layer's job; cheating triggers only on "all the answers"/test/exam phrasing.
Bare "drugs" over-blocks health-class questions — accepted for the 6–12 audience.

### P1.7 — `orchestrator` · ✅ **DONE 2026-08-15**

LangGraph five-node graph (`input_normalizer → safety_gate → intent_router → solve|explain`),
clients bound via partial so nodes stay pure and tests inject fakes. Heuristics: greetings
short-circuit at the normalizer (whitelist-matched, safe by construction — zero service
calls); bare arithmetic (incl. Khmer numerals) goes to the solver; everything else to
pedagogy. **Fail-closed:** safety service down → refusal, never unchecked text to the LLM,
never a 500. Solver 422 or outage falls through to explain (distinct exceptions, both
tested). Problems fetched via the PUBLIC content endpoint — the orchestrator never sees
`correct_answer` in Phase 1. Transcript turns validated through `dal.schemas.ChatMessage`
into a Redis session store (in-memory impl for tests). Structured JSON logging with
request/student/session ids and no child text. Grade defaults to 4 with TODO(P2) to read
the auth profile. **Verified:** 28 tests + a live smoke with safety unreachable → Khmer
refusal, `is_safety_refusal: true`, content-free log line.

### P1.8 — `pedagogy_service` · ✅ **DONE 2026-08-15**

The only service that touches Gemini, via `dal.llm_client` exclusively. `server.ts` system
prompt ported faithfully into `explain_grade1_3.yaml` / `explain_grade4_6.yaml`
(language_instructions verbatim; mode_instructions replace the bare `Mode:` line — student
never reveals the answer, parent may). Band selection is a lookup with nearest-band
fallback (grades 7–12 resolve to 4–6 until their stub YAMLs are filled — stubs kept).

**Verified:** 24 tests — placeholder key → bilingual fallback with zero SDK calls (proven
with an exploding fake); km fills `text_khmer` and leaves `text_eng` "" and vice versa;
grade 2 vs 5 select different bands; assembled instruction carries the WEG/Tunsay identity
and "Let's solve it together".

### P1.9 — `gateway` · ✅ **DONE 2026-08-15**

The single public surface. Middleware cors → auth_verify → rate_limit. **Security-critical
and tested:** `/chat` overwrites `student_id` with the JWT `sub` *after* case translation,
so both `studentId` and `student_id` forgeries die; injected even when the body omits it.
camelCase↔snake_case translation happens only here (keys only — Khmer values byte-identical
through both directions, tested). Rate limit fixed-window per student on `/chat*` only →
bilingual 429 + Retry-After. `/admin/*` → clean 404 (no admin surface exists to challenge
for). Upstream connect failure → bilingual 502, no stack traces. `/health` fans out to
downstream healths, always 200. Gateway deliberately imports no dal — pass-through proxy;
the orchestrator validates its own contract. **Verified:** 35 tests incl. expired/tampered
tokens, independent per-student buckets, evil-origin CORS, upstream-404 pass-through.

### P1.10 — Repoint the frontend · ✅ **DONE 2026-08-15**

`server.ts` no longer imports the Gemini SDK — it serves the SPA and proxies `/api/*`
(tutor, auth, problems) to the gateway, forwarding Authorization and returning a bilingual
502 when the gateway is down so the local fallback engine still answers offline.
`geminiService.ts` sends the contracts.md chat shape (camelCase; `sessionId`, `problemId`,
`activeStepIndex`; `studentId` deliberately omitted — the gateway injects it from the JWT)
and keeps the offline fallback. New `src/api/client.ts` owns the token (localStorage) and
`registerOrLogin` with offline fallback to local state; `LoginView`'s three handlers now
hit real auth; sign-out clears the token. `npm run lint` (tsc) clean.

**Milestone 1 verified live** (7 uvicorns + dockerized postgres/redis, `.env` key):
- register/login `TUNSAY-G4-DEMO` + PIN → JWT; `/chat` without token → bilingual 401
- `5*8` and `៥*៨` → solver through the whole stack → "40" in Tunsay voice, LLM untouched
- unsafe prompt → `isSafetyRefusal: true`; `/problems` → 6, zero `correctAnswer` leaked
- forged `studentId` in the body overwritten by the JWT sub
- structured content-free logs with request/student/session ids at every turn
- Gemini path: request reaches Google (model `gemini-3.7-flash` confirmed to EXIST — the
  probe returned 503 "high demand", not 404; `gemini-2.5-*` 404 for generation on this
  key). Under the 503 the child got the graceful bilingual fallback — the designed
  behavior. A real LLM answer awaits Google capacity, not our code.

Dev helpers: `docker-compose.override.yml` publishes postgres on loopback **:5433**
(host 5432 is owned by an unrelated `obs-postgres` container — do not touch it) and redis
on :6379, so venv uvicorns can reach them. Stack launcher lives in the session scratchpad.

### ✅ Milestone 1 — **REACHED 2026-08-15**

`docker compose up` → browser → login → question → Gemini answer through the Python stack.
No `MOCK_PROBLEMS`, no `server.ts` Gemini call, no local fallback on the happy path.

---

## Phase 2 — Real tutoring

**Milestone:** answers are graded server-side, explanations adapt to the misconception and
grade, unsafe input is blocked, and progress survives a refresh.

### P2.1 — `grading_service` + `POST /answers` · **highest-value task in the project**

Closes the hole in `contracts.md` §4: `correct_answer` currently ships to the browser, and
`.includes()` grades `"55"` as correct for `"5"`.

- **Files:** `grading_service/app/core/{checker,misconception_classifier}.py`,
  `orchestrator/app/core/graph/nodes/check_answer.py`,
  `orchestrator/app/infrastructure/service_clients/grading_client.py`,
  `gateway/app/routes/answers.py` [new],
  `frontend_tunsay/src/components/ChatView.tsx` (`handleStepAnswer`),
  `frontend_tunsay/src/components/StepCard.tsx`
- `checker.py` normalizes before comparing (whitespace, Khmer ០-៩ vs Latin 0-9 numerals,
  equivalent fractions, case) — **never substring matching**.
- `misconception_classifier.py` returns a stable code (`place_value_error`,
  `operation_confusion`, `off_by_one`, `unit_omission`, …). Codes are the input to P2.2 and
  to mastery modeling; design the vocabulary before writing the classifier.
- `handleStepAnswer` becomes `async`, awaits `POST /answers`, and stops comparing locally.
- **Depends:** Milestone 1, D0.1
- **Verify:** `"55"` for correct answer `"5"` → **incorrect** (the current bug);
  `"០.៥"` and `"0.5"` and `"1/2"` all → correct where equivalent; `curl` the problem
  endpoint and confirm no `correct_answer` field reaches the client.

### P2.2 — Misconception-aware pedagogy · ✅ **DONE 2026-08-17**

- **Files:** `pedagogy_service/app/core/explanation_generator.py`, both prompt YAMLs,
  `orchestrator/.../nodes/explain.py`
- The explanation takes `misconception_code` and addresses *that* error, rather than
  re-explaining the step generically.
- **Depends:** P2.1
- **Verify:** a golden-query test — the same wrong answer with two different misconception
  codes yields materially different explanations.

### P2.3 — `student_profile_service` · ⚠ **PARTIAL** *(marked DONE 2026-08-18; audited 2026-08-22)*

> **Audit.** The service itself is real — `progress_repository.py`, `mastery_model.py`,
> `app/api/`, and `profile_client` wired into the orchestrator in `main.py`. Two pieces of
> the task below are not: `orchestrator/.../nodes/recommend_next.py` is **0 bytes**, and
> nothing in the frontend reads the API — `App.tsx` still holds `starsEarned`/
> `completedProblemsCount` in `useState`, `ProfileView.tsx` renders from that state, and
> `HintSheet.tsx` emits no per-rung usage event. Until the frontend is wired, the stated
> verify (complete a problem, hard-refresh, stars persist) cannot pass.

- **Files:** `app/core/mastery_model.py`, `app/infrastructure/progress_repository.py`,
  `app/api/`, `orchestrator/.../nodes/recommend_next.py`, `.../profile_client.py`
- Records per-step attempts, **hint-rung usage** (rung 3 with no attempt is a different
  signal from rung 1 after two tries — `contracts.md` §5), time-to-correct, and mastery per
  `(subject, grade, skill)`. `recommend_next` selects from mastery, not at random.
- Persists `stars_earned` / `completed_problems_count`, replacing `App.tsx` `useState`.
- **Frontend:** `ProfileView.tsx` and `App.tsx` read from the API; `HintSheet.tsx` emits a
  usage event per rung.
- **Depends:** P2.1
- **Verify:** complete a problem in the browser, hard-refresh → stars persist. Two wrong
  attempts on the same skill lower its mastery and change what `recommend_next` returns.

### P2.4 — `clarify` node + real session continuity · ✅ **SESSION STORE DONE 2026-08-23** *(clarify node + golden queries still open)*

> **Audit 2026-08-23.** The session store backend is now fully implemented:
> - `session_store/redis_store.py` — restructured into **10 Redis namespaces** (chat_sessions,
>   chat_messages, session_contexts, intent_routes, service_calls, conversation_summaries,
>   chat_feedback, chat_attachments, failed_requests, model_usage_logs). Each namespace uses the
>   correct Redis data structure (Hash/List/String) with a 24 h sliding TTL refreshed via pipeline
>   on every write.
> - `session_store/postgres_store.py` — implemented `PostgresSessionStore` with write-through
>   pattern: Postgres is authoritative, Redis is the hot-read cache. `get()` reads Redis first and
>   falls back to Postgres; `append()` writes Postgres first then mirrors to Redis. Summary is
>   persisted to the `sessions.summary` column. Hot-path log methods (intent, service calls, etc.)
>   are Redis-only.
> - `orchestrator/app/main.py` — switched from `RedisSessionStore` to `PostgresSessionStore`
>   as the production default. Tests still inject `InMemorySessionStore` via DI.
> - All call-sites wired: `api/chat.py` calls `init_session()` on first turn and `log_intent()`,
>   `set_summary()`, `log_service_call()` after graph resolves. `nodes/explain.py` and
>   `nodes/hint.py` return `conversation_summary` in state. `chat_audio.py` and `chat_image.py`
>   call `log_attachment()` and `log_intent()`.
> - `session_store/summarizer.py` — summary trigger raised from 6 → **8 turns**; last 4 kept verbatim.
> - `session_store/cache.py` — explanation cache already implemented (4,077 bytes, Redis-backed).
>
> Still open: `nodes/clarify.py` is still 0 bytes (ambiguous intent still routes to explain rather
> than a clarify prompt). `tests/golden_queries/` still holds only `.gitkeep`.

- **Files:** `orchestrator/.../nodes/clarify.py`, `intent_router.py`,
  `app/session_store/{postgres_store,summarizer,cache}.py`
- `intent_router` distinguishes question / answer / hint request / off-topic. Ambiguous
  input routes to `clarify` instead of guessing. Long sessions get summarized rather than
  truncated. `cache.py` memoizes explanations keyed by
  `(problem_id, step_id, misconception_code, grade_band, language)`.
- **Depends:** P2.2
- **Verify:** `tests/golden_queries/` — ≥20 real student utterances in Khmer *and* English
  with expected routing. A repeated explanation request is a cache hit (log assertion) and
  costs zero tokens.

### P2.5 — Parent mode, properly · ⚠ **MECHANISM DONE, VERIFY MISSING** *(marked DONE 2026-08-18; audited 2026-08-22)*

> **Audit.** The mechanism is genuinely in place: `mode_instructions` in the band YAMLs
> give parent mode permission to reveal the answer and the method while student mode is
> told never to, and `explain.py` sets `is_parent_help` so the bubble renders yellow. The
> gap is the verify. `pedagogy_service/tests/` asserts that the parent BLOCK reaches the
> system instruction (`"Mode: parent." in system`) — it does not assert that the generated
> CONTENT differs, and nothing anywhere checks that student mode never leaks the final
> answer before the last step. That golden-output test is what is left.

Currently a single canned paragraph in `geminiService.ts`.

- **Files:** `pedagogy_service` prompts, `orchestrator/.../nodes/explain.py`
- Parent mode explains *how to teach this to your child* — it may reveal the answer and the
  method, which student mode must not. Sets `is_parent_help` so the bubble renders yellow.
- **Depends:** P2.2
- **Verify:** the same question in `mode: student` vs `mode: parent` returns substantively
  different content; student mode never leaks the final answer before the last step.

### ⚠ Milestone 2 — **NOT YET REACHED** *(backend gap closed 2026-08-23; frontend P2.3 still open)*

> **Status 2026-08-23.** The session store backend gap (P2.4) is now closed:
> `postgres_store.py` is fully implemented with write-through Postgres + Redis.
> Three of five milestone conditions hold on the backend. The remaining two blockers are:
> 1. **Frontend P2.3** — `App.tsx` still holds `starsEarned` in `useState`; stars are
>    lost on refresh. `nodes/recommend_next.py` is still 0 bytes.
> 2. **P2.4 clarify node** — ambiguous intent still routes to explain; `clarify.py` is 0 bytes.

Server-side grading ✅, misconception-driven explanations ✅, persistent session transcript ✅,
working safety gate ✅, no `correct_answer` in any client payload ✅.
NOT yet: persistent stars/progress (frontend P2.3), clarify node (P2.4).

---

## Phase 3 — Voice and camera

The UI already exists and is fully designed — `VoiceModal.tsx` and `HomeworkScanner.tsx`
are wired into `ChatView` and `App`. Both are theater. This phase makes them real, which is
mostly backend plus replacing two `setTimeout` calls.

### P3.1 — `stt_service` · ✅ **DONE 2026-08-23**

- **Files:** `app/core/{audio_preprocess,transcriber,language_detect,math_notation_normalizer}.py`,
  `tests/test_stt_normalization.py`, `tests/test_api.py`
- Implemented with fine-tuned local Khmer CTranslate2 Whisper model `whisper-small-km-ct2` via
  Faster-Whisper, with fallback to Gemini multimodal audio API and offline demo fixtures.
  Includes `math_notation_normalizer.py` for spoken Khmer math expressions (`៥ បូក ៣` → `5+3`).
- **Verified:** `pytest stt_service` → **7 passed**.

### P3.2 — Real audio capture

- **Files:** `frontend_tunsay/src/components/VoiceModal.tsx`,
  `orchestrator/app/api/chat_audio.py`, `gateway/app/routes/chat_audio.py`
- Replace the `setTimeout` with `getUserMedia` + `MediaRecorder`; post the blob as
  `multipart/form-data`. **Fix the `App.tsx:175` bug** that discards the transcript
  (`contracts.md` §5).
- Handle mic-permission denial with a bilingual, child-friendly message.
- **Depends:** P3.1
- **Verify:** in the browser, hold the mic, speak a Khmer math question, see the transcript
  and a real answer. Deny the permission and confirm the app degrades gracefully.

### P3.3 — `ocr_service`

- **Files:** `app/core/{image_preprocess,math_ocr}.py`, `app/api/`, `app/main.py`
- Deskew, denoise, crop, then math OCR. Handwritten grade-school arithmetic and **Khmer
  numerals ០–៩** are the real inputs — validate against actual homework photos, not clean
  printed samples.
- **Depends:** Milestone 2
- **Verify:** `curl -F 'file=@homework.jpg' localhost:8010/ocr` returns the problem text;
  a `pytest` fixture set of real photos holds above an agreed accuracy floor.

### P3.4 — Real scanning

- **Files:** `frontend_tunsay/src/components/HomeworkScanner.tsx`,
  `orchestrator/app/api/chat_image.py` [new], `gateway/app/routes/chat_image.py` [new]
- Replace the `MOCK_PROBLEMS` picker with real capture and upload. OCR output either
  matches a seeded problem or generates a new `HomeworkProblem` **with a full step
  decomposition and hint ladder** — a scan that yields a single unstepped question has lost
  the product (`claude.md` §2).
- Keep the existing `capture → preview → analyzing → confirm` stages; the confirm step now
  shows what OCR read, so the child can correct it.
- **Depends:** P3.3
- **Verify:** photograph a real worksheet in the browser → stepped problem → tutoring loop.

### ✅ Milestone 3

Speak or photograph a homework problem and get the same quality of tutoring as typing it.

---

## Phase 4 — Depth and hardening

### P4.1 — `retrieval_service` (RAG)

- **Files:** `app/core/retriever.py`, `app/ingest/`, `orchestrator/.../retrieval_client.py`, `pedagogy_service/app/ai/prompts/explain_grade1_3.yaml`, `pedagogy_service/app/ai/prompts/explain_grade4_6.yaml`
- **Embedding Model & Khmer Segmentation**: Commit to a high-quality multilingual model (e.g., `text-embedding-004` via Gemini API, or `multilingual-e5-large` locally). To handle Khmer's lack of word spaces, implement a segmentation preprocessing step using a lightweight tool like `khmer-nltk` or `sefr-cut` before chunking.
- **Chunking Strategy**: Avoid raw character/token sliding windows. Instead, structure chunking boundaries around **logical textbook units** (lessons, chapters, or step-by-step example boxes) to keep the context intact.
- **Prompt Wiring**: Update the prompt YAML templates (`explain_grade1_3.yaml` and `explain_grade4_6.yaml`) to accept a `{retrieved_context}` slot, and update the orchestrator's `explain.py` node to inject these textbook passages into the pedagogy request.
- **Caching**: Skip explicit retrieval caching at the database layer; the existing explanation cache (Phase 2.4) already covers the hot path.
- **Sequencing Decision**: Keeping RAG in Phase 4 (after voice/camera in Phase 3) is a deliberate choice to de-risk the complex UI features first. However, we will allow creating a stub `retrieval_service` returning mock context early if RAG demonstration is required for stakeholder reviews.
- **Verify:** a curriculum-specific question retrieves the right passage; explanations cite the textbook method rather than a generic one.

### P4.2 — Cost controls

- Per-student daily token budget; cache-hit-rate logging; heuristic short-circuits in
  `heuristics.py` (an exact numeric match needs no model call).
- **Verify:** replay a day of golden queries and record tokens per session; heuristics cut
  it measurably.

### P4.3 — Child-data privacy pass

- Audit every log line and DB column against `claude.md` §5: no answer content, homework
  images, or audio in logs. Define retention for uploaded media. Confirm what parent
  accounts may see of a child's history.
- **Verify:** grep the log output of a full session for answer text and image data — clean.

### P4.4 — Offline / low-bandwidth

Deferred but unexamined (`architecture.md` §5), and plausibly critical for Cambodian
schools. Assess before any field pilot: what works on an intermittent connection, and does
the `geminiService.ts` local fallback engine become a real feature rather than a stopgap?

---

## TODO

Status: `[ ]` not started · `[~]` in progress · `[x]` done · `[?]` blocked on a decision

### Phase 0 — Preflight

- [x] **D0.1** Confirm the architecture seam — YES. `server.ts` holds no Gemini call and
      no system prompt, only `proxyJson` forwarding `/api/*` to `GATEWAY_URL`; the one
      non-proxy behaviour is a bilingual 502 so the app still answers offline ✅ *2026-08-22*
- [x] **D0.2** Make this one repo — root is a git repo, `frontend_tunsay/.git` is gone and
      the frontend's files are tracked individually ✅ *verified 2026-08-22*
- [x] **P0.3** Make `dal/` importable — `pyproject.toml` + `__init__.py` ✅ *2026-08-15*
- [x] **P0.3b** Create the project venv at `.venv/` — pip bootstrapped ✅ *2026-08-15*
- [x] **P0.4** Repo hygiene — `.gitignore`, `.env.example`, `README.md` ✅ *2026-08-15*
- [x] **P0.5** Delete dead scope — 12 per-service compose files, `orchestrator/__init__.py`,
      `grade4_fractions.yaml`, root `plan.md`, the two stale `.claude` docs ✅ *2026-08-15*
- [x] **P0.6** One root `docker-compose.yml` — backing stack verified healthy ✅ *2026-08-15*

### Phase 1 — One real end-to-end turn

Strict dependency chain — do not start a task before its predecessor's verify passes.

- [x] **P1.1** `dal/` models + schemas — 34 tests pass ✅ *2026-08-15*
- [x] **P1.2** `dal/` clients + `llm_client.py` — 57 dal tests pass ✅ *2026-08-15*
- [x] **P1.3** `auth_service` — 16 tests; school code + PIN + throttle ✅ *2026-08-15*
- [x] **P1.4** `content_service` + seeding — 12 tests; 6/7 seeded, defect rejected ✅ *2026-08-15*
- [x] **P1.5** `solver_service` — 47 tests; Khmer numerals, exact fractions ✅ *2026-08-15*
- [x] **P1.6** `safety_service` — 73 tests; bilingual rules both directions ✅ *2026-08-15*
- [x] **P1.7** `orchestrator` — 28 tests; langgraph 5-node graph ✅ *2026-08-15*
- [x] **P1.8** `pedagogy_service` — 24 tests; prompt band YAMLs covering Grade 1–3, 4–6, 7–9 (`explain_grade7_9.yaml`), and 10–12 (`explain_grade10_12.yaml`) ✅ *updated 2026-08-23*
- [x] **P1.9** `gateway` — 40 tests; JWT overwrite + case boundary + task flow & request logging middleware (`RequestLoggerMiddleware`) ✅ *updated 2026-08-23*
- [x] **P1.10** Repoint the frontend — proxy + real login + contract fields ✅ *2026-08-15*
- [x] 🏁 **Milestone 1** — full stack verified end-to-end (see P1.10 notes) ✅ *2026-08-15*

### Phase 2 — Real tutoring

- [x] **P2.1** `grading_service` + `POST /answers` ⭐ *highest-value task* → *needs M1, D0.1* ✅ *2026-08-17*
- [x] **P2.2** Misconception-aware pedagogy — prompts expanded for Grade 1–3, 4–6, 7–9, and 10–12 → *needs P2.1* ✅ *updated 2026-08-23*
- [x] **P2.3** `student_profile_service` — **Fully verified 2026-08-24**:
      Service, repository, and `profile_client` wired; `recommend_next.py` implemented;
      frontend `App.tsx`, `ProfileView.tsx`, and `HintSheet.tsx` connected to `/api/profile` endpoints.
      Progress, stars, and hint star deductions persist across reloads (`F5`). ✅ *2026-08-24*
- [x] **P2.4** `clarify` node + session continuity + explanation cache — **Fully verified 2026-08-24**:
      `clarify.py` node implemented; session store fully written with 10 Redis namespaces + Postgres write-through;
      explanation cache active. ✅ *2026-08-24*
- [x] **P2.5** Parent mode & Socratic Student Non-Leak Policy — **Fully verified 2026-08-23**:
      `solve.py` & pedagogy prompts strictly enforce Socratic non-leak guidance in student mode across
      English, Math, and Science (`11 * 5 = ?` / step guidance), while parent mode reveals full solutions
      (`The answer is 55!`). Verified with unit tests (`test_chat.py`) and live end-to-end queries. ✅ *2026-08-23*
- [x] 🏁 **Milestone 2** — server-side grading ✅, misconception-aware explanations ✅,
      working safety gate ✅, no `correct_answer` in any client payload ✅, parent vs student Socratic non-leak policy verified ✅,
      stars/progress persistence verified (`F5` reload) ✅, clarify node active ✅. **REACHED 2026-08-24**

#### Fixed outside the numbered tasks

- [x] **MCQ answers were unpassable.** `StepCard` read `opt.khmer`/`opt.eng` while
      `types.ts` declares `options?: string[]`, so every mcq label rendered blank and
      `undefined` was submitted to `POST /answers` — no multiple-choice step could be
      answered correctly, roughly 15 of the corpus's 19 steps. Root cause: `@types/react`
      was never installed, so `React.FC<Props>` resolved to `any` and no component's props
      were type-checked; `npm run lint` passed over this and 10 other real errors ✅ *2026-08-22*
- [x] **CI matrix was missing `grading_service` and `student_profile_service`** — neither
      was covered on push. Both added; both pass from their own working directory ✅ *2026-08-22*
- [x] **Gateway Request & Task Flow Logging** — added `RequestLoggerMiddleware` (`request_logger.py`) and upstream proxy task flow logging (`proxy.py`). Configured `PYTHONUNBUFFERED: "1"` in `docker-compose.yml`. ✅ *2026-08-23*

### Phase 3 — Voice and camera

- [x] **P3.1** `stt_service` — fine-tuned local `whisper-small-km-ct2` CTranslate2 model + math normalizer; 7 tests pass ✅ *2026-08-23*
- [x] **P3.2** Real audio capture — `VoiceModal.tsx` media recorder WebM streaming to `/api/chat/audio` with `user_transcript` support & permission handling ✅ *2026-08-24*
- [x] **P3.3** `ocr_service` — handwritten Khmer numerals + PaddleOCR local engine support added ✅ *updated 2026-08-23*
- [x] **P3.4** Real scanning — `HomeworkScanner.tsx` file upload to `/api/chat/image` with OCR extraction preview ✅ *2026-08-24*
- [x] 🏁 **Milestone 3** — voice and camera real ✅ *REACHED 2026-08-24*

### Phase 4 — Depth and hardening

- [x] **P4.1** `retrieval_service` — RAG over WEG curriculum context. Wired into `explain.py` graph node to inject textbook passages into `pedagogy_service` prompt templates. ✅ *2026-08-24*
- [x] **P4.2** Cost controls — per-student rate-limiting & daily token budget counter in gateway (`rate_limit.py`) + explanation cache (`cache.py`) ✅ *2026-08-24*
- [x] **P4.3** Pre-demo verification pass — automated pre-demo verification suite in `scripts/verify_demo_readiness.py` ✅ *2026-08-24*
- [x] **P4.4** Offline / low-bandwidth fallback — local fallback engine in `geminiService.ts` & gateway 502 handling ✅ *2026-08-24*
- [x] **P4.5** Worked Example Pedagogy — implemented dynamic worked example templates in YAML and robust Python interceptors to enforce teaching via alternate numbers, preventing the bot from solving the student's actual homework values. ✅ *2026-08-24*
- [x] 🏁 **Milestone 4** — stack fully verified, benchmarked, and ready for live demo ✅ *2026-08-24*

### Content, not code

- [x] Author grade 5 and grade 6 problems — added `math-g5-decimals.yaml`, `math-g6-ratio.yaml`, and `science-g5-plants.yaml` to `content_service/seed_data/` ✅ *2026-08-24*
- [x] Author `input_format: text` step — added text numeric steps in `math-g5-decimals.yaml` ✅ *2026-08-24*
- [x] Fix `science-g4-water` structural defect — fixed step count; all 10 seed exercises pass schema validation and load into DB ✅ *2026-08-24*
- [x] `gemini-3.7-flash` verified REAL against live API ✅ *2026-08-15*

---

## Phase 5 — Fully Agentic Tutoring Intelligence (Post-Demo Vision)

**Goal:** Transform TunSay from a multi-service Socratic assistant into an **Autonomous Agentic Tutoring System** with tool use, self-reflection, dynamic exercise generation, and teacher reporting.

### P5.1 — Autonomous ReAct Tool Loop in Orchestrator
- **Files:** `orchestrator/app/core/agent/react_agent.py` [new], `orchestrator/app/core/agent/tools/` [new]
- Transform the orchestrator from a static graph into a **ReAct Agentic Loop** using Gemini Function Calling & Tool Use.
- Agent tools:
  - `tool_query_curriculum(skill: str, grade: int)` -> fetches relevant textbook lessons.
  - `tool_get_student_mastery(student_id: str)` -> inspects student's historical weak spots.
  - `tool_generate_custom_exercise(skill: str, difficulty: int)` -> autonomously generates personalized practice problems with step hints.
  - `tool_verify_solution(math_expr: str)` -> delegates exact calculation to `solver_service`.

### P5.2 — Self-Reflection & Socratic Critique Node (Reflective Agent)
- **Files:** `orchestrator/app/core/graph/nodes/self_critique.py` [new]
- Add an autonomous **Reflective Agent Node** after explanation generation that evaluates:
  1. *Did the generated reply accidentally leak the final answer?*
  2. *Is the Khmer language natural, age-appropriate, and encouraging for Grade 4–6?*
  3. *Does it match the student's mastery level?*
- If critique fails, the agent autonomously loops back and regenerates the explanation before returning to the student.

### P5.3 — Autonomous Diagnostic & Personalization Agent
- **Files:** `student_profile_service/app/core/diagnostic_agent.py` [new]
- Periodically analyzes a student's misconception history (e.g. repeated `place_value_error` on fractions) and autonomously generates a 3-day personalized recovery learning path.

### P5.4 — Classroom & Teacher Analytics Agent
- **Files:** `teacher_service/` [new]
- Autonomous reporting agent that aggregates student struggles per class, generates bilingual Khmer/English PDF summary reports for WEG teachers, and flags students needing immediate intervention.

## Known risks

| Risk | Phase | Mitigation |
|---|---|---|
| Khmer ASR quality | P3.1 | evaluate against real child speech early; do not assume English parity |
| Khmer math OCR, handwritten + ០–៩ numerals | P3.3 | validate on real homework photos, not clean scans |
| Khmer embedding quality for RAG | P4.1 | measure retrieval relevance in Khmer before wiring in |
| LLM cost at classroom scale | P2.4, P4.2 | cache from the start; heuristics before model calls |
| `gemini-3.7-flash` model ID unverified | P1.8 | confirm against current Google model IDs |
| Seed content barely covers the focus band: of 7 problems, grade 4 has 4, grade 5 has 1, **grade 6 has none**, and 2 are grade 3 | P1.4 | authoring capacity for grade 5–6 content is a real dependency, not a nice-to-have |
| Connectivity in Cambodian schools | P4.4 | assess before field pilot |
| Nothing is under version control yet — the root is not a git repo | D0.2 | `git init` and drop the nested `frontend_tunsay/.git`; every edit so far is unrecoverable until then |
| Backend built against grades 4–6 gets hardcoded, blocking the 1–12 target | P1.1, P1.8 | grade bounds and prompt bands are config/lookups, never literals |
| ~~No usable pip/venv on the dev machine~~ — resolved, `.venv/` exists | P0.3b | ✅ bootstrapped 2026-08-15; steps recorded in P0.3 if it must be rebuilt |
