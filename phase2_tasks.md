# Phase 2: Decoupled Division of Labor & Mocking Guide

This document defines the roles, independent tasks, git branches, and mocking strategies for our 4-person team to implement **Phase 2 (Real Tutoring)** in parallel without blocking each other.

---

## 👤 Member 1: AI Prompt Engineer · ✅ COMPLETED & MERGED
* **Git Branch**: `feature/pedagogy-prompts` (merged into `main` and `sovandeth`)
* **Focus**: Misconception-Aware Pedagogy (Phase 2.2) and LLM prompting quality.

### Independent Workflow
You do **not** need the Frontend, Orchestrator, or Database to test prompts. You will test the `pedagogy_service` prompts directly in isolation.

1. **Service Path**: `pedagogy_service/`
2. **Prompts to Tune**:
   - `pedagogy_service/app/ai/prompts/explain_grade1_3.yaml`
   - `pedagogy_service/app/ai/prompts/explain_grade4_6.yaml`
3. **Execution**:
   - Run the pedagogy service locally or in Docker.
   - Access Swagger docs at `http://localhost:9006/docs`.
   - Send `POST /explain` requests with simulated misconception contexts.
4. **Mock Test Payload**:
   ```json
   {
     "prompt": "why is the answer 13?",
     "grade": 4,
     "language": "km",
     "mode": "student",
     "context": "Current step: Calculate 5 times 8. Student answered: 13. Misconception: operation_confusion"
   }
   ```
5. **Goal**: Ensure Gemini responds in a Socratic way (guiding them gently, pointing out they might have added instead of multiplied, without giving away the answer).

---

## 👤 Member 2: DB & Backend Specialist
* **Git Branch**: `feature/profile-db`
* **Focus**: Student Profile Service (Phase 2.3) and PostgreSQL persistence.

### Independent Workflow
You do **not** need the Frontend or the Orchestrator. You will build and test the database operations in isolation.

1. **Service Path**: `student_profile_service/` (Create FastAPI service structure if it's empty).
2. **Database Schema**: Reference the SQLAlchemy models in `dal/models/student_profile.py` and `dal/models/attempt.py`.
3. **Endpoints to Build**:
   - `GET /profile` (Returns stars, completed problems, and mastery badges).
   - `POST /profile/attempts` (Logs student attempts).
   - `POST /profile/hints` (Deducts active stars when student opens hints).
4. **Execution**:
   - Boot only PostgreSQL: `docker compose up postgres -d`.
   - Run your FastAPI service locally.
   - Use FastAPI Swagger UI (`http://localhost:9008/docs`) to interactively test database reads/writes.
   - Author standard Python tests (`pytest`) under `student_profile_service/tests/`.

---

## 👤 Member 3: Integration & Orchestration Engineer
* **Git Branch**: `feature/orchestrator-graph`
* **Focus**: LangGraph routing integration, Chat Summarization, and Session Continuity (Phase 2.4).

### Independent Workflow
You do **not** need Member 2's database API or Member 1's finished prompts to work on the LangGraph. You will mock these services locally.

1. **Service Path**: `orchestrator/`
2. **Tasks**:
   - Build client queries to talk to `student_profile_service`.
   - Connect the `check_answer` node to report attempts and reward stars.
   - Implement chat transcript summarization when context gets long.
3. **Mocking Downstreams (How to build without blocked dependencies)**:
   - In `orchestrator/tests/conftest.py` (or inside a local test script), stub out the clients so they return hardcoded JSON payloads.
   - Example Mock Client:
     ```python
     class FakeProfileClient:
         async def get_profile(self, student_id):
             return {"stars": 10, "completed_problems": []}
             
         async def record_attempt(self, student_id, problem_id, step_id, is_correct):
             return {"status": "recorded"}
     ```
   - Bind these fakes to the Orchestrator container's app state during development.
4. **Goal**: Run `pytest` inside the `orchestrator/` folder and verify that the LangGraph transitions correctly from safety checking to answer grading and LLM response summarization.

---

## 👤 Member 4: Frontend UI Developer
* **Git Branch**: `feature/frontend-ui`
* **Focus**: React dashboard profile integration, UI animations, and hint triggers.

### Independent Workflow
You do **not** need any backend services running at all. You will mock the Gateway APIs in the Express development proxy.

1. **Service Path**: `frontend_tunsay/`
2. **Mocking Downstreams**:
   - Open `frontend_tunsay/server.ts`.
   - Before forwarding proxy routes, write quick Express mock endpoints returning static data:
     ```typescript
     // Temporary Mock for Profile
     app.get('/api/profile', (req, res) => {
       res.json({
         stars: 25,
         completedProblemsCount: 4,
         name: "Sokha",
         masteryLevels: { "fractions": 0.8 }
       });
     });
     
     // Temporary Mock for Hints
     app.post('/api/profile/hints', (req, res) => {
       res.json({ success: true, remainingStars: 24 });
     });
     ```
3. **Execution**:
   - Run `npm run dev -- -p 3001` to start the frontend on port 3001.
   - Implement the star meters, mastery badges dashboard, correct/incorrect answer animations, and Socratic chat window using these static mocks.

---

## 🚀 Git Integration Day (How to merge)

When all 4 branches are ready, merge using the following steps:

1. **BFF Cleanup**: Member 4 removes the Express mock endpoints from `frontend_tunsay/server.ts`.
2. **Orchestrator Swap**: Member 3 switches the fake clients in the orchestrator to call the actual microservice endpoints.
3. **Bring Up Stack**: Run the full stack locally:
   ```powershell
   docker compose --profile app up -d --build
   ```
4. **End-to-End Testing**: Test by logging in, selecting a problem step, answering it incorrectly to test Member 1's socratic prompts, answering it correctly to test Member 2 & 3's Postgres stars updater, and observing the frontend reflect the live data.
