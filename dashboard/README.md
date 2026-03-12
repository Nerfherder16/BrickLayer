# Autosearch Dashboard

Local control surface for the autoresearch loop. Reads directly from autosearch project directories — no database, no auth, no Docker.

## Start

```bash
cd C:/Users/trg16/Dev/autosearch/dashboard
./start.sh
# or with explicit project:
./start.sh C:/Users/trg16/Dev/autosearch/adbp
```

- Backend: http://localhost:8100
- Frontend: http://localhost:3100

## First-time setup

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

## Switch projects

Use the project name dropdown in the top bar. It scans `C:/Users/trg16/Dev/autosearch/` for directories containing `questions.md`.

You can also pass `?project=/full/path/to/project` in the URL.

## Add questions

Click **+ Add Question** in the Questions panel. Choose domain (D1–D6), enter the question text and optional hypothesis, then pick **Next** (inserts before the first PENDING question) or **End of queue**.

## Flag a finding as wrong

Expand any finding card, click **Flag as Wrong**, enter your correction. This appends a `## Human Correction` block to the finding file — the research agents treat this as Tier 1 authority on next run.

## Auto-refresh

The dashboard polls the backend every 10 seconds. No manual refresh needed while the research loop is running.

## Backend API

- `GET /api/status?project=` — summary counts
- `GET /api/questions?project=` — all questions parsed from questions.md
- `POST /api/questions?project=` — add a new question
- `GET /api/findings?project=` — findings index
- `GET /api/findings/{id}?project=` — full finding content
- `POST /api/findings/{id}/correct?project=` — append human correction
- `GET /api/results?project=` — raw results.tsv rows
- `GET /api/projects` — list available projects
