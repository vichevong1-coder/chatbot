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

- **Frontend: built and running, on mock data.** The UI is complete and polished, but every
  problem, transcript, scan and progress number comes from local mocks. Its only network
  call goes straight to Gemini from `frontend_tunsay/server.ts`.
- **Backend: scaffolded, not implemented.** The twelve-service Python tree, `dal/` and
  `docker-compose.yml` exist as directories and empty files. `dal/` is now installable; the
  rest is still to be written. Nothing in the Python stack runs yet.

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

The frontend serves on `:3000` and the API gateway on `:8000`. Note that
`docker-compose.yml` is still an empty placeholder, so today only the frontend command
actually brings anything up.

## Documentation

Everything about how this system is meant to fit together lives in `.claude/`:

| File | What it is for |
|---|---|
| `.claude/claude.md` | Start here. Ground truth on what is real vs. aspirational, plus the guardrails and conventions. |
| `.claude/architecture.md` | Service boundaries, request flow, the repository tree, and infrastructure. |
| `.claude/contracts.md` | The canonical data model — schemas, endpoint signatures, the bilingual field convention. |
| `.claude/plan.md` | The canonical execution plan: ordered tasks with validation commands. |
