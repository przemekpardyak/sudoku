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

- The buttons are too bunched up as a long column on the right. Reorganize and resize so that they are aligned with the board better.
  - ✅ Done: Reorganized 13 action buttons from single-column flex into grouped 2-column grids (`.action-row`). New Game spans full width. Reduces vertical height ~40%, aligns with board. 5 E2E tests added.

- Clicking on difficulty should not immediately create a new game. Only new game should do it.
  - ✅ Done: Difficulty buttons now only update selected difficulty + label, show hint message. New Game button uses selected difficulty. Updated old test, added 3 new E2E tests.

---

## Completed

<!-- Completed items move here with full summary. -->

---

## Agent-Extrapolated Requirements

<!-- Requirements the agent identified on its own, derived from existing work. -->
<!-- These follow the same TDD process: add requirement → test → implement → deploy. -->

