# Tunsay AI Tutor — Project Status Summary

Based on [README.md](file:///e:/TunSay-AI/README.md) and the documentation files in [.claude/](file:///e:/TunSay-AI/.claude/), here is the summary of what has been accomplished so far and what is planned for the next phases.

---

## 1. What Has Been Done (Phase 0 & Phase 1 Complete)

As of **August 15, 2026**, the project has completed **Phase 0 (Preflight)** and **Phase 1 (One Real End-to-End Turn)**. A working end-to-end vertical slice of the application is now active.

### Phase 0: Preflight & Environment
* **Repository Unification**: Initialized git at the root and removed the nested `frontend_tunsay/.git` to bring the entire codebase (frontend and backend) under single source-of-truth version control.
* **Shared Data Access Layer (`dal`)**: Created the importable `dal/` package, including SQLAlchemy tables and Pydantic schemas. Bootstrapped a Python virtual environment (`.venv/`) to handle dependencies.
* **Docker Infrastructure**: Created a single root [docker-compose.yml](file:///e:/TunSay-AI/docker-compose.yml) setting up backing services: PostgreSQL (database), Redis (cache/sessions), Qdrant (vector DB), and MinIO (object storage).

### Phase 1: Core Python Stack & End-to-End Flow
A student can now log in, submit a query, and get a response processed through the following services:
* **`gateway`**: Handles public routing, rates, CORS, case conversion (`camelCase` ↔ `snake_case`), and JWT authentication.
* **`auth_service`**: Implements school-code + PIN validation, JWT emission, and lockout throttling.
* **`content_service`**: Exposes curricula and problems to the stack; includes database seeding scripts.
* **`solver_service`**: Evaluates arithmetic expressions using exact fraction math (handles Khmer numerals).
* **`safety_service`**: Blocks toxic, unsafe, or cheating prompts in both Khmer and English.
* **`pedagogy_service`**: Connects to the Gemini API (`gemini-3.7-flash`) with structured prompts adapted for grades 4–6.
* **`orchestrator`**: Coordinates execution using a 5-node LangGraph state machine.
* **Frontend Repointed**: The Node/Express BFF `server.ts` is configured as a proxy to the Python `gateway`, completely routing the core chat loop through the Python microservices instead of calling Gemini directly from Node.

---

## 2. What Needs to Be Done (Next Phases)

The remaining work is divided into three key phases focusing on real tutoring, voice/camera inputs, and production hardening.

### Phase 2: Real Tutoring (Upcoming Focus)
* **P2.1: `grading_service` & `POST /answers`** *(Highest Priority)*
  * Implement server-side grading (exact matches, equivalent fractions, Khmer/Latin numeral normalization).
  * Ensure the correct answer is stripped from public client payloads to prevent cheating.
  * Classify student misconceptions into stable codes (e.g., place value error, operation confusion).
* **P2.2: Misconception-Aware Pedagogy**: Modify `pedagogy_service` prompts to tailor Tunsay's explanations to specific classified misconceptions rather than generic replies.
* **P2.3: `student_profile_service`**: Model skill mastery and persist stars/progress to DB, replacing the client-side `useState` mock.
* **P2.4: Session Continuity & Caching**: Cache repetitive responses to save token costs and implement conversation summaries for long sessions.
* **P2.5: Parent Mode**: Adjust prompts to explain *how* to teach the child (which allows revealing answers) compared to student mode (which never gives answers).

### Phase 3: Voice & Camera
* **P3.1 & P3.2: `stt_service` & Audio Integration**: Implement real Speech-to-Text for Khmer child speech and replace the frontend audio capture mocks.
* **P3.3 & P3.4: `ocr_service` & Scanner Integration**: Build math OCR capable of reading handwritten Khmer numerals from homework worksheets and decompose scanned problems into step-by-step hint ladders.

### Phase 4: Depth & Hardening
* **P4.1: Vector Retrieval (RAG)**: Ingest Westline Education Group (WEG) curriculum into Qdrant for curriculum-aligned explanations.
* **P4.2: Cost Controls**: Implement student-level daily token budgets and caching.
* **P4.3: Child-Data Privacy**: Audit logs and databases to ensure no children's answers or uploaded assets are leaked.
* **P4.4: Low-Bandwidth Assessment**: Assess offline capabilities and connection resiliency for local Cambodian schools.

---

## 3. Content Tasks & Outstanding Risks
* **Content Deficit**: The seeded content lacks Grade 6 problems entirely and only contains 1 problem for Grade 5. Additional math, science, and English exercises must be authored.
* **Format Testing**: Author a problem step with `input_format: text` (the current corpus only has number/mcq formats, meaning the text-input widget pathway is untested).
* **Corpus Fix**: Correct the `science-g4-water/sci-step-1` problem where `total_steps: 3` is declared but only 2 steps exist.
