# Requirements & Backlog

> **Communication channel for the autonomous TDD loop.**
> Add bullet points below. The agent will process them in order, add comments
> with what was done, and update deployment status.

---

## Deployment Status

| Field | Value |
|-------|-------|
| **Last deployed** | 2026-07-21 22:15 UTC |
| **Revision** | sudoku-00005-tp7 |
| **URL** | https://sudoku-d5mqgioeaa-uc.a.run.app |
| **Proxy** | `gcloud run services proxy sudoku --region=us-central1 --project=ppardyak-cad --port=8080` |
| **Local dev** | `http://localhost:5000` (venv/bin/python3 app.py) |
| **Tests** | 980 total (888 API + 92 E2E), 1 skipped |
| **Git HEAD** | b204157 |

---

## Active Requirements

<!-- Add your requirements below as bullet points. -->
<!-- The agent will add comments under each one as it works on them. -->
<!-- Format: - [requirement text] -->
<!--         - ✅ Done: [summary] or 🚧 In progress or ❌ Failed: [why] or ⏳ Pending -->



- Clicking on auto-notes if they have been turned on, should turn them off. However, any notes that were input from a user, should remain
  - ✅ Done: Implemented toggle behavior using `autoNotesMask` array to track auto-generated notes. Toggle off clears only auto notes, preserves user-entered. Button shows active state. 3 E2E tests added.

- When hint is pressed, it should be highlighted the way it is right now.  Howver, it should not disappear the moment the curors leaves the hint button.  Instead, the hint should be visible until the user presses the hint button again. Make the button look depressed when hint is active.  Make the hint diseappear when button is off.  Additionally, if a user clicks on the cell that has the hint in it, the hint should be accepted as the number in that cell and should be removed from the hint mode.
  - ✅ Done: Changed from hold-to-preview to click-to-toggle. Button gets active class (depressed look). Hint stays visible until clicked again, cell clicked to accept, or Escape. Removed mousedown/mouseleave/touchstart listeners. 4 new E2E tests, updated 2 old tests.


- Make it obvious that the game is paused.  Also, to make it impossible to cheat when the game is paused, make the board invisible, e.g., by blurring.

- Add users with login, password, the works.  Keep proper per user stats and full game history.  Do not over-engineer this for now. Simple user management.  Create the first user with the credentials:  username:  testuser, password: password and migrate the exisiting game state to them.

---

## Draft

<!-- Partially drafted requirements not ready for the loop yet.  Wait until user moves them to the Active Requirements section. -->

- Add an app version to the app itself
---

## Completed

<!-- Completed items move here with full summary. -->

- The buttons are too bunched up as a long column on the right. Reorganize and resize so that they are aligned with the board better.
  - ✅ Done: Reorganized 13 action buttons from single-column flex into grouped 2-column grids (`.action-row`). New Game spans full width. Reduces vertical height ~40%, aligns with board. 5 E2E tests added. Commit: [`7f20f67`](file:///usr/local/google/home/ppardyak/Dogfood/sudoku)

- Clicking on difficulty should not immediately create a new game. Only new game should do it.
  - ✅ Done: Difficulty buttons now only update selected difficulty + label, show hint message. New Game button uses selected difficulty. Updated old test, added 3 new E2E tests. Commit: [`7f20f67`](file:///usr/local/google/home/ppardyak/Dogfood/sudoku)

- Clicking on auto-notes if they have been turned on, should turn them off. However, any notes that were input from a user, should remain
  - ✅ Done: Implemented toggle behavior using `autoNotesMask` array to track auto-generated notes. Toggle off clears only auto notes, preserves user-entered. Button shows active state. 3 E2E tests added. Commit: [`5a9510c`](file:///usr/local/google/home/ppardyak/Dogfood/sudoku)

- When hint is pressed, it should be highlighted the way it is right now.  Howver, it should not disappear the moment the curors leaves the hint button.  Instead, the hint should be visible until the user presses the hint button again. Make the button look depressed when hint is active.  Make the hint diseappear when button is off.  Additionally, if a user clicks on the cell that has the hint in it, the hint should be accepted as the number in that cell and should be removed from the hint mode.
  - ✅ Done: Changed from hold-to-preview to click-to-toggle. Button gets active class (depressed look). Hint stays visible until clicked again, cell clicked to accept, or Escape. Removed mousedown/mouseleave/touchstart listeners. 4 new E2E tests, updated 2 old tests. Commit: [`b204157`](file:///usr/local/google/home/ppardyak/Dogfood/sudoku)

- Allow users to make errors.  If they input the wrong number that conflicts with the numbers already established, it should be marked as an error.  However, if the new number does not violate any of the board constraints, it should be allowed.  Currently, the user is not allowed to make an error.  Only flag such numbers when the user clicks the "Check" button.
  - ✅ Done: Removed solution comparison from placeFinal — numbers are always placed. Conflict detection highlights row/col/box conflicts in amber. Mistakes counter no longer incremented on placement — only Check button flags errors against solution. 3 E2E tests added. Commit: [`a38022f`](file:///usr/local/google/home/ppardyak/Dogfood/sudoku)

---

## Agent-Extrapolated Requirements

<!-- Requirements the agent identified on its own, derived from existing work. -->
<!-- These follow the same TDD process: add requirement → test → implement → deploy. -->

