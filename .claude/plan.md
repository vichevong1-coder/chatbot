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

### D0.1 — Confirm the architecture seam · **DECISION, BLOCKING FOR PHASE 2**

`claude.md` §3 assumes the Python backend is the target and `server.ts` becomes a proxy.
Phase 1 is worth doing under either reading, but Phase 2 branches. Confirm before P2.1.

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
  `FRONTEND_ORIGIN=http://localhost:3000`, `GATEWAY_URL=http://gateway:8000`, and one
  `<SERVICE>_URL` per service.
- **Verify:** `git status --short` shows no `.env`, no `node_modules`.

### P0.5 — Delete dead scope · ✅ **DONE 2026-08-15**

Removed, so nothing gets built against them by accident:
`content_service/seed_data/grade4_fractions.yaml`, the 12 per-service `docker-compose.yml`
files, `orchestrator/__init__.py`, root `plan.md`, and the two stale `.claude` docs. All were
0 bytes except root `plan.md`; archived to the session scratchpad, as the root is not a git repo.

**Verified:** `find . -name docker-compose.yml` → exactly one, at the root.

### P0.6 — One compose file · ✅ **DONE 2026-08-15**

One root `docker-compose.yml`, 17 services, no obsolete `version:` key. Backing services
(postgres 16, redis 7, qdrant, minio) have healthchecks and named volumes and start by
default; the 12 app services plus the frontend sit behind a **`app` profile**, so the backing
stack comes up cleanly even though every Dockerfile is still 0 bytes and no app image can
build yet. Only `8000` (gateway) and `3000` (frontend) publish to the host — everything else
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

### P1.3 — `auth_service`

- **Files:** `app/core/{password_hashing,jwt_handler}.py`, `app/api/{register,login,me}.py`,
  `app/infrastructure/repository.py`, `app/main.py`, `alembic/`
- **Read `contracts.md` §4 "Auth credentials" first.** There is **no password and no email** —
  `LoginView.tsx` collects a school code, a Khmer display name, and an optional 4-digit PIN
  across three flows. Building an email/password service here means rewriting it and the
  login UI later. `password_hashing.py` hashes PINs; the filename is inherited, not a spec.
- Resolve the school-code/class scope question in §4 before writing the schema.
- **One role: student.** No `role` column, no account types, no `parent_student_link`
  table — the frontend has no account-type picker (`contracts.md` §4). `UserMode` is a
  separate concept and stays: it is an in-app student/parent toggle, not an identity.
- Admin is **not** gateway-routed and needs no auth path here (`contracts.md` §4).
- Rate-limit auth attempts: a 4-digit PIN has 10,000 combinations.
- **Contract:** `contracts.md` §4
- **Depends:** P1.1, P0.6
- **Verify:**
  ```bash
  docker compose up -d auth_service
  # school-code flow, mirroring LoginView's demo values
  curl -sX POST localhost:8002/register -H 'Content-Type: application/json' \
    -d '{"student_name":"សុជា (Sochea)","school_code":"TUNSAY-G4-DEMO","pin":"1234"}'
  curl -sX POST localhost:8002/login -H 'Content-Type: application/json' \
    -d '{"student_name":"សុជា (Sochea)","school_code":"TUNSAY-G4-DEMO","pin":"1234"}' | tee /tmp/tok.json
  curl -s localhost:8002/me -H "Authorization: Bearer $(jq -r .access_token /tmp/tok.json)"
  ```
  Round-trips; `/me` returns grade 4 resolved from the school code; the Khmer name survives
  unmangled. Two students with the same name under different school codes both work. A wrong
  PIN fails, and repeated wrong PINs get throttled.

### P1.4 — `content_service` + seeding

- **Files:** `scripts/seed_exercises.py`, `seed_data/*.yaml`, `app/api/admin.py`,
  `app/api/problems.py` [new], `app/infrastructure/repository.py`, `app/core/models.py`
- `app/api/admin.py` stays **internal-network only** — no gateway route, no public
  exposure (`contracts.md` §4). `expose:` in compose, never `ports:`.
- ✅ **The YAML transcode is done** — `seed_data/*.yaml`, 7 files, 18 steps, snake_case,
  Khmer preserved byte-for-byte (verified bidirectionally against the `.ts` source).
  **`scripts/seed_exercises.py` is still to write** — the seed data currently has no loader.
- Ingest validation must reject: a missing Khmer *or* English authored field (§3), and
  **`total_steps != len(steps)`** — see the known defect in `contracts.md` §6.
- `GET /problems/{id}` **must strip `correct_answer`** from every step.
- **Depends:** P1.1
- **Verify:**
  ```bash
  docker compose run --rm content_service python scripts/seed_exercises.py
  curl -s localhost:8003/problems | jq 'length'                        # 7
  curl -s localhost:8003/problems/math-g4-apples | jq '.steps[0]'      # no correct_answer
  curl -s localhost:8003/problems/math-g4-apples | jq -r '.title_khmer' # Khmer renders
  ```

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

### P1.7 — `orchestrator`: minimal graph

- **Files:** `app/core/graph/state.py`, `builder.py`, `edges.py`,
  `nodes/{input_normalizer,safety_gate,intent_router,solve,explain}.py`,
  `app/infrastructure/service_clients/{auth,content,solver,safety,pedagogy}_client.py`,
  `app/session_store/redis_store.py`, `app/utils/logging.py`, `app/api/chat.py`, `app/main.py`
- Only five nodes this phase — `clarify`, `check_answer`, and `recommend_next` come in
  Phase 2. `state.py` is auth-aware from the first commit (`student_id`, `session_id`,
  `language`, `mode`, `problem_id`, `active_step_index`) — `mode` is the student/parent
  toggle, and there is no `role`, since every account is a student.
- Write `utils/logging.py` **now**, before the first cross-service debugging session.
- **Contract:** `contracts.md` §4 `POST /chat`
- **Depends:** P1.2, P1.4, P1.5, P1.6
- **Verify:**
  ```bash
  curl -sX POST localhost:8001/chat -H 'Content-Type: application/json' \
    -d '{"session_id":"t1","student_id":"s1","prompt":"why do I multiply?",
         "mode":"student","language":"km","problem_id":"math-g4-apples","active_step_index":0}'
  ```
  → `text_khmer` populated, `text_eng: ""`, `is_safety_refusal: false`. Re-posting the same
  `session_id` shows the prior turn in Redis.

### P1.8 — `pedagogy_service` owns the Gemini call

The system prompt moves out of `server.ts`. Port it verbatim first — it encodes the product
voice (friendly rabbit, Cambodia/WEG context, never give the answer immediately, "Let's
solve it together", never judgmental) — then split by grade band.

- **Files:** `app/core/explanation_generator.py`,
  `app/ai/prompts/explain_grade4_6.yaml` (build first), `explain_grade1_3.yaml`,
  `app/api/`, `app/main.py`
- Band selection is a lookup, not an `if` chain — grades 7–9 and 10–12 already have prompt
  files reserved and will be filled in later (`claude.md` §4). Grade and language are prompt
  inputs, not string concatenation at the call site.
- **Depends:** P1.2
- **Verify:** with `GEMINI_API_KEY` unset the service still returns the bilingual fallback
  (matching `server.ts`'s current no-key behavior); with a key set, a grade-4 and a grade-6
  request produce visibly different reading levels, and an unmapped grade falls back to the
  nearest band instead of erroring.

### P1.9 — `gateway`

- **Files:** `app/middleware/{cors,auth_verify,rate_limit}.py`,
  `app/routes/{auth,chat}.py`, `app/routes/problems.py` [new], `app/main.py`
- **No `admin.py`** — content editing does not pass through the gateway (`contracts.md` §4).
  The empty stub has been deleted; do not recreate it.
- Middleware order `cors → auth_verify → rate_limit`. CORS allows `FRONTEND_ORIGIN` only.
  Rate limit per `student_id` on `/chat*` only. **`auth_verify` injects `student_id` from
  the JWT** — the gateway must overwrite any client-supplied `student_id` in the body,
  or a child can impersonate a classmate.
- **Contract:** `contracts.md` §4
- **Depends:** P1.3, P1.7
- **Verify:** `/chat` without a token → `401`; with a token → `200`; a body carrying a
  forged `student_id` is overridden by the JWT's; 20 rapid requests → `429`; a request from
  a disallowed `Origin` is refused; **`/admin/anything` → `404`** from the gateway, while
  `docker compose exec gateway curl content_service:8003/admin/...` still works internally.

### P1.10 — Repoint the frontend

The smallest possible frontend change: two files, no components touched.

- **Files:** `frontend_tunsay/server.ts`, `frontend_tunsay/src/services/geminiService.ts`
- `server.ts`: delete the `GoogleGenAI` import and the inline system prompt; `/api/tutor`
  becomes a proxy to `${GATEWAY_URL}/chat` that forwards the `Authorization` header. Keep
  serving the SPA and keep the Vite middleware.
- `geminiService.ts`: send `session_id`, `problem_id`, `active_step_index`; map
  `snake_case` → `camelCase`. **Keep the local fallback engine** — it is the offline story.
- **Depends:** P1.9
- **Verify:** `npm run lint` clean, then in a browser at `localhost:3000`: log in, ask
  "why do I multiply?", get a Khmer answer. Confirm in the **network tab** that it went
  through `:8000`, and in `docker compose logs orchestrator` that the graph ran.

### ✅ Milestone 1

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

### P2.2 — Misconception-aware pedagogy

- **Files:** `pedagogy_service/app/core/explanation_generator.py`, both prompt YAMLs,
  `orchestrator/.../nodes/explain.py`
- The explanation takes `misconception_code` and addresses *that* error, rather than
  re-explaining the step generically.
- **Depends:** P2.1
- **Verify:** a golden-query test — the same wrong answer with two different misconception
  codes yields materially different explanations.

### P2.3 — `student_profile_service`

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

### P2.4 — `clarify` node + real session continuity

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

### P2.5 — Parent mode, properly

Currently a single canned paragraph in `geminiService.ts`.

- **Files:** `pedagogy_service` prompts, `orchestrator/.../nodes/explain.py`
- Parent mode explains *how to teach this to your child* — it may reveal the answer and the
  method, which student mode must not. Sets `is_parent_help` so the bubble renders yellow.
- **Depends:** P2.2
- **Verify:** the same question in `mode: student` vs `mode: parent` returns substantively
  different content; student mode never leaks the final answer before the last step.

### ✅ Milestone 2

Server-side grading, misconception-driven explanations, persistent progress, working safety
gate, no `correct_answer` in any client payload.

---

## Phase 3 — Voice and camera

The UI already exists and is fully designed — `VoiceModal.tsx` and `HomeworkScanner.tsx`
are wired into `ChatView` and `App`. Both are theater. This phase makes them real, which is
mostly backend plus replacing two `setTimeout` calls.

### P3.1 — `stt_service`

- **Files:** `app/core/{audio_preprocess,transcriber,language_detect,math_notation_normalizer}.py`,
  `tests/test_stt_normalization.py`
- **Khmer ASR is the hard part and the schedule risk.** Evaluate options against real
  Khmer child speech before committing; assume no off-the-shelf model is good enough and
  budget for it. Do not let English accuracy stand in for validation.
- `math_notation_normalizer.py`: "two over three" → `2/3`, "five times eight" → `5*8`, and
  the Khmer equivalents. Pure and unit-tested — no model needed to test it.
- **Depends:** Milestone 2
- **Verify:** `pytest tests/test_stt_normalization.py` covers both languages;
  `curl -F 'file=@sample_km.webm' localhost:8009/transcribe` returns usable Khmer text.

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

- **Files:** `app/core/retriever.py`, `app/ingest/`, `orchestrator/.../retrieval_client.py`
- Ingest the WEG curriculum into Qdrant so explanations use the vocabulary and method the
  child's own textbook uses. **Khmer embedding quality needs validating** — verify
  retrieval relevance in Khmer specifically before wiring it into `explain`.
- **Verify:** a curriculum-specific question retrieves the right passage; explanations cite
  the textbook method rather than a generic one.

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

- [?] **D0.1** Confirm the architecture seam — `server.ts` becomes a gateway proxy?
      *Blocks P2.1. Phase 1 is safe to build either way.*
- [ ] **D0.2** Make this one repo — `git init` at root, drop `frontend_tunsay/.git` ✅ *decided*
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
- [ ] **P1.3** `auth_service` — school code + PIN, **no password/email** → *needs P1.1, P0.6*
- [~] **P1.4** `content_service` + seeding — YAML done, `seed_exercises.py` to write → *needs P1.1*
- [x] **P1.5** `solver_service` — 47 tests; Khmer numerals, exact fractions ✅ *2026-08-15*
- [x] **P1.6** `safety_service` — 73 tests; bilingual rules both directions ✅ *2026-08-15*
- [ ] **P1.7** `orchestrator` — 5-node graph, session store, logging → *needs P1.2, P1.4, P1.5, P1.6*
- [ ] **P1.8** `pedagogy_service` — owns the Gemini call → *needs P1.2*
- [ ] **P1.9** `gateway` — cors, auth_verify, rate_limit → *needs P1.3, P1.7*
- [ ] **P1.10** Repoint the frontend — `server.ts` + `geminiService.ts` → *needs P1.9*
- [ ] 🏁 **Milestone 1** — browser → login → question → Gemini answer via the Python stack

### Phase 2 — Real tutoring

- [ ] **P2.1** `grading_service` + `POST /answers` ⭐ *highest-value task* → *needs M1, D0.1*
- [ ] **P2.2** Misconception-aware pedagogy → *needs P2.1*
- [ ] **P2.3** `student_profile_service` — mastery, stars, hint telemetry → *needs P2.1*
- [ ] **P2.4** `clarify` node + session continuity + explanation cache → *needs P2.2*
- [ ] **P2.5** Parent mode, properly → *needs P2.2*
- [ ] 🏁 **Milestone 2** — server-side grading, persistent progress

### Phase 3 — Voice and camera

- [ ] **P3.1** `stt_service` ⚠ *Khmer ASR is the schedule risk* → *needs M2*
- [ ] **P3.2** Real audio capture — replace the `setTimeout`; fix the dropped transcript → *needs P3.1*
- [ ] **P3.3** `ocr_service` — handwritten Khmer numerals → *needs M2*
- [ ] **P3.4** Real scanning — replace the `MOCK_PROBLEMS` picker → *needs P3.3*
- [ ] 🏁 **Milestone 3** — voice and camera real

### Phase 4 — Depth and hardening

- [ ] **P4.1** `retrieval_service` (RAG over WEG curriculum)
- [ ] **P4.2** Cost controls — token budgets, cache-hit logging, heuristics
- [ ] **P4.3** Child-data privacy pass
- [ ] **P4.4** Offline / low-bandwidth assessment — *before any field pilot*

### Content, not code

- [ ] Author grade 5 and grade 6 problems — the corpus has **zero** grade 6 (see risks)
- [ ] Author at least one `input_format: text` step — the corpus has **none**, so that
      `StepCard` widget path ships untested
- [ ] Fix `science-g4-water/sci-step-1`: `total_steps: 3` but the problem has 2 steps
- [ ] Verify the `gemini-3.7-flash` model ID against current Google model IDs

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
