# Tunsay (ទន្សាយ)

An AI homework tutor for **Westline Education Group (WEG)** in Cambodia. A cartoon rabbit
mascot — *tunsay* is Khmer for "rabbit" — walks a child through their homework one step at
a time, with a three-rung hint ladder, and never just hands over the answer.

- **Bilingual** — Khmer (`km`, the default) and English (`en`). Every user-facing string
  exists in both.
- **Subjects** — math, science, english.
- **Grades** — targets grades 1–12; **focus band is grades 4–6**.
- **Modes** — `student` (guided discovery) and `parent` (how to explain it to your child).

---

## Status

- **Frontend & Backend (Phases 0–4 COMPLETE)**:
  - Real voice audio capture (`getUserMedia` + `MediaRecorder`) connected to `/api/chat/audio` (STT).
  - Camera & worksheet scanner connected to `/api/chat/image` (OCR).
  - Socratic student non-leak policy vs parent help mode.
  - Server-side answer checking & misconception-aware explanations.
  - Redis + Postgres write-through session store & star count persistence across page reloads (`F5`).
  - RAG curriculum context integration & 10 exercise seed files covering Grades 3–6.

---

## Pre-Demo Quick Start & Verification

```bash
# 1. Run the automated pre-demo verification suite
python scripts/verify_demo_readiness.py

# 2. Start all backing containers & microservices
docker compose --profile app up -d --build

# 3. Seed demo school & curriculum exercises
python auth_service/scripts/seed_demo_school.py
python content_service/scripts/seed_exercises.py
```

The frontend serves on `http://localhost:3000` and the API gateway on `http://localhost:9000`.

---

## Documentation

Everything about how this system is structured lives in `.claude/`:

| File | What it is for |
|---|---|
| `.claude/claude.md` | Ground truth on guardrails, rules, and conventions. |
| `.claude/architecture.md` | Service boundaries, request flow, and infrastructure. |
| `.claude/contracts.md` | Data model — schemas, endpoint signatures, bilingual fields. |
| `.claude/plan.md` | Canonical execution plan and status. |
