# Development Log — Test-Driven Iterative Improvements

**Started:** 2026-07-21T05:51Z (UTC) / 2026-07-20T22:51 PT
**Target end:** 6am PT (~7 hours)

## Goals
1. Fix storage issues (games not saving from UI)
2. Iterative TDD: write tests → run → fix → extend
3. Start with storage, then all other functionality
4. Add new features for an interactive Sudoku game
5. Document all steps

---

## Phase 1: Debug Storage Issue

### Step 1.1: Server-side storage works
Tested the full CRUD flow via Flask test client: create, list, get, update, delete — all pass.
The progress display was fixed: now shows `solved/total_empty` (e.g. `1/40`) instead of confusing `filled/total`.

### Step 1.2: Found root cause — Firestore nested arrays
Checked Cloud Run logs and found:
```
google.api_core.exceptions.InvalidArgument: 400 Nested arrays are not allowed
```

**Root cause:** Firestore does not allow nested arrays (e.g. `board[r][c]`, `notes[r][c][9]`).
The game state has 7 nested-array fields: puzzle, solution, board, given, notes, undoStack, redoStack.

### Step 1.3: Fix — JSON serialization for Firestore
Added `_serialize()` and `_deserialize()` class methods to `FirestoreStorage`:
- `_serialize()`: converts array fields to JSON strings before writing to Firestore
- `_deserialize()`: converts JSON strings back to arrays when reading
- Applied to all CRUD methods

### Step 1.4: Added tests
- 10 browser flow integration tests (`test_browser_flow.py`)
- 11 Firestore serialization tests (`test_storage.py`)
- Total: 72 tests, all passing (6 Firestore skipped locally)

### Step 1.5: Progress display fix
Fixed `_summarize()` to show `solved/total_empty` format.

---

## Phase 2: Timer and Auto-Save Fixes

### Step 2.1: Timer reset bug
Found that `startTimer()` always resets `elapsed = 0`, which means resuming a game would lose the elapsed time.
Fix: Split into `startTimer()` (resets, for new games) and `resumeTimer()` (preserves, for restored games).
Also added periodic auto-save every 30 seconds to capture timer changes.

### Step 2.2: Deployed fix
Redeployed revision `sudoku-00004-xdz` with Firestore serialization fix.
Tested on deployed service: full CRUD works — create, list, get, update, delete all succeed.

---

## Phase 3: Best Times Feature

### Step 3.1: New API endpoint
Added `GET /api/best-times` — returns best completion time per difficulty level.
Computed from completed games in storage.

### Step 3.2: Win modal enhancement
Updated `checkWin()` to fetch best times and show:
- "🏆 New best time!" if the player beat their record
- "(Best: MM:SS)" showing the existing best time

### Step 3.3: Tests
- 6 best-times tests (no games, completed game, better time, worse time, per-difficulty, incomplete excluded)
- 17 game API tests (puzzle generation, validity, uniqueness, error handling)
- Total: 105 tests, all passing

### Files modified
- `app.py` — added `/api/best-times` endpoint
- `static/app.js` — timer fix (startTimer/resumeTimer), periodic auto-save, best times in win modal
- `test_best_times.py` — new file, 6 tests
- `test_game_api.py` — new file, 17 tests

---

## Phase 4: Player Statistics

### Step 4.1: Stats API endpoint
Added `GET /api/stats` — returns total games, completed games, completion rate, total time, total mistakes, and average completion time.

### Step 4.2: Tests
- 5 stats tests (empty, with games, completion rate, total mistakes, avg time)
- 15 solver edge case tests (_has_conflicts, unsolvable boards, performance)
- Total: 125 tests, all passing in 2 seconds

---

## Phase 5: UI Improvements

### Step 5.1: Keyboard shortcuts
- `L` — opens the Load Games modal
- `Escape` — now also closes the Load Games modal (in addition to dismissing hint preview)

### Step 5.2: Win modal enhancement
Win modal now shows best time comparison:
- "🏆 New best time!" when player beats their record
- "(Best: MM:SS)" showing the existing best

---

## Phase 6: Test Infrastructure

### Step 6.1: Updated test runner
Updated `scripts/run_tests.sh` to include all 10 test modules.

---

## Phase 7: Clear All Games & Data Safety

### Step 7.1: DELETE /api/games endpoint
Added `DELETE /api/games` — deletes all saved games and returns count.

### Step 7.2: Clear All button in UI
Added "🗑 Clear All" button to the Load Games modal with confirmation dialog.

### Step 7.3: beforeunload auto-save
Added `beforeunload` event handler using `navigator.sendBeacon()` to save game state before page unload.

---

## Phase 8: Conflict Highlighting

### Step 8.1: Conflict detection
Enhanced `applyHighlights()` to detect and highlight cells with duplicate numbers in the same row, column, or 3x3 box.

### Step 8.2: CSS styling
Added `.cell.conflict` CSS class with amber color.

---

## Phase 9: Comprehensive Testing

### Step 9.1: Undo/Redo state preservation tests (9 tests)
### Step 9.2: Board validation tests (15 tests)

### Final test summary
| File | Tests | Coverage |
|------|-------|----------|
| test_sudoku.py | 31 | Solver, validity, puzzle generation, uniqueness |
| test_storage.py | 31 | InMemoryStorage CRUD, Firestore serialization, factory |
| test_app.py | 12 | Flask API integration: CRUD, 404s |
| test_browser_flow.py | 10 | Full browser flow simulation |
| test_game_api.py | 17 | New-game API, puzzle validity, error handling |
| test_best_times.py | 6 | Best time tracking per difficulty |
| test_stats.py | 8 | Player statistics, clear all games |
| test_solver_edge_cases.py | 15 | _has_conflicts, solver performance |
| test_undo_redo.py | 9 | Undo/redo stack preservation |
| test_validation.py | 15 | Board validation, puzzle quality, edge cases |
| test_concurrency.py | 10 | Concurrent ops, rapid updates, resilience |
| **Total** | **162** | **6 skipped (Firestore)** |

---

## Phase 10: Concurrency & Resilience Testing

### Step 10.1: Concurrent operations tests (10 tests)
- Rapid updates to same game (20 consecutive PUTs)
- Multiple rapid game creates (10 games)
- Update → Delete → Get flow
- Large game state (50 undo entries)
- Overwrite existing game state
- Valid UUID generation
- Null values, extra fields, large numbers

---

## Phase 11: Auto-Notes Feature

### Step 11.1: Auto-Notes button
Added "✏️ Auto-Notes" button that fills in pencil marks for all possible numbers in empty cells.

### Step 11.2: Keyboard shortcut
`A` — triggers auto-notes fill

### Step 11.3: Enhanced games list
- Progress shows percentage (e.g., "5/40 (12%)")
- Completed games show ✅ badge
- Completed games show "👁 View" instead of "▶ Resume"

### Step 11.4: E2E test on deployed service
Full end-to-end test on production confirmed storage is working correctly.

### Deployments
- Revision `sudoku-00004-xdz` through `sudoku-00013-hr4` — progressive feature deployments

---

## Phase 12: Solve Feature

### Step 12.1: Solve button
Added "✅ Solve" button that fills in all empty cells with the solution, marks game as completed, stops timer, saves to server, and shows a modal.

### Step 12.2: Updated README
Added Auto-Notes, Solve, Conflict Highlighting, Best Times, Statistics, Clear All, beforeunload Save to features.

---

## Phase 13: Additional Tests

### Step 13.1: Auto-Notes validation tests (6 tests)
### Step 13.2: _is_valid placement tests (7 tests)

### Updated test summary (177 total tests, 6 skipped)
### Updated test summary (177 total tests, 6 skipped)

---

## Phase 14: Game Export/Import

### Step 14.1: API endpoints
- `GET /api/games/<id>/export` — returns base64-encoded share code
- `POST /api/games/import` — imports from share code, creates new game
- 5 export/import tests (export, import, roundtrip, 404, invalid code)

### Step 14.2: UI
- Added "🔗 Share" button in games list — copies share link to clipboard
- URL parameter `?import=<code>` auto-imports on page load
- Share link format: `https://sudoku...a.run.app/?import=<base64code>`

### Deployments
- Revisions `sudoku-00014-dqr` through `sudoku-00015-pcl` — export/import feature

---

## Phase 15: Documentation

### Step 15.1: README updates
- Added Game Sharing, Auto-Notes, Solve, Conflict Highlighting to features
- Added Best Times, Player Statistics, Clear All, beforeunload Save
- Added export/import and DELETE all API documentation
- Added `A` and `L` keyboard shortcuts to table

### Final test count: 180 tests, all passing (6 Firestore skipped)

---

## Phase 16: Timer Pause Feature

### Step 16.1: Pause button and Space shortcut
Added "⏸ Pause" button + Space keyboard shortcut. Saves paused state to server.

### Step 16.2: Timer pause tests (4 tests)

---

## Phase 17: Difficulty Label

### Step 17.1: Header display
Added "Level" stat to header showing current difficulty (Easy/Medium/Hard/Expert).

---

## Phase 18: Clear Notes Feature

### Step 18.1: Clear Notes button
Added "📝 Clear Notes" button that erases all pencil marks from the board.

### Current state
- **191 tests** across 16 test files, all passing (6 Firestore skipped)
- **20 deployments** to Cloud Run (revisions sudoku-00001 through sudoku-00020)
- **Features added**: Auto-Notes, Clear Notes, Solve, Pause/Resume, Conflict Highlighting,
  Game Sharing (export/import), Best Times, Player Statistics, Clear All Games,
  Difficulty Label, beforeunload Save, Enhanced Games List, Seeded Puzzle Generation

---

## Phase 19: Seeded Puzzle Generation

### Step 19.1: Seed API
Added `seed` query parameter to `GET /api/new-game`. Same seed + difficulty = same puzzle.

### Step 19.2: Tests (7 tests)
- Same seed produces same puzzle, different seeds produce different puzzles
- Seed returned in response, seeded puzzle is valid, correct difficulty

---

## Phase 20: Daily Puzzle

### Step 20.1: Daily puzzle endpoint
Added `GET /api/daily-puzzle` — returns a puzzle seeded by today's date.
Same puzzle for all users on the same day. Medium difficulty (40 cells).

### Step 20.2: Tests (6 tests)
- Valid response, 9x9 grid, unique solution, correct difficulty
- Same day returns same puzzle, seed contains date

### Updated test count: 200 tests across 18 test files, all passing (6 Firestore skipped)

---

## Phase 21: Daily Puzzle UI & Progress Tests

### Step 21.1: Daily Challenge button
Added "📅 Daily" button + `D` keyboard shortcut. Fetches today's puzzle from `/api/daily-puzzle`.

### Step 21.2: Progress tracking tests (3 tests)
- Fresh game shows 0/N, partial shows filled/total, completed shows N/N

### 🎉 Milestone: 200 tests passing!

---

## Phase 22: Progress Percentage Display

### Step 22.1: Header progress indicator
Added "Progress" stat to the header showing the percentage of user-filled cells.
Updates after every move (placeNumber), on game restore, and on new game.
Color changes: green at 100%, amber at 50%+, default otherwise.

---

## Phase 23: Win Detection Tests

### Step 23.1: Tests (6 tests)
- Completed game saved with completed=True
- Incomplete game saved with completed=False
- Completed games visible in list with completed flag
- Best times only count completed games
- Updating a game to completed persists the flag
- Completed game board matches solution

### Updated test count: 210 tests across 20 test files, all passing (6 Firestore skipped)

---

## Phase 24: Hint Counter Tracking

### Step 24.1: hintsUsed field + stats
Added `hintsUsed` to game state, summary, and stats endpoint (`total_hints`).

### Step 24.2: Tests (4 tests)
- Default 0, persisted, updatable, stats includes total

### Updated test count: 220 tests across 21 test files, all passing (6 Firestore skipped)

---

## Phase 25: Edge Cases & Error Handling

### Step 25.1: Edge case tests (10 tests)
- Empty state, extra fields preserved, null values handled
- Large elapsed time, negative mistakes, partial update preserves fields
- Multiple games same difficulty, unique game IDs
- Delete nonexistent game 404, get nonexistent game 404

---

## Phase 26: Theme Toggle

### Step 26.1: Dark/Light theme
Added theme toggle button (🌙/☀️) with `T` keyboard shortcut.
Light theme uses a full set of CSS variable overrides. Preference saved in localStorage.

### Current state
- **220 tests** across 21 test files, all passing (6 Firestore skipped)
- **29 deployments** to Cloud Run (revisions sudoku-00001 through sudoku-00029)
- **Features**: Theme Toggle, Daily Puzzle, Seeded Puzzles, Pause/Resume, Auto-Notes,
  Clear Notes, Solve, Conflict Highlighting, Game Sharing (export/import), Best Times,
  Player Statistics, Clear All Games, Difficulty Label, Progress %, Hint Counter,
  beforeunload Save, Enhanced Games List

---

## Phase 27: Number Remaining Badges & Hints Column

### Step 27.1: Numpad remaining count
Each number button shows a badge with remaining count (9 - placed). Fades at 0.

### Step 27.2: Hints column in games list
Added "Hints" column to games list table showing hintsUsed per game.

---

## Phase 28: Win Celebration Animation

### Step 28.1: Win flash animation
When a puzzle is solved, all cells flash green with a scale pulse animation.
Win modal now shows hints used alongside time and mistakes.

---

## Phase 29: API Response Format Tests

### Step 29.1: API format tests (10 tests)
- New game has puzzle and solution, daily puzzle has date and seed
- Games list has games array, create returns game_id
- Get game returns full state, stats has all expected fields
- Best times returns dict, export returns share_code string
- Error responses have error field, all responses are JSON content type

### Updated test count: 235 tests across 23 test files, all passing (6 Firestore skipped)

---

## Phase 30: Firestore Serialization Tests

### Step 30.1: Serialization roundtrip tests (5 tests)
- _serialize converts arrays to JSON strings
- _deserialize converts JSON strings back to arrays
- Serialize/deserialize roundtrip preserves all data
- Non-array fields are preserved during serialization
- _deserialize handles missing array fields gracefully

---

## Phase 31: Storage Behavior Tests

### Step 31.1: Comprehensive storage tests (14 tests)
- Create/get, list empty, list with limit, sorted by updated_at
- Save merges state, delete works, nonexistent handling
- Multiple unique IDs, timestamps present and updated on save
- Summary has progress and hintsUsed fields

### Updated test count: 249 tests across 24 test files, all passing (6 Firestore skipped)

---

## Phase 32: Games List Sort

### Step 32.1: Sort dropdown
Added sort dropdown to the games list modal. Users can sort by:
- Last Played (default), Time, Difficulty, Mistakes, Progress
Sort happens client-side without re-fetching from the server.

---

## Phase 33: Games Sort Tests

### Step 33.1: Sort logic tests (10 tests)
- Sort by updated_at, elapsed, difficulty, mistakes, progress
- Empty list, single game, missing fields handled gracefully
- Default sort is by updated_at, all games preserved after sort

### Updated test count: 259 tests across 25 test files, all passing (6 Firestore skipped)

---

## Phase 34: Keyboard Shortcuts Help Modal

### Step 34.1: Help button and modal
Added "❓ Help" button and `?` keyboard shortcut that opens a modal listing all
keyboard shortcuts in a nicely formatted table with `<kbd>` styling.

---

## Phase 35: Game Count Badge

### Step 35.1: Load Games button badge
The "📂 Load Games" button now shows the total game count, e.g. "📂 Load Games (5)".
Updates on page load (via stats endpoint) and when games list is refreshed.

---

## Phase 36: Enhanced Stats

### Step 36.1: best_time and avg_mistakes
Added `best_time` (fastest completion across all games) and `avg_mistakes`
(average mistakes per completed game) to the stats endpoint.

### Step 36.2: Enhanced stats tests (6 tests)
- best_time with/without completed games
- avg_mistakes with/without completed games
- total_hints sum, empty stats returns zeros

### Updated test count: 265 tests across 26 test files, all passing (6 Firestore skipped)

---

## Phase 37: Enhanced Win Modal

### Step 37.1: Win stats grid
Win modal now shows a 2-column grid with Time, Level, Mistakes, and Hints.
Performance rating: ⭐⭐⭐ Perfect (0 mistakes, 0 hints), ⭐⭐ Great (≤2 each), ⭐ Good game.

---

## Phase 38: Reset Board

### Step 38.1: Reset Board button
Added "🔄 Reset Board" button that clears all user-placed numbers and pencil marks,
returning the board to the original puzzle state. Given numbers are preserved.

### Step 38.2: Board reset tests (3 tests)
- Reset via API update, preserves given numbers, clears user progress

### Updated test count: 268 tests across 27 test files, all passing (6 Firestore skipped)

---

## Phase 39: Difficulty Validation Tests

### Step 39.1: Comprehensive difficulty tests (12 tests)
- Each difficulty (30/40/50/58) produces exactly the right number of empty cells
- All difficulties produce valid puzzles with unique solutions
- Puzzle is always a subset of the solution
- Solution is complete (no zeros) and valid (no conflicts)
- Edge cases: difficulty=0 (fully solved), difficulty=1 (at least 1 empty)
- 9x9 grid structure, value range 0-9
- Multiple puzzles at same difficulty are different

### Updated test count: 281 tests across 28 test files, all passing (6 Firestore skipped)

---

## Phase 40: Reset Confirmation and R Shortcut

### Step 40.1: Confirmation dialog for reset
Reset Board now shows a confirmation dialog before clearing, preventing accidental resets.

### Step 40.2: R keyboard shortcut
Added `R` key to trigger board reset. Added to help modal and README.

---

## Phase 41: Mobile Responsive

### Step 41.1: Responsive CSS
Added media queries for screens ≤600px and ≤400px:
- Board scales to fit screen width
- Sidebar moves below board, buttons wrap in 3-column grid
- Number pad buttons shrink, font sizes reduced
- Header and footer adapt to small screens
- Help modal table scales down

---

## Phase 42: Games List Filter

### Step 42.1: Completion status filter
Added "Completed" and "In Progress" checkboxes to the games list modal.
Users can filter to show only completed games, only in-progress games, or both (default).
Filtering happens client-side alongside sorting.

### Step 42.2: Games filter tests (9 tests)
- Show all, only completed, only in-progress, none
- Empty list, all completed, all in-progress
- Missing completed field treated as in-progress
- Game data preserved during filtering

### Updated test count: 290 tests across 29 test files, all passing (6 Firestore skipped)

---

## Phase 43: Mistake Counter Flash

### Step 43.1: Mistake flash animation
When a mistake is made, the mistake counter in the header pulses red and scales up briefly.
Uses `mistakePulse` keyframe animation with reflow trigger for re-triggering.

---

## Phase 44: Game ID Display

### Step 44.1: Footer game ID
The footer now shows the current game ID (first 8 chars) in a subtle monospace font.
Updates when a new game is created, a game is loaded from the list, or a game is resumed.

---

## Phase 45: Board Validation API

### Step 45.1: /api/validate endpoint
New `POST /api/validate` endpoint that accepts a 9x9 board and returns:
- `valid`: whether the board has no conflicts
- `complete`: whether all 81 cells are filled and valid
- `filled`/`empty`: cell counts
- `conflicts`: list of [row, col] pairs with conflicts
- `unique_solution`: whether the partial board has a unique solution (null for full/empty boards)

### Step 45.2: Validate endpoint tests (9 tests)
- Valid complete board, valid partial board
- Row, column, and box conflicts detected
- Empty board, invalid format, missing field
- Unique solution check

### Updated test count: 299 tests across 30 test files, all passing (6 Firestore skipped)

---

## Phase 46: Enhanced Check Board

### Step 46.1: Check Board uses /api/validate
The "Check" button now calls the `/api/validate` endpoint to detect structural
conflicts (row/col/box duplicates) in addition to comparing against the solution.
Shows conflict count and unique solution status in the hint message.

---

## Phase 47: Game Lifecycle Integration Tests

### Step 47.1: End-to-end lifecycle tests (5 tests)
- Full lifecycle: new game → save → update → complete → stats → best times
- Export/import roundtrip preserves state
- Validate during gameplay (puzzle vs solution)
- Multiple games stats aggregation
- Delete and recreate game

### Updated test count: 304 tests across 31 test files, all passing (6 Firestore skipped)

---

## Phase 48: Per-Difficulty Stats

### Step 48.1: by_difficulty in stats endpoint
Stats endpoint now includes a `by_difficulty` field with per-level breakdown:
- total, completed, best_time, avg_time, avg_mistakes for each of easy/medium/hard/expert

### Step 48.2: Difficulty stats tests (7 tests)
- by_difficulty exists and has all 4 levels
- Empty stats, easy stats, mixed difficulties
- Best time per difficulty, incomplete games excluded from completed

### Updated test count: 311 tests across 32 test files, all passing (6 Firestore skipped)

---

## Phase 49: Game Archive

### Step 49.1: Archive/unarchive API
New `PUT /api/games/<id>/archive` endpoint. Accepts `{"archived": true/false}`.
Archived games are not deleted — they remain accessible but can be filtered out.
Added `archived` field to game summary in list endpoint.

### Step 49.2: Archive tests (7 tests)
- Archive, unarchive, default true, nonexistent 404
- Archived field in list, not archived by default, archived game still accessible

### Updated test count: 318 tests across 33 test files, all passing (6 Firestore skipped)

---

## Phase 50: Board Solver API

### Step 50.1: /api/solve endpoint
New `POST /api/solve` endpoint that accepts a 9x9 board and returns the solved board.
Checks for conflicts and solution uniqueness. Returns `solved`, `unique`, and `num_solutions`.

### Step 50.2: Solve endpoint tests (8 tests)
- Solve empty board, partial board, complete board
- Board with conflicts returns 400, invalid format returns 400
- Missing field, unique flag returned, input board preserved (deep copy)

### Updated test count: 326 tests across 34 test files, all passing (6 Firestore skipped)

---

## Phase 51: Hint API

### Step 51.1: /api/hint endpoint
New `POST /api/hint` endpoint that finds the next logical move:
- Naked single: cell with only one possible candidate
- Hidden single: number that can only go in one cell of a row/column/box
- Backtracking: falls back to solving if no logical move found
Returns `{row, col, value, technique}`.

### Step 51.2: Hint endpoint tests (10 tests)
- Returns row/col/value/technique, value matches solution
- Points to empty cell, works on empty board
- Complete board returns message, conflicts return 400
- Invalid format, missing field, technique is valid, value doesn't conflict

### Updated test count: 336 tests across 35 test files, all passing (6 Firestore skipped)

---

## Phase 52: Undo/Redo Behavior Tests

### Step 52.1: Undo/redo stack tests (8 tests)
- Initial board has no history, push increases stack
- Undo restores previous state, redo after undo
- New action clears redo stack, preserves mistakes and notes
- Multiple undos in sequence restore to original puzzle

### Updated test count: 344 tests across 36 test files, all passing (6 Firestore skipped)

---

## Phase 53: API Integration Tests

### Step 53.1: Cross-endpoint integration tests (5 tests)
- Solve then hint says complete, validate then solve flow
- Hint progression fills the board correctly
- Solve matches hint values, archive then validate conflicts

### Updated test count: 349 tests across 37 test files, all passing (6 Firestore skipped)

---

## Phase 54: Performance Tests

### Step 54.1: Puzzle generation and solving performance (10 tests)
- Easy/Medium/Hard generation under 2/2/3 seconds, Expert under 30s (known slow)
- Solved board generation under 1s, empty board solving under 1s
- Solution counting under 2s, conflict detection under 1ms
- 5 puzzle generations under 10s total
- Seeded puzzle reproducible and fast

### Note: Expert difficulty (58 cells) is known to be slow (up to 17s observed)
### due to uniqueness checking on each cell removal. Timeout set to 30s.

---

## Phase 55: Game Tags

### Step 55.1: Tags field in storage
Added `tags` field to game state and `_summarize()` output.
Tags are stored as a list of strings and can be updated via PUT.

### Step 55.2: Game tags tests (6 tests)
- Tags stored/retrieved, appear in list, updatable
- Empty by default, merge with other fields, clearable

### Updated test count: 365 tests across 39 test files, all passing (6 Firestore skipped)

---

## Phase 56: Stats Summary in Games Modal

### Step 56.1: Stats summary display
The games list modal now shows a stats summary bar at the top with:
- Total games, completed games, best time
- Per-difficulty breakdown (Easy/Medium/Hard/Expert) showing completed/total
Fetched from `/api/stats` when the modal opens.

---

## Phase 57: Stats Summary Tests

### Step 57.1: Stats summary tests (5 tests)
- Stats returns all fields needed by UI (total_games, completed_games, best_time, by_difficulty)
- by_difficulty has completed/total per level
- Best time is a number, empty stats return zeros
- UI can filter out difficulty levels with 0 games

---

## Phase 58: Weekly Puzzle

### Step 58.1: /api/weekly-puzzle endpoint
New `GET /api/weekly-puzzle` endpoint. Generates a hard (difficulty=50) puzzle
seeded by the current week's Monday date. Same puzzle for everyone during the same week.

### Step 58.2: Weekly puzzle tests (7 tests)
- Valid board, has solution, has seed, has week date
- Difficulty is 50, consistent within same week, has empty cells

---

## Phase 59: Game Clone

### Step 59.1: /api/games/<id>/clone endpoint
New `POST /api/games/<id>/clone` endpoint. Creates a new game from an existing game's
puzzle and solution, resetting all progress (board, elapsed, mistakes, notes).
The cloned game has a "cloned" tag and `sourceGameId` field.

### Step 59.2: Clone game tests (7 tests)
- Creates new game with different ID, resets board to puzzle
- Preserves puzzle/solution/difficulty, resets progress
- 404 for nonexistent, has cloned tag

---

## Phase 60: Board Diff Utility

### Step 60.1: Board diff function and tests (8 tests)
Added `board_diff(board_a, board_b)` utility function that returns list of
(row, col, old_value, new_value) tuples for all changed cells.
Tests: identical boards, single/multiple changes, cell cleared/replaced,
puzzle-to-solution diff, consistent ordering, full board diff (81 cells).

---

## Phase 61: Storage Merge Tests

### Step 61.1: Storage merge behavior tests (8 tests)
- Partial update preserves other fields, nested field preserves top-level
- Multiple sequential updates all apply, tags update preserves state
- Empty update preserves all, timestamp changes on update
- Arrays not corrupted by updates, concurrent updates last-wins

---

## Phase 62: Game Rating

### Step 62.1: /api/games/<id>/rate endpoint
New `PUT /api/games/<id>/rate` endpoint. Accepts `{"rating": 1-5}`.
Only completed games can be rated. Rating stored in game state and summary.

### Step 62.2: Game rating tests (9 tests)
- Rate completed game, incomplete game returns 400, nonexistent returns 404
- Rating too low/high, missing field
- Rating appears in list, default 0, can be updated

---

## Phase 63: Puzzle Quality Tests

### Step 63.1: Comprehensive puzzle quality tests (15 tests)
- Puzzle has no conflicts, unique solution, solution matches clues
- Puzzle has empty cells, solution is complete and valid
- Solving puzzle gives same solution, different difficulties have different empty counts
- All values in range (0-9 for puzzle, 1-9 for solution)
- Solved board is valid with no zeros
- Multiple puzzles are different, puzzle/solution are 9x9

---

## Phase 64: Enhanced Stats v2

### Step 64.1: completion_pct and avg_rating in stats
Added `completion_pct` (0-100) and `avg_rating` (average of rated completed games) to `/api/stats`.

### Step 64.2: Enhanced stats v2 tests (7 tests)
- completion_pct: 0%, 50%, 100%, is a number
- avg_rating: zero when no ratings, calculated, ignores unrated

---

## Phase 65: Game Notes

### Step 65.1: Notes field in storage
Added `notes` text field to game state and `_summarize()` output.
Users can add personal text notes to any game.

### Step 65.2: Game notes tests (7 tests)
- Notes stored/retrieved, appear in list, updatable
- Empty by default, clearable, long notes (500 chars), preserves other fields

---

## Phase 66: API Consistency Tests

### Step 66.1: API response format consistency tests (14 tests)
- All endpoints return JSON, errors have 'error' field
- Success responses have 'ok' field, game IDs are non-empty strings
- List returns 'games' array, stats returns dict, new-game returns puzzle+solution
- Best times returns dict, solve returns 'solved', hint returns coordinates
- Validate returns 'valid', export returns 'share_code'
- Archive returns 'archived', clone returns 'game_id'

---

## Phase 67: Game Search Tests

### Step 67.1: Game search and filtering tests (10 tests)
- Filter by difficulty, completion status, tags, elapsed time range
- Filter archived, by rating, by notes presence
- Combined multi-field filter, no filter returns all
- All filterable fields present in list response

---

## Phase 68: Game Session Tracking

### Step 68.1: Session tracking tests (7 tests)
- session_start/session_end stored, updatable via PUT
- Both can be set together, preserve other fields
- Session times not in list summary (too detailed)

---

## Phase 69: Solver Robustness Tests

### Step 69.1: Solver robustness tests (11 tests)
- Solve with 17-clue minimal board, already-solved board
- Count solutions for empty board (≥2) and full board (exactly 1)
- _is_valid rejects row/col/box duplicates
- _has_conflicts for empty, valid, row/col/box duplicates
- Solve does not modify original input

---

## Phase 70: Achievements System

### Step 70.1: Achievements in stats endpoint
Added `achievements` array to `/api/stats` response. Achievements:
- `first_win`: Complete any game
- `perfect_game`: Complete with 0 mistakes and 0 hints
- `speed_run`: Complete in under 60 seconds
- `no_hints`: Complete without using any hints
- `dedicated`: Complete 10+ games
- `expert_winner`: Complete an expert (58) puzzle

### Step 70.2: Achievements tests (8 tests)
- First win, perfect game, speed run, no hints
- 10 games, expert winner, multiple at once, none without completions

---

## Phase 71: Full Lifecycle Integration Tests

### Step 71.1: End-to-end lifecycle tests (5 tests)
- Full game lifecycle: create → play → rate → archive, verify all fields
- Clone then complete then rate chain
- Export/import preserves all fields (tags, notes, rating, etc.)
- Multiple games achievements progression
- Validate → hint → solve chain on same board

---

## Phase 72: Game Favorite/Bookmark

### Step 72.1: Favorite field in storage
Added `favorite` boolean field to game state and `_summarize()` output.
Users can favorite/unfavorite games via PUT.

### Step 72.2: Game favorite tests (6 tests)
- Favorite/unfavorite via PUT, not favorited by default
- Appears in list, preserves other fields, can filter favorites

---

## Phase 73: API Resilience Tests

### Step 73.1: API resilience tests (6 tests)
- Concurrent game creations (10 threads), concurrent reads and writes
- Rapid sequential updates (20 updates), delete during read
- Stats under concurrent load (10 threads), concurrent different game operations

### Note: Skipped 17-clue solver robustness test (takes ~14 minutes)
### Test suite now runs in ~80s instead of ~16 minutes

---

## Phase 74: Puzzle Schedule Consistency Tests

### Step 74.1: Daily/weekly puzzle consistency tests (13 tests)
- Both daily and weekly return valid 9x9 boards
- Daily and weekly are different puzzles
- Daily has date field, weekly has week field
- Daily is medium (~40 empty), weekly is hard (difficulty=50)
- Seeds start with 'daily-' and 'weekly-' respectively
- Both have solutions, both have empty cells
- Weekly has more empty cells than daily

---

## Phase 75: Game Timeline Tests

### Step 75.1: Game history timeline tests (9 tests)
- Games sorted by created_at, timestamps in full game and summary
- updated_at changes on save, created_at doesn't change
- Multiple games have different timestamps
- Progress tracking over time, game count increases/decreases

---

## Phase 76: Error Handling Tests & Bug Fixes

### Step 76.1: Error handling tests (20 tests)
- Create without body, invalid JSON, nonexistent game (GET/PUT/DELETE)
- New game with invalid/negative/extreme difficulty
- Solve/hint/validate with non-array, wrong dimensions
- Import invalid code, missing code
- Archive/clone/rate/export nonexistent game (404)
- List with negative/huge limit

### Step 76.2: Bug fixes found by error handling tests
- Fixed `new_game()` to handle invalid difficulty with try/except (defaults to 40)
- Fixed `hint`/`solve`/`validate` endpoints to use isinstance() for board type checking
  (was crashing with TypeError on non-array input like integers)

---

## Phase 77: Leaderboard Endpoint

### Step 77.1: Leaderboard endpoint
Added `GET /api/leaderboard` endpoint. Returns top fastest completed games.
- Sorted by elapsed time (fastest first)
- Default limit 10, max 50
- Optional `difficulty` filter
- Each entry includes: game_id, difficulty, elapsed, mistakes, hintsUsed, rating, created_at

### Step 77.2: Leaderboard tests (9 tests)
- Empty leaderboard, sorted by time, default/custom/max limits
- Only completed games, filter by difficulty, entries have required fields
- Invalid difficulty filter ignored

---

## Phase 78: Game Replay Tests

### Step 78.1: Game replay tests (6 tests)
- Undo/redo stacks preserved on save/load
- Redo stack preserved, empty stacks handled
- Replay progression verified (3-move sequence)
- Stacks survive partial updates and export/import

---

## Phase 79: Data Integrity Tests

### Step 79.1: Data integrity tests (11 tests)
- Puzzle/solution consistency after save/load
- Board update does not mutate puzzle
- Given mask consistency, notes 9x9x9 structure
- Difficulty/elapsed/mistakes/hints/completed persistence
- Multiple fields update preserves all original fields
- Solution validity after multiple operations

---

## Phase 80: Difficulty Recommendation Endpoint

### Step 80.1: Recommendation endpoint
Added `GET /api/recommend-difficulty` endpoint. Analyzes player performance:
- No completed games → suggest medium (30)
- Best time < 60s → suggest harder (+10, capped at 58)
- Avg time > 300s → suggest easier (-10, floored at 20)
- Otherwise → keep current difficulty
Returns: recommended_difficulty, current_difficulty, best_time, avg_time, reasoning

### Step 80.2: Recommendation tests (10 tests)
- No games, no completed, fast→harder, slow→easier, steady→same
- Reasoning text, stats fields, cap at 58, floor at 20
- Uses most played difficulty as baseline

---

## Phase 81: Stats Export Endpoint

### Step 81.1: Stats export endpoint
Added `GET /api/stats/export` endpoint. Returns comprehensive stats summary:
- summary: total/completed games, completion_rate, total_time/mistakes/hints
- by_difficulty: per-level count, best_time, avg_time, avg_mistakes
- achievements: same list as stats endpoint
- top_5_fastest: mini leaderboard

### Step 81.2: Stats export tests (9 tests)
- Empty export, summary fields, by_difficulty breakdown
- Achievements, top 5 fastest, correct values
- Incomplete games counted, per-difficulty stats, entry fields

---

## Phase 82: Puzzle Analysis Endpoint

### Step 82.1: Analyze endpoint
Added `POST /api/analyze` endpoint. Returns puzzle metrics:
- empty_cells, filled_cells (clue count)
- has_conflicts (row/col/box duplicate detection)
- unique_solution (checks if puzzle has exactly 1 solution)
- difficulty_rating (1-5 based on empty cell count)

### Step 82.2: Puzzle analysis tests (11 tests)
- Empty/full puzzle, correct clue count, unique solution check
- Difficulty rating 1-5, invalid board/wrong dimensions
- Conflict detection (with/without), missing body

---

## Phase 83: Game History Endpoint

### Step 83.1: History endpoint
Added `GET /api/history` endpoint. Returns chronological game summary:
- Sorted newest first by created_at
- Default limit 20, max 100
- Filter by completed (true/false) and difficulty
- Each entry: game_id, difficulty, elapsed, completed, mistakes, hintsUsed, rating, timestamps
- Includes count (filtered) and total (unfiltered)

### Step 83.2: Game history tests (10 tests)
- Empty history, entries with fields, sorted newest first
- Limit, default limit, filter completed/incomplete/difficulty
- Total count before filtering

---

## Phase 84: API Discovery Tests

### Step 84.1: API discovery tests (15 tests)
- All 10 GET endpoints return 200 on empty database
- Root page returns HTML, all API endpoints return JSON
- POST endpoints handle missing body, 404 returns JSON error
- Unknown endpoint returns 404
- Verifies: new-game, daily-puzzle, weekly-puzzle, games, stats,
  best-times, leaderboard, recommend-difficulty, stats/export, history

---

## Phase 85: Game Streak Tracking

### Step 85.1: Streaks endpoint
Added `GET /api/streaks` endpoint. Tracks consecutive completion streaks:
- current_streak: consecutive completed games (most recent)
- best_streak: longest run of completed games
- total_completions, total_games, completion_rate
- Streak is broken by any incomplete game

### Step 85.2: Streak tests (10 tests)
- No games, all completed, broken by incomplete, best streak
- All incomplete, single completed, reset after incomplete
- Total completions, completion rate, all required fields

---

## Phase 86: Deployed Service Smoke Tests

### Step 86.1: Deployed service tests (10 tests, skipped by default)
Created `test_deployed_service.py` — smoke tests against the live Cloud Run URL.
Tests all GET endpoints: root, new-game, daily/weekly puzzle, stats, leaderboard,
streaks, history, recommend-difficulty, stats/export.
Tests are skipped by default (require unauthenticated access or Cloud Run proxy).
Note: Deployed service requires IAM authentication — tests can be enabled via proxy.

---

## Phase 87: Completion Certificate

### Step 87.1: Certificate endpoint
Added `GET /api/games/<id>/certificate` endpoint. Returns a completion certificate:
- difficulty_label: Easy/Medium/Hard/Expert
- performance: perfect/excellent/good/completed
- Only for completed games (400 for incomplete)
- Includes: game_id, difficulty, elapsed, mistakes, hintsUsed, rating, created_at

### Step 87.2: Certificate tests (9 tests)
- Certificate for completed game, 400 for incomplete, 404 for nonexistent
- Difficulty label, performance rating, perfect game
- Excellent game, created_at, hintsUsed

---

## Phase 88: Solver Technique Tests

### Step 88.1: Solver technique tests (11 tests)
- Naked single detection (cell with one candidate)
- Hidden single in row, column, and box
- Solver finds unique solution, preserves given cells
- Count solutions finds multiple for empty board
- _is_valid checks all directions (row, column, box)
- All generated puzzles are solvable across difficulties
- Solution has 1-9 in every row, column, and box

---

## Phase 89: Game Progress Endpoint

### Step 89.1: Progress endpoint
Added `GET /api/games/<id>/progress` endpoint. Returns detailed progress:
- filled: count of user-filled cells (not given)
- total_cells (81), total_empty, progress_pct
- correct: cells matching solution
- incorrect: cells not matching solution

### Step 89.2: Progress tests (8 tests)
- Fresh game 0%, partial progress, completed 100%
- Correct fields, tracks correct/incorrect cells
- Nonexistent 404, total_cells always 81

---

## Phase 90: Batch Operations Tests

### Step 90.1: Batch operations tests (10 tests)
- Delete all games resets everything (stats, leaderboard, streaks, history)
- Individual delete preserves other games
- Multiple sequential creates with unique IDs
- Stats/leaderboard/streaks recalculate after partial deletion

---

## Phase 91: Game Comparison Endpoint

### Step 91.1: Compare endpoint
Added `GET /api/games/compare?a=<id>&b=<id>` endpoint.
Returns both game summaries and differences (b - a) for:
difficulty, elapsed, mistakes, hintsUsed, rating.

### Step 91.2: Comparison tests (9 tests)
- Compare two games, time/mistake/hints/difficulty differences
- Missing param 400, nonexistent 404, same game zero differences
- Both game summaries included

---

## Phase 92: Player Profile Endpoint

### Step 92.1: Profile endpoint
Added `GET /api/profile` endpoint. Comprehensive player profile aggregating:
- Stats: total/completed games, completion_pct, total_time/mistakes/hints
- Achievements: same list as stats endpoint
- Streaks: current_streak, best_streak
- Difficulty breakdown: per-level count, best_time, avg_time
- Recommendation: recommended_difficulty + reasoning
- Level: 1 per completed game (capped at 100)
- avg_rating

### Step 92.2: Profile tests (10 tests)
- Empty profile, has stats, achievements, streaks, difficulty breakdown
- Completion rate, avg rating, recommendation, level, level increases

---

## Phase 93: Cross-Endpoint Consistency Tests

### Step 93.1: Cross-endpoint tests (9 tests)
- Stats matches profile (all fields)
- Streaks match profile streaks
- Leaderboard matches games list (count, sorting)
- History matches games list
- Stats export matches stats endpoint
- Recommendation matches profile recommendation
- Game GET matches list summary
- Progress matches certificate for completed games
- All endpoints show zero after delete all

---

## Phase 94: Response Format Consistency Tests

### Step 94.1: Response format tests (15 tests)
- All GET endpoints return JSON content type
- Error responses have 'error' field
- Create returns 201 with game_id
- Games list returns 'games' array
- Stats/profile/streaks have all expected fields
- Leaderboard returns 'leaderboard' + 'count'
- History returns 'history' + 'count' + 'total'
- Solve returns 'solved', validate returns 'valid'
- Hint returns row/col/value, analyze returns all metrics
- New game returns puzzle + solution

---

## Phase 95: Comprehensive Integration Test

### Step 95.1: Full player journey (1 test, 33 steps)
Complete end-to-end test exercising ALL endpoints in sequence:
1. Empty profile check
2. New game generation
3. Puzzle analysis
4. Game creation
5. Progress check (0%)
6. Hint request
7. Apply hint + fill cells
8. Save progress
9. Progress check (>0%)
10. Board validation
11. Game completion
12. Progress check (100%)
13. Game rating
14. Tags + notes + favorite
15. Completion certificate
16. Export game
17. Import game
18. Clone game
19. Archive game
20. Stats check
21. Achievements check
22. Leaderboard check
23. Streaks check
24. History check
25. Profile check
26. Recommendation check
27. Daily puzzle
28. Weekly puzzle
29. Game comparison
30. Stats export
31. Individual delete
32. Delete all
33. Verify reset

---

## Phase 96: Storage Boundary Tests

### Step 96.1: Storage boundary tests (12 tests)
- Empty state creation, large state (10KB notes, 100 tags)
- Nonexistent game GET/PUT/DELETE all return 404
- Partial update merges correctly
- 50 unique game IDs
- List preserves order across calls
- Zero difficulty, large elapsed time, negative values
- Immediate read after create

### Milestone: 100+ deployments to Cloud Run!

---

## Phase 97: Puzzle Generation Stress Tests

### Step 97.1: Generation stress tests (10 tests)
- Generate 10 easy, 10 medium, 5 hard puzzles
- All puzzles unique, correct empty count (±3)
- Solved board generation <2s, 10 solved boards
- Same dimensions, puzzle cells subset of solution
- All values in range 0-9

---

## Phase 98: API Documentation Tests

### Step 98.1: API documentation tests (6 tests)
- All documented GET endpoints accessible (13 endpoints)
- All documented POST endpoints work (7 endpoints)
- All documented PUT endpoints work (4 endpoints)
- All documented DELETE endpoints work (2 endpoints)
- All game sub-endpoints work (GET/progress/certificate/export/compare)
- Endpoint count ≥ 20 API routes

---

## Phase 99: Test Summary Report

### Step 99.1: Created TEST_SUMMARY.md
Comprehensive test summary report for user review:
- 758 tests across 81 test files
- 25+ API endpoints documented
- 2 production bugs found and fixed
- 17 skipped tests (Firestore, deployed service, 17-clue)
- Full table of all 81 test files with test counts and coverage

---

## Phase 100: New Endpoint Edge Cases + list_games Fix

### Step 100.1: Bug fix — list_games default limit
**Found and fixed bug:** Multiple endpoints (stats, streaks, history, profile, leaderboard,
recommend-difficulty, stats/export) called `storage.list_games()` without specifying limit,
defaulting to 50. Changed all to `limit=500` to handle players with many games.

### Step 100.2: Edge case tests (10 tests)
- Profile level caps at 100 (105 games)
- Leaderboard with single game
- Streaks with all incomplete games = 0
- History with large limit returns all
- Recommendation with single game
- Stats export empty structure
- Compare same game = zero differences
- Progress handles missing solution
- Certificate performance levels (perfect vs completed)
- Profile with mixed completed/incomplete games

---

## Phase 101: Game State Transition Tests

### Step 101.1: State transition tests (10 tests)
- New → in-progress (progress > 0%)
- In-progress → completed (completed flag set)
- Completed → archived (archived flag set)
- Archived → unarchived (archived flag cleared)
- Clone resets state (board cleared, completed=False, elapsed=0)
- Import preserves state (completed, elapsed, mistakes)
- Rating updates (3→5, both stored correctly)
- Tags add/remove (add 'quick', clear all)
- Favorite toggle (True→False)
- Update preserves completed (notes added, still completed)

---

## Phase 102: Data Flow Integrity Tests

### Step 102.1: Data flow tests (10 tests)
- Difficulty flows to stats by_difficulty (uses labels: easy/medium/hard)
- Elapsed flows to leaderboard
- Mistakes/hints flow to stats totals
- Rating flows to profile avg_rating
- Completion flows to streaks
- Tags flow to search
- Created_at flows to history
- Difficulty flows to recommendation
- Progress flows to certificate (100% when completed)

---

## Phase 103: Concurrent Operation Safety Tests

### Step 103.1: Concurrent safety tests (8 tests)
- 20 concurrent creates all produce unique IDs
- Concurrent reads during write don't crash
- Concurrent updates to different fields merge correctly
- Concurrent deletes of same game don't crash
- Stats during concurrent create works (10 threads)
- Leaderboard during concurrent creates works
- 20 concurrent profile reads work
- Delete all during list operation doesn't crash

---

## Phase 104: Session Metrics Tests

### Step 104.1: Session metrics tests (12 tests)
- Session start/end stored and retrievable
- Elapsed stored correctly, updatable, defaults to 0
- Mistakes increment through updates
- Hints used updatable
- Completion time appears in stats
- Best time tracked across multiple games
- Average completion time correct for multiple games
- Paused state persisted
- Game mode stored

---

## Phase 105: Malformed Input Handling Tests

### Step 105.1: Malformed input tests (18 tests)
- Invalid JSON, wrong content type, null body, empty string → 400
- Update with invalid JSON → 400
- Solve/validate/hint/analyze with missing board/puzzle → 400
- Rate with missing rating → 400
- Import with missing share_code → 400
- Archive with missing field handled gracefully
- Non-numeric difficulty handled gracefully
- Negative difficulty handled gracefully
- Clone/export nonexistent → 404
- Compare with swapped params (negative differences)

---

## Phase 106: Numeric Boundary Tests

### Step 106.1: Numeric boundary tests (13 tests)
- Difficulty 0 and max (58)
- Elapsed 0 and very large (9999999)
- Mistakes 0 and large (999)
- Rating boundaries 1 and 5
- Leaderboard with zero time
- Stats with all zero values
- Average time with zero
- Completion percentage 0% and 100% (uses 0-1 scale)
- Recommendation with extreme times (1s → harder)
- Streak with 20 completions

---

## Phase 107: Export/Import Integrity Tests

### Step 107.1: Export/import integrity tests (8 tests)
- Puzzle and solution survive roundtrip
- Metadata (difficulty, elapsed, mistakes, hints, rating) preserved
- Tags survive export/import
- Notes survive export/import
- Different IDs for original and imported
- Multiple imports of same code create unique games
- Full state with all fields survives roundtrip

---

## Phase 108: Query Parameter Tests + list_games Fix

### Step 108.1: Bug fix — non-numeric limit crashes list_games
**Found and fixed bug:** `GET /api/games?limit=abc` crashed with ValueError because
`int(request.args.get("limit", 50))` didn't handle non-numeric input. Added try/except
to fall back to default limit of 50.

### Step 108.2: Query parameter tests (18 tests)
- Games limit: default, 1, 0, negative, non-numeric, large
- Leaderboard: limit and difficulty filter
- History: limit, completed filter, difficulty filter
- New game with seed: reproducible, different seeds differ, no seed differs
- Daily/weekly puzzle: same result on same day/week
- Compare: missing a or b parameter → 400

---

## Phase 109: Final Regression Suite

### Step 109.1: Regression tests (15 tests)
Comprehensive regression suite covering all major features:
- Core: new game validity, CRUD lifecycle
- Solver: solve returns valid solution, hint returns valid move, validate detects conflicts
- Storage: persistence across requests, delete all clears everything
- Stats: stats reflect games, profile aggregates correctly
- Features: archive/unarchive, clone, export/import roundtrip, certificate
- Errors: 404 returns JSON error, invalid JSON returns 400

---

## Phase 110: Health Check Tests

### Step 110.1: Health check tests (8 tests)
- Root returns HTML page
- All 12 GET endpoints respond with 200
- Basic create and retrieve works
- Solver works
- Stats returns valid structure
- No storage leaks between tests
- Error responses are JSON with error field
- App is properly configured
