# Tunsay (ទន្សាយ)

An AI homework tutor for **Westline Education Group (WEG)** in Cambodia. A cartoon rabbit
mascot — *tunsay* is Khmer for "rabbit" — walks a child through their homework one step at
a time, with a three-rung hint ladder, and never just hands over the answer.

- **Bilingual** — Khmer (`km`, the default) and English (`en`). Every user-facing string
  exists in both.
- **Subjects** — math, science, english.
- **Grades** — targets grades 1–12 long term; **the current focus is grades 4–6**.
- **Modes** — `student` (guided discovery) and `parent` (how to explain it to your child).

## Status

Honest state of the repo:

- **Frontend: built and running.** The UI is complete and polished. It is now wired to the Python backend via the gateway, no longer relying on direct Gemini calls from the local node server. Some features like scanning and profile progress still use local mocks pending Phase 2 and 3 completion.
- **Backend: Phase 1 complete.** The core Python stack is implemented and running, achieving a real end-to-end tutoring turn. Services including `dal`, `auth`, `content`, `solver`, `safety`, `orchestrator`, `pedagogy`, and `gateway` are functioning.

`frontend_tunsay/` was generated in Google AI Studio and first landed in a separate repo,
but **this repository is now the single source of truth** — frontend and backend alike. Edit
the frontend here freely; the upstream clone was temporary storage and is no longer
authoritative.

## Quick start

```bash
# Backing services and (eventually) the Python services
docker-compose up

# Frontend — separate repo, own dependencies
cd frontend_tunsay && npm install && npm run dev
```

The frontend serves on `:3000` and the API gateway on `:8000`. The Python backend services and backing infrastructure (Postgres, Redis, Qdrant, MinIO) are fully configured in `docker-compose.yml`.

## Documentation

Everything about how this system is meant to fit together lives in `.claude/`:

| File | What it is for |
|---|---|
| `.claude/claude.md` | Start here. Ground truth on what is real vs. aspirational, plus the guardrails and conventions. |
| `.claude/architecture.md` | Service boundaries, request flow, the repository tree, and infrastructure. |
| `.claude/contracts.md` | The canonical data model — schemas, endpoint signatures, the bilingual field convention. |
| `.claude/plan.md` | The canonical execution plan: ordered tasks with validation commands. |
