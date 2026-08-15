# Contracts — Data Model & Service APIs

**This file is canonical.** Where it disagrees with any other document, this wins.

Everything here is derived from code that already exists and runs:
`frontend_tunsay/src/types.ts`, `src/data/mockProblems.ts`, `src/components/ChatView.tsx`,
`src/services/geminiService.ts`, and `server.ts`. The frontend is the customer; the backend
is being built to serve it. Do not invent a data model — the model below is already
implemented in TypeScript and rendered on screen.

---

## 1. Why the old model was wrong

The superseded docs specified `Problem`, `StudentAnswer`, `GradeLevel`. None of those match
what the UI consumes. The real shape is a **problem containing ordered steps, each carrying
its own scaffolding**:

```
HomeworkProblem
└── steps: StepItem[]              ordered, 1..N, student advances one at a time
    ├── question + inputFormat     mcq | number | text
    ├── correctAnswer
    ├── hint1 → hint2 → hint3      escalating ladder, pre-authored per step
    └── explainDifferently         plain restatement + concrete analogy
```

Every text-bearing field is doubled into Khmer and English.

## 2. Core entities

Mirror these exactly in `dal/schemas/` as Pydantic models. Field names on the wire are
`snake_case`; the gateway aliases to the `camelCase` the frontend expects (`claude.md` §5).

### `HomeworkProblem`

| Field | Type | Notes |
|---|---|---|
| `id` | `str` | e.g. `math-g4-apples` — stable, human-readable slug |
| `title_khmer` / `title_eng` | `str` | |
| `grade` | `int` | Target is **1–12**; **4–6 is the current focus**; `types.ts` currently caps at 6. Validate against a configurable supported set, not a hardcoded `<= 6`. |
| `subject` | `"math" \| "science" \| "english"` | |
| `problem_statement_khmer` / `_eng` | `str` | |
| `image_uri` | `str?` | currently Unsplash URLs in mocks; becomes object-storage keys |
| `steps` | `StepItem[]` | ordered, non-empty |

### `StepItem`

| Field | Type | Notes |
|---|---|---|
| `id` | `str` | unique within the problem |
| `step_number` / `total_steps` | `int` | 1-indexed. `total_steps` is denormalized — **validate `total_steps == len(steps)` at ingest**; the corpus already violates it once (§6). |
| `question_khmer` / `question_eng` | `str` | |
| `input_format` | `"mcq" \| "number" \| "text"` | drives which widget `StepCard` renders |
| `options` | `str[]?` | **required when `input_format == "mcq"`**, absent otherwise |
| `correct_answer` | `str` | always a string, even for `number` |
| `hint1`, `hint2` | `{khmer, eng}` | rungs 1–2: nudges |
| `hint3` | `{title_khmer, title_eng, example_khmer, example_eng}` | rung 3: a *worked analogous example*, never this problem's answer |
| `explain_differently` | see below | |

### `explain_differently`

`{ simple_khmer, simple_eng, analogy_title, analogy_khmer, analogy_eng, analogy_type }`
where `analogy_type ∈ {apples, pizza, water, plants}`. The type selects the illustration in
`ExplanationCard.tsx`; adding a value there requires a matching frontend change.

`analogy_title` is deliberately **one field, not a `_khmer`/`_eng` pair** — it carries Khmer
with a parenthesized English gloss (`ប្រអប់ផ្លែឈើ (Fruit Boxes)`), the same convention as
`name` above. It satisfies §3's bilingual rule through the parenthetical, so do not "fix" it
into a pair.

### `ChatMessage`

`{ id, sender: "user"|"sayo"|"system", text_khmer?, text_eng, timestamp, image_uri?,
problem?, active_step_index?, is_safety_refusal?, is_parent_help? }`

`is_safety_refusal` and `is_parent_help` are **render flags** — they select the bubble color
(pink refusal / yellow parent). The backend must set them; the frontend will not infer them.

### `UserProfile`

`{ name, grade, subject, mode: "student"|"parent", language: "km"|"en",
completed_problems_count, stars_earned }`

`name` is currently the literal string `"សុជា (Sochea)"` — Khmer name with a parenthesized
Latin transliteration. `utils/language.ts::getDisplayName` splits it. Preserve that
convention when `auth_service` starts issuing real profiles.

## 3. The bilingual field rule — **pick this one**

The codebase is currently inconsistent, and this must be resolved before any backend code
is written:

- `mockProblems.ts` populates **both** `khmer` and `eng` on every field.
- `server.ts` and `geminiService.ts` populate **one** and set the other to `''`.
- `ChatView.tsx:444` renders with a fallback: `isKhmer ? (textKhmer || textEng) : (textEng || textKhmer)`.

**Rule: authored content is always bilingual; generated content may be single-language.**

| Content kind | Requirement |
|---|---|
| **Authored** — problems, steps, hints, analogies, UI strings, error fallbacks | Both fields populated. Reject at validation if either is empty. |
| **Generated** — live LLM tutor turns | The requested `language` is populated; the other is `""`. Never `null` — the frontend fallback relies on `""` being falsy. |

Rationale: translating every LLM turn doubles latency and cost for a child who reads one
language, while a seed problem missing its Khmer text is simply broken content for the
primary audience. `content_service` enforces the first row at ingest time.

## 4. Service APIs

All client traffic goes through the gateway. Services are not publicly reachable.

### Gateway (`:8000`) — the only public surface

| Method | Path | Proxies to | Notes |
|---|---|---|---|
| `POST` | `/auth/register` `/auth/login` | auth_service | issues JWT |
| `GET` | `/auth/me` | auth_service | |
| `POST` | `/chat` | orchestrator `/chat` | **the core loop** |
| `POST` | `/chat/audio` | orchestrator `/chat/audio` | `multipart/form-data` |
| `POST` | `/chat/image` | orchestrator `/chat/image` | `multipart/form-data` |
| `GET` | `/problems` `/problems/{id}` | content_service | |
| `POST` | `/answers` | orchestrator | server-side answer check |
| `GET` | `/health` | — | aggregates downstream health |

There is deliberately **no `/admin/*` route**. Content editing does not pass through the
gateway at all — see below.

Middleware order: `cors` → `auth_verify` → `rate_limit` → route. Rate limiting is
per-`student_id` and applies to the LLM-cost-heavy paths (`/chat*`), not to `/problems`.

### Auth credentials — **one role, no password, no email**

**Every account is a student.** There are no account types, no `role` field, and no
`parent_student_link` table. `LoginView.tsx` has no account-type picker and never sends
one; teachers appear only as prose ("your teacher gave you a code"). Do not add roles
speculatively — if teacher accounts are needed later, that is a deliberate feature with its
own UI, not a column to leave lying around.

**`UserMode` is not a role.** The student/parent split in the UI is a per-session toggle
(`ModeSwitcher.tsx`) on the child's own account: a parent sitting beside their child flips
it to get "here is how to explain this". It is not an identity and is not stored on the
user. Parent mode (P2.5) is unaffected by the single-role decision.

`LoginView.tsx` implements three entry flows. `auth_service` must serve these, not a
conventional email/password scheme — the users are 6–12 years old.

| Flow | Collects | Meaning |
|---|---|---|
| `school-code` | `school_code` (e.g. `TUNSAY-G4-DEMO`) → then `student_name` + optional 4-digit `pin` | a child at a partner school; the code resolves to school, grade, and class |
| `public-signup` | 3 steps: `student_name` → `grade` + `class_name` → `parent_contact` + `pin` | a family signing up directly |
| `returning-login` | `school_code` **or** `student_name`, plus `pin` | coming back |

Consequences `auth_service` must handle:

- **The 4-digit PIN is optional** in the school-code flow. Decide what an account with no
  PIN means — likely a classroom device where the school code is the real credential.
  A 4-digit PIN is trivially brute-forced, so rate-limit auth attempts per `student_name`
  and scope PINs to a school code rather than treating them as globally unique secrets.
- **`student_name` is the identifier**, and it is a Khmer display string like
  `"សុជា (Sochea)"` (§2). It is not unique on its own — it must be scoped by school code or
  account. Do not build a global unique index on it.
- **`school_code` resolves to `{school_name, grade, class_name, subject_track}`.** `LoginView`
  currently hardcodes this lookup; `auth_service` needs a schools/classes table to serve it.
- **This contradicts a stated guardrail.** `claude.md` §4 defers multi-tenancy
  (school/class grouping), but the login UI is already built around school codes and
  `Class 4A`. Resolve before P1.3: either the code is an opaque enrollment token now and
  real grouping comes later, or multi-tenancy is in scope from the start. Recommend the
  former — store `school_code` and `class_name` as fields, defer the hierarchy.
- Today all three handlers call `onLoginSuccess({name, grade, language, mode})` with local
  state and no network. `pin`, `school_code`, `parent_contact`, and `class_name` are
  collected and then **discarded**. Note all three hardcode `mode: 'student'` — further
  confirmation that login carries no role.

### Admin is not on the gateway · **DECIDED**

`/admin/*` was originally specified as "teacher/admin role required". With one role that
gate cannot exist, and the resolution is to remove the surface rather than invent a
credential for it: **content editing is not exposed through the gateway.**

- `gateway/app/routes/admin.py` is **deleted**. Do not recreate it.
- `content_service` keeps its admin CRUD endpoints, reachable only on the internal compose
  network (`expose:`, never `ports:`). Nothing outside Docker can reach them.
- Operators edit content two ways: re-run `scripts/seed_exercises.py`, or
  `docker compose exec content_service ...` for one-offs.
- Consequence to accept knowingly: any service on the compose network can call content
  CRUD. That is fine while every service is ours; it stops being fine the day something
  untrusted joins the network.

Revisit only when teachers get a real UI — at which point it is a deliberate feature with
its own auth, not a hole to patch.

### `POST /chat` — the contract that replaces `/api/tutor`

`geminiService.ts` currently sends `{prompt, mode, problemContext, language}` and receives
`{textKhmer, textEng, isSafetyRefusal}`. That request is **stateless, unauthenticated, and
carries no history** — three gaps the orchestrator needs closed.

Request:
```jsonc
{
  "session_id": "uuid",          // NEW — orchestrator owns the transcript
  "student_id": "uuid",          // NEW — from the JWT, not the body; gateway injects it
  "prompt": "why do I multiply?",
  "mode": "student",             // student | parent
  "language": "km",
  "problem_id": "math-g4-apples", // NEW — replaces shipping the whole problem back up
  "active_step_index": 0
}
```

Response:
```jsonc
{
  "text_khmer": "...",
  "text_eng": "",                 // single-language per §3
  "is_safety_refusal": false,
  "is_parent_help": false,
  "session_id": "uuid",
  "suggested_next": null          // optional: problem_id from recommend_next
}
```

`problemContext` becomes `problem_id`: the orchestrator loads the problem from
`content_service` rather than trusting a client-supplied blob. Keep the `mode` and
`language` names — they already flow through three components.

### `POST /answers` — **closes a real hole**

Today `ChatView.tsx:221` checks answers **in the browser**:

```ts
const isCorrect = studentAnswer.toLowerCase().trim() === currentStep.correctAnswer.toLowerCase().trim()
  || studentAnswer.includes(currentStep.correctAnswer);
```

Two defects. First, `correct_answer` is shipped to the browser inside every
`HomeworkProblem`, so any child can read it in devtools. Second, `.includes()` means for
`correctAnswer: "5"`, the answer `"55"` grades as correct, and for `"apples"`, the answer
`"I hate apples"` grades as correct.

`grading_service` owns this. Request:
`{session_id, problem_id, step_id, student_answer, language}` →
`{is_correct, misconception_code?, feedback_khmer, feedback_eng, advance_to_step?}`.

`GET /problems/{id}` must **strip `correct_answer`** from every step before serialization.
The frontend switches from local comparison to awaiting this response.

### `POST /chat/audio` and `/chat/image`

`multipart/form-data`, field `file`, plus `session_id` / `language` as form fields.
Audio → `stt_service` (transcribe, detect language, normalize spoken math: "two over three"
→ `2/3`) → the `/chat` pipeline. Image → `ocr_service` (preprocess, math OCR) → a
`HomeworkProblem` matched or generated → returned as a chat message with `problem` attached.

### Internal services

| Service | Owns |
|---|---|
| `auth_service` | student identity only; JWT issue + verify. No account types. |
| `content_service` | `HomeworkProblem` CRUD, seeding, bilingual validation at ingest. Admin CRUD is internal-network only — never gateway-routed. |
| `solver_service` | computing the answer and formatting solution steps |
| `grading_service` | answer checking + misconception classification |
| `pedagogy_service` | grade-banded explanation generation — **owns the Gemini call and system prompt** |
| `retrieval_service` | Qdrant RAG over curriculum content |
| `student_profile_service` | mastery model, progress, hint-usage telemetry |
| `safety_service` | age gate + content filter, on input and output |
| `stt_service` | transcription + math-notation normalization |
| `ocr_service` | image preprocessing + math OCR |

## 5. What is fake in the frontend today

Each row is a backend deliverable and its acceptance test.

| UI surface | What it actually does now | Backend that replaces it |
|---|---|---|
| `HomeworkScanner.tsx` | `setTimeout` "analyzing", then user **picks from `MOCK_PROBLEMS`**. The camera is never opened. | `ocr_service` + `POST /chat/image` |
| `VoiceModal.tsx` | `setTimeout` sets a canned transcript. No `MediaRecorder`, no `getUserMedia`. | `stt_service` + `POST /chat/audio` |
| Answer checking | client-side string compare (§4) | `grading_service` + `POST /answers` |
| Hint ladder | `HintSheet.tsx` local `hintLevel` state over pre-authored text; **no telemetry** | keep local; emit usage events to `student_profile_service` |
| Login | 3 flows collect school code / name / PIN, then **discard them** and call `onLoginSuccess` with local state | `auth_service` |
| Profile / stars | React `useState` in `App.tsx`; lost on refresh | `student_profile_service` |
| Chat history | in-memory array; "New Chat" clears it | orchestrator `session_store` |
| Problem catalog | `MOCK_PROBLEMS` (7 problems) imported directly | `content_service` `GET /problems` |

**Two live bugs found while deriving this contract** — fix when touching these files:

1. `App.tsx:175` — `onTranscriptSubmitted={() => handleStartChatWithProblem()}` discards the
   transcript argument that `VoiceModal` passes. Voice input is dropped on the floor.
2. `metadata.json` requests `camera` and `microphone` permissions that no code uses.

## 6. Seed data

**`frontend_tunsay/src/data/mockProblems.ts` (7 problems) is the seed corpus.** It is
authored, bilingual, step-decomposed, and already validated by being rendered.

`content_service/scripts/seed_exercises.py` transcodes it to YAML under `seed_data/` and
loads it. Do **not** hand-author the `grade4_fractions.yaml` the old docs described — that
was a placeholder for content that turned out to already exist.

Also exported by that module: `generateHistoryChatForProblem(problem, name)`, which
synthesizes a plausible prior conversation. That is demo scaffolding, not a contract —
drop it once `session_store` is real.

### Transcode status and corpus defects

✅ **Done** — `content_service/seed_data/*.yaml`, 7 files, 18 steps, `snake_case`, Khmer
preserved byte-for-byte (verified in both directions against the `.ts` source: every string
in the YAML appears verbatim in the source, and every Khmer literal in the source appears in
the YAML). `scripts/seed_exercises.py`, the loader, is still to write.

Known defects in the corpus — do not silently "fix" them in the seed files; fix the source
and re-transcode, and have `content_service` reject them at ingest:

| Defect | Impact |
|---|---|
| `science-g4-water` / `sci-step-1` declares `total_steps: 3`, but the problem has 2 steps (and `sci-step-2` says 2) | `StepTrail` would render "step 1 of 3" then jump to completion. Suggests a third step was planned and never authored. |
| No step anywhere uses `input_format: "text"` — 14 are `mcq`, 4 are `number` | The free-text branch of `StepCard` has zero seed coverage and would ship untested. |
| Grade coverage: g4 ×4, g3 ×2, g5 ×1, **g6 ×0** | The current focus band (4–6) is barely covered; see `plan.md` risks. |
