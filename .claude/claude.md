# Tunsay — Agent Context

Working context for Claude on this repository. Read this first; it tells you what is real,
what is aspirational, and which rules are non-negotiable.

**Doc map**

| File | Read it when |
|---|---|
| `claude.md` (this file) | Always. Ground truth, guardrails, conventions. |
| `architecture.md` | You need service boundaries, the repo tree, or "where does X live". |
| `contracts.md` | You are writing any endpoint, schema, or client. **Canonical data model.** |
| `plan.md` | You are picking up work. Task list with validation commands. **Canonical plan.** |

`k12-tutor-bot-full-structure.md` and `todolist.md` have been **removed**. They were right
about the long-term K–12 ambition but wrong about everything nearer to hand — the product
name, the current grade focus, the bilingual requirement, the subject breadth, and the fact
that a frontend already exists. The root-level `plan.md` is the last survivor of that set
and should go too (`plan.md` P0.5).

---

## 1. Ground truth — read before believing any other document

Verified against the filesystem on 2026-08-15.

- **All 198 backend files are 0 bytes.** Every directory in `architecture.md` exists; every
  Python file in it is empty. Nothing is implemented. No `docker-compose.yml`, `.env`,
  `.gitignore`, or `README.md` has content either.
- **`frontend_tunsay/` is the only real code** — ~300 KB of working React. It is a complete,
  polished UI with mock data behind it.
- **This repository is the single source of truth — backend and frontend both.** Edit
  anything under `frontend_tunsay/` freely; it is first-class code here, not a vendored
  dependency. Ordinary care applies (a teammate also works on the UI), but there is no
  upstream that can overwrite you.
- **How the lopsided state happened:** the frontend was generated in **Google AI Studio**
  and initially lived in a separate repo, which is why there is a polished React app with
  mock data and no backend at all — AI Studio produces exactly that in one shot. That repo
  was temporary storage; it is no longer authoritative.
- **The repo root is not yet a git repository**, and `frontend_tunsay/` still carries a
  nested `.git` from the clone. Both are leftovers to clean up — see `plan.md` D0.2.
- AI Studio fingerprints, so you can tell generated scaffolding from deliberate design:
  `metadata.json` (`MAJOR_CAPABILITY_SERVER_SIDE_GEMINI_API`), `assets/.aistudio/`,
  `"name": "react-example"` in `package.json`, the `DISABLE_HMR` comments in
  `vite.config.ts`, and the "AI Studio automatically injects this" notes in `.env.example`.
  `server.ts` is one of those artifacts — it exists because AI Studio apps need a
  server-side Gemini proxy, not because anyone chose a BFF architecture. That makes
  demoting it to a gateway proxy cheap and consistent with intent (§3). Knowing which files
  are generated scaffolding still matters: it tells you what is safe to rewrite.
- Therefore: *no task in this repo is "modify existing behavior".* Every backend task is
  "create from nothing, against a contract the frontend already implies".

## 2. What the product actually is

**Tunsay (ទន្សាយ, "rabbit")** — an AI homework tutor for **Westline Education Group (WEG)**
in Cambodia. A cartoon rabbit mascot walks a child through their homework one step at a
time, never handing over the answer.

| | |
|---|---|
| Audience | Long-term **grades 1–12**; **current focus is grades 4–6**. Plus a parent mode. |
| Subjects | **math, science, english** |
| Languages | **Khmer (`km`) and English (`en`)** — km is the default |
| Modes | `student` (guided discovery) · `parent` (how to explain it to your child) |
| LLM | **Google Gemini** via `@google/genai` |

**Grade scope, precisely.** The product targets grades 1–12 eventually; the team is building
grades **4–6 first**. The frontend has narrowed further ahead of the backend: `types.ts`
declares `Grade = 1|2|3|4|5|6`, so it currently cannot express a grade above 6. Treat 4–6 as
what must work, 1–6 as what the UI can already represent, and 1–12 as what the schema must
not permanently exclude. Do not hardcode `6` as an eternal upper bound.

The pedagogy is the product. A problem is not a question-and-answer pair; it is a
`HomeworkProblem` decomposed into ordered `StepItem`s, each with a **three-rung hint ladder**
(nudge → stronger nudge → worked analogous example) and an **"explain differently"** card
(plain restatement + a concrete analogy: apples / pizza / water / plants). Anything that
flattens a problem into one answer has destroyed the product. See `contracts.md` §2.

## 3. The architecture decision everything else depends on

Two systems are described in this repo and they are not the same system:

- **What runs today:** `frontend_tunsay/server.ts`, an Express BFF on port 3000. It serves
  the Vite app and exposes one endpoint, `POST /api/tutor`, which calls Gemini directly
  with an inline system prompt.
- **What is scaffolded:** twelve Python services behind an API gateway, with JWT auth,
  Postgres/Redis/Qdrant, and a LangGraph orchestrator.

**Decision (assumption — confirm before Phase 2):** the Python backend is the target. The
seam moves as follows:

```
now:     browser → server.ts ──(Gemini SDK)──▶ Gemini
target:  browser → server.ts ──(proxy only)──▶ gateway :8000 → orchestrator → … → Gemini
```

`server.ts` keeps serving the SPA and keeps the `/api/tutor` path, but its body becomes a
thin proxy to the gateway. The Gemini call, the system prompt, and the API key move
server-side into `pedagogy_service`. No frontend component changes in Phase 1 — only
`server.ts` and `geminiService.ts`.

This is the single load-bearing assumption in these docs. If the intent is instead to grow
`server.ts` into the backend and delete the Python tree, say so — `plan.md` becomes a
different document.

## 4. Guardrails

**Do not over-scope.** Explicitly out of scope until stated otherwise:

- Kubernetes — `docker-compose` only.
- Notification service, Prometheus/Grafana. Structured logs via
  `orchestrator/app/utils/logging.py` are the observability story.
- Multi-tenancy (school/class grouping) — **but note the contradiction**: `LoginView.tsx`
  is already built around school codes (`TUNSAY-G4-DEMO`) and classes (`Class 4A`). Store
  them as flat fields; defer the hierarchy. See `contracts.md` §4.
- WebSocket / streaming audio. Audio is a recorded blob posted as `multipart/form-data`.
- Grades outside 4–6, for now. **But do not delete the grade 7–9 and 10–12 prompt files** —
  they are future scope, not dead scope. Build for 4–6, leave the other bands stubbed.

**Do not silently change these.** Flag and ask instead:

- The LLM provider. The project is Gemini; do not swap it for another vendor.
- `server.ts` pins model `gemini-3.7-flash`. That string is **unverified** — check it against
  current Google model IDs before relying on it, but do not "fix" it unilaterally.
- The visual design of `frontend_tunsay/` — the neo-brutalist palette (`#6C4FF6` purple,
  `#FFCB3D` yellow, `#2A1E4D` ink, hard `shadow-[Npx_Npx_0px]` offsets) and the mascot are
  brand, not placeholder.

**Bilingual is a correctness constraint, not a feature.** Every user-facing string exists in
both languages. A backend response, prompt, seed row, or error message that only speaks
English is a bug. See `contracts.md` §3 for the exact field convention — the codebase is
currently inconsistent about it and you must follow the rule stated there.

**Child-safety is not optional.** Users are 6–12 years old. `safety_service` gates input
before the orchestrator spends a token, and gates output before it reaches the child. The
current frontend fallback does keyword matching on `'cheat' | 'hack' | 'fight' | 'game code'`
— that is a placeholder, not a filter, and it only runs when the network call fails.

## 5. Conventions

**Python services** — FastAPI, one shape for all of them:

```
<service>/app/
  api/              # routers only: parse, delegate, serialize. No business logic.
  core/             # the actual logic. Pure functions where possible, no FastAPI imports.
  infrastructure/   # DB, cache, and outbound HTTP clients
  schemas/          # Pydantic request/response models
  main.py           # app factory, router registration, /health
```

- Every service exposes `GET /health` returning `{"status": "ok", "service": "<name>"}`.
- Services never import each other. Cross-service calls go through a typed client in
  `orchestrator/app/infrastructure/service_clients/`. Only the orchestrator fans out.
- Shared types live in `dal/`; every service depends on it. `dal/` imports nothing local.
- Async all the way down (`httpx.AsyncClient`, `async def`). No blocking I/O in a request path.

**Naming** — `snake_case` in Python and in JSON on the wire, `camelCase` in TypeScript.
The gateway is the translation boundary; Pydantic aliases do the work. Do not leak
`camelCase` into Python or `snake_case` into the React components.

**Errors** — services raise; the gateway maps to HTTP. A child never sees a stack trace or an
English-only error. Every failure path has a Tunsay-voiced bilingual fallback, the way
`server.ts` already does in its `catch`.

**Logging** — structured JSON via `utils/logging.py`, one shared format across services.
Always carry `request_id`, `student_id`, `session_id`. **Never log** answer content, uploaded
homework images, or audio — this is children's data.

**Tests** — `pytest` per service under `tests/`. Business logic in `core/` is tested without
a running server. The orchestrator additionally keeps `tests/golden_queries/` — a frozen set
of student questions with expected routing decisions, which is the regression net for
prompt and graph changes.

## 6. Where to look

| Question | Look at |
|---|---|
| What does the tutor actually say? | `frontend_tunsay/server.ts` (system prompt) |
| What does a problem look like? | `frontend_tunsay/src/types.ts`, `src/data/mockProblems.ts` |
| How does the tutoring loop work? | `frontend_tunsay/src/components/ChatView.tsx` |
| How do hints escalate? | `src/components/HintSheet.tsx`, `StepCard.tsx` |
| What does login actually collect? | `src/components/LoginView.tsx` |
| What's fake and needs a backend? | `contracts.md` §5 |
