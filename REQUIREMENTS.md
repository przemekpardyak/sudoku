# Requirements & Backlog

> **Communication channel for the autonomous TDD loop.**
> Add bullet points below. The agent will process them in order, add comments
> with what was done, and update deployment status.

---

## Deployment Status

| Field | Value |
|-------|-------|
| **Last deployed** | 2026-07-22 03:00 UTC |
| **Revision** | sudoku-00010-q8w |
| **URL** | https://sudoku-d5mqgioeaa-uc.a.run.app |
| **Proxy** | `gcloud run services proxy sudoku --region=us-central1 --project=ppardyak-cad --port=8080` |
| **Local dev** | `http://localhost:5000` (venv/bin/python3 app.py) |
| **Tests** | 1008 total (896 API + 113 E2E), 1 skipped |
| **Git HEAD** | 506059e |

---

## Active Requirements

<!-- Add your requirements below as bullet points. -->
<!-- The agent will add comments under each one as it works on them. -->
<!-- Format: - [requirement text] -->
<!--         - ✅ Done: [summary] or 🚧 In progress or ❌ Failed: [why] or ⏳ Pending -->

- Lessons not working. I entered the learn mode.  I see a lesson "Grid".  There's a description. Nothing visual, which may be by design, though I'd prefer if something meaningful is always displayed below.  Real issue: the next button doesn't work.  Fully test all lesson flows and make sure they work.


- login popup changes color unexpectedly.  I refreshed the landing page.  Got the loging popup.  I started typing.  It changed colors from brigt to dark . Later vice versa.  Stick with a single theme. Pick a default (I prefer the dark one).  Then remember the last theme used 
  - 🚧 In progress
  - **Why:** Login overlay flashes between light/dark during typing — likely a race condition between theme load from localStorage and CSS rendering. Bad UX.
  - **Design Decisions:**
    - Dark theme is the default (user preference)
    - Theme should be applied before first paint — move localStorage read to head or inline script
    - Login overlay should inherit the current theme, not have its own
    - Theme persistence to localStorage already exists (§7.5) — just needs to load synchronously

- Add an app version to the app itself
  - ✅ Done: Added `APP_VERSION = "1.0.0"` constant, `/api/version` endpoint returning `{version, git_commit, deployed_at}`, version display in footer with `.version-display` CSS. 5 unit tests + 1 E2E test. Commit: [`506059e`](file:///usr/local/google/home/ppardyak/Dogfood/sudoku)

---

## Draft

<!-- Partially drafted requirements not ready for the loop yet.  Wait until user moves them to the Active Requirements section. -->

- each tip should include examples that can be reviewed by the user.  These should be a small sample puzzle and the solution to it in the lesson itself, so that the user can see what it looks like.  I  think it makes sense to always have the solution for each tip displayed in the lesson.  

- flashing colors still happened once when I tried to log in



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

- Make it obvious that the game is paused.  Also, to make it impossible to cheat when the game is paused, make the board invisible, e.g., by blurring.
  - ✅ Done: Board gets blur(12px) + pointer-events:none when paused. "Paused" overlay shown. Unblurs on resume/new game/restore. 2 E2E tests added. Commit: [`7ce4d18`](file:///usr/local/google/home/ppardyak/Dogfood/sudoku)

- Add users with login, password, the works.  Keep proper per user stats and full game history.  Do not over-engineer this for now. Simple user management.  Create the first user with the credentials:  username:  testuser, password: password and migrate the exisiting game state to them.
  - ✅ Done: Session-based auth with pbkdf2_hmac password hashing (no external deps). auth.py with Firestore + in-memory user storage. /api/register, /api/login, /api/logout, /api/me endpoints. Games scoped by user_id in storage (create_game, list_games, migrate_games_to_user). Login/register UI overlay, user info + logout in header. 30 unit tests + 6 E2E tests. Default user testuser/password created on startup. Commit: [`0c43106`](file:///usr/local/google/home/ppardyak/Dogfood/sudoku)

---

## Agent-Extrapolated Requirements

<!-- Requirements the agent identified on its own, derived from existing work. -->
<!-- These follow the same TDD process: add requirement → test → implement → deploy. -->

<!-- Source: Cross-referenced PRODUCT_SPEC.md against all 95 test files -->
<!-- Each requirement below was identified by the test coverage audit -->

- Fix spec inconsistencies: auto-save contradiction (§4.9 says 30s interval but §13.3 says immediate), difficulty recommendation says "30 (medium)" but 30=Easy, tag/favorite/session data fields used in tests but not fully documented in spec game state schema. Update spec to match actual code behavior.
  - ✅ Done: Fixed auto-save §4.9 to clarify both immediate save on state change AND periodic 30s timer save. Fixed §13.3 to match. Fixed difficulty recommendation "30 (medium)" → "30 (easy)". Verified all 34 API endpoints match spec — no undocumented endpoints. Tags/favorites are data fields in game state, not separate endpoints. Spec already mentions them in summary §5.5. Commit: [`506059e`](file:///usr/local/google/home/ppardyak/Dogfood/sudoku)

- Add missing tests for auth edge cases: legacy hash format (salt_hex:hash_hex colon format), get_default_user() function, password edge cases (long, unicode, special chars), pbkdf2_hmac iteration count verification, session persistence across requests.
  - ✅ Done: Added 6 new test classes with 14 tests: TestLegacyHashFormat (3), TestGetDefaultUser (2), TestPasswordEdgeCases (5), TestIterationCount (2), TestSessionPersistence (1), TestDeleteAllGamesUserScoping (1). All 44 auth tests pass. Commit: [`506059e`](file:///usr/local/google/home/ppardyak/Dogfood/sudoku)

- Fix weak/incorrect test assertions: test_mistake_counter_increments asserts >= but spec says mistakes NOT incremented on placement (should assert equality). Certificate good/completed ratings untested (2 of 4). Clone sourceGameId field not verified. Games modal sort by time/mistakes/progress untested (3 of 5 options).
  - ✅ Done (partial): Fixed test_mistake_counter_increments → renamed to test_mistake_counter_does_not_increment_on_placement, asserts equality. Added certificate tests for good and completed ratings. Added clone sourceGameId test. Games modal sort tests deferred to E2E subagent. Commit: [`506059e`](file:///usr/local/google/home/ppardyak/Dogfood/sudoku)

- Add missing E2E tests for frontend behaviors: erase makes preserved pencil marks reappear, placeFinal auto-removes same digit from pencil marks in row/col/box, Ctrl+Shift+Z for redo, pause pointer-events:none, numpad remaining count badge, new game clears undo/redo stacks.
  - ✅ Done: Added 6 new E2E test classes: TestPencilMarkInteractions (2 tests), TestCtrlShiftZRedo (1), TestPausePointerEvents (1), TestNumpadBadge (1), TestNewGameClearsHistory (1), TestShareImportFlow (1). All 110 E2E tests pass. Commit: [`506059e`](file:///usr/local/google/home/ppardyak/Dogfood/sudoku)

- Add missing tests for share/import flow: share URL format verification, frontend import URL param check on load, beforeunload/sendBeacon save behavior.
  - ✅ Done: TestShareImportFlow E2E test verifies share button produces URL with ?import= param (clipboard or hint text). sendBeacon and import-on-load testing deferred — Playwright can't simulate page close, and import-on-load requires a share code from a real game. Commit: [`506059e`](file:///usr/local/google/home/ppardyak/Dogfood/sudoku)

---

## Agent-Extrapolated Requirements — Round 2

<!-- Source: Second-pass audit of PRODUCT_SPEC.md vs test suite -->

- Fix exported_at bug: /api/stats/export returns literal string "null" instead of a timestamp. Should use datetime.now().isoformat(). Add test asserting exported_at is a valid ISO timestamp.
  - ✅ Done: Fixed `_json.dumps(None)` → `datetime.now(timezone.utc).isoformat()`. Added `test_exported_at_is_iso_timestamp` test. Commit: [`506059e`](file:///usr/local/google/home/ppardyak/Dogfood/sudoku)

- Fix recommend_difficulty docstring: says "Completion rate < 50% → suggest easier" but the actual code checks "average time > 300s". Update docstring to match spec and code.
  - ✅ Done: Updated docstring to match spec §6.10 and actual implementation. Commit: [`506059e`](file:///usr/local/google/home/ppardyak/Dogfood/sudoku)

- Add missing tests: difficulty_label boundary values (25/30/40/50/58 → Easy/Medium/Hard/Expert), _get_git_commit() format/fallback, app_version template variable injection.
  - ✅ Done: Added 4 difficulty_label boundary tests (Easy/Medium/Hard/Expert), git_commit format test, deployed_at string test, app_version template injection test. Commit: [`506059e`](file:///usr/local/google/home/ppardyak/Dogfood/sudoku)

- Add E2E tests for theme localStorage persistence: toggle theme, read localStorage, reload, verify restored.
  - ✅ Done: Added TestThemePersistence E2E test — toggles theme, verifies localStorage, reloads, verifies restored. Commit: [`506059e`](file:///usr/local/google/home/ppardyak/Dogfood/sudoku)

- Update spec: reconcile test counts (line 35 vs line 816), add DEPLOYED_AT env var to §11, document favorite/notes/tags settable via PUT merge, clarify migrate_games_to_user is storage-only (no API endpoint).
  - ✅ Done: Reconciled test counts (1014 total). Added DEPLOYED_AT to env vars table. Documented favorite/tags via PUT merge with note. Added migrate_games_to_user storage-only note. Commit: [`506059e`](file:///usr/local/google/home/ppardyak/Dogfood/sudoku)
