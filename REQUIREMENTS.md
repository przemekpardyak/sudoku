# Requirements & Backlog

> **Communication channel for the autonomous TDD loop.**
> Add bullet points below. The agent will process them in order, add comments
> with what was done, and update deployment status.

---

## Deployment Status

| Field | Value |
|-------|-------|
| **Last deployed** | (pending) |
| **Revision** | (pending) |
| **URL** | https://sudoku-d5mqgioeaa-uc.a.run.app |
| **Proxy** | `gcloud run services proxy sudoku --region=us-central1 --project=ppardyak-cad --port=8080` |
| **Local dev** | `http://localhost:5000` (venv/bin/python3 app.py) |
| **Tests** | 968 total (888 API + 80 E2E), 1 skipped |
| **Git HEAD** | (pending) |

---

## Active Requirements

<!-- Add your requirements below as bullet points. -->
<!-- The agent will add comments under each one as it works on them. -->
<!-- Format: - [requirement text] -->
<!--         - ✅ Done: [summary] or 🚧 In progress or ❌ Failed: [why] or ⏳ Pending -->

- he buttons are too bunched up as a long colum on the right.  Reorganize and resize so that they are aligned with the board better.

- clicking on difficulty should not immediately create a new game.  only new game should do it.
  

---

## Completed

<!-- Completed items move here with full summary. -->

---

## Agent-Extrapolated Requirements

<!-- Requirements the agent identified on its own, derived from existing work. -->
<!-- These follow the same TDD process: add requirement → test → implement → deploy. -->

