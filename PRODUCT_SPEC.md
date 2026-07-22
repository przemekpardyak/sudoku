# Sudoku Web App — Product Specification

> **Version:** 1.0 — captured 2026-07-21
> **Purpose:** Detailed specification of all implemented features. Suitable as a source for user guide generation or as a reimplementation spec for a different coding agent.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Authentication & User Management](#2-authentication--user-management)
3. [Puzzle Generation & Solver](#3-puzzle-generation--solver)
4. [Game Play — Frontend Features](#4-game-play--frontend-features)
5. [Game Management & Persistence](#5-game-management--persistence)
6. [API Reference](#6-api-reference)
7. [UI/UX — Frontend Interactions](#7-uiux--frontend-interactions)
8. [CSS Theming System](#8-css-theming-system)
9. [Deployment Architecture](#9-deployment-architecture)
10. [Test Architecture](#10-test-architecture)
11. [Environment Variables](#11-environment-variables)
12. [Design Decisions](#12-design-decisions)
13. [Known Issues & Gotchas](#13-known-issues--gotchas)

---

## 1. Overview

### Tech Stack
- **Backend:** Python 3.11 + Flask 3.0.3
- **Frontend:** Vanilla JavaScript (no framework), single IIFE in `static/app.js`
- **Styling:** Vanilla CSS with CSS variables, dark/light glassmorphism theme
- **Storage:** Google Cloud Firestore (production) / in-memory (dev)
- **Auth:** Session-based, `hashlib.pbkdf2_hmac` password hashing (no external deps)
- **Deployment:** Google Cloud Run + Terraform IaC
- **Tests:** `unittest` + Playwright (E2E), 991 tests total

### Key Files

| File | Lines | Description |
|------|-------|-------------|
| `app.py` | ~1220 | Flask backend with 34 API endpoints |
| `static/app.js` | ~1515 | All frontend game logic in a single IIFE |
| `static/styles.css` | ~867 | Dark/light glassmorphism theme |
| `templates/index.html` | ~221 | Page structure |
| `auth.py` | ~278 | Session-based auth with pbkdf2_hmac |
| `storage.py` | ~293 | Firestore + in-memory storage |
| `sudoku.py` | ~136 | Puzzle generation + solver |
| `tests/test_e2e_sudoku.py` | ~2300 | 103 E2E browser tests (Playwright) |
| `tests/test_auth.py` | ~280 | 30 auth unit tests |
| `terraform/` | 8 files | Cloud Run + Firestore + optional IAP |
| `scripts/deploy.sh` | 314 | 4-phase deploy script |
| `scripts/cleanup.sh` | ~255 | 8-phase cleanup script |

---

## 2. Authentication & User Management

### 2.1 Password Hashing (`auth.py`)

- **Algorithm:** `hashlib.pbkdf2_hmac` with SHA-256
- **Iterations:** 200,000
- **Salt:** 32-byte random salt per user
- **Hash format:** `algo$iterations$salt_hex$hash_hex` (e.g., `sha256$200000$ab12cd34...$ef56gh78...`)
- **Legacy support:** Also accepts old `salt_hex:hash_hex` colon format
- **Verification:** Uses `secrets.compare_digest` (constant-time comparison to prevent timing attacks)

### 2.2 User Storage

| Backend | Class | Collection | Use Case |
|---------|-------|------------|----------|
| In-memory | `InMemoryUserStorage` | N/A (dict + username index) | Local dev, testing |
| Firestore | `FirestoreUserStorage` | `users` | Production |

- Factory `_get_user_storage()` — uses Firestore if `FIRESTORE_PROJECT` env var set, else in-memory
- `reset_user_store()` — testing helper, resets to fresh in-memory store

### 2.3 Functions

| Function | Description |
|----------|-------------|
| `hash_password(password)` | Returns `sha256$200000$salt_hex$hash_hex` |
| `verify_password(password, stored_hash)` | Constant-time comparison, supports both hash formats |
| `create_user(username, password)` | Creates user, returns `{user_id, username}`, raises `ValueError` if username exists |
| `authenticate(username, password)` | Returns user dict or `None` |
| `get_user(user_id)` | Returns user dict or `None` |
| `ensure_default_user()` | Creates `testuser`/`password` if not exists (idempotent, doesn't overwrite) |
| `get_default_user()` | Returns testuser info for migration purposes |

### 2.4 Auth API Endpoints

| Endpoint | Method | Request Body | Success Response | Error Responses |
|----------|--------|-------------|-----------------|-----------------|
| `/api/register` | POST | `{username, password}` | `201: {user_id, username}` | `400` missing fields, `409` username exists |
| `/api/login` | POST | `{username, password}` | `200: {user_id, username}` | `401` invalid credentials |
| `/api/logout` | POST | (none) | `200: {ok: true}` | — |
| `/api/me` | GET | (none) | `200: {authenticated: bool, user_id?, username?}` | — |

### 2.5 Frontend Auth Flow

1. Page loads → `checkAuth()` calls `GET /api/me`
2. If authenticated → hide login overlay, show game UI, start/resume game
3. If not authenticated → show `#loginOverlay` with login/register form, game waits
4. Login form: username + password fields, submit button, error display
5. Toggle between Login/Register modes — register auto-logs in after success
6. Header shows `👤 username` + Logout button when authenticated
7. Session uses Flask cookies (not JWT)

### 2.6 Game Scoping

- All game operations scoped by `user_id` from session
- `get_current_user_id()` returns `session.get("user_id")`
- `create_game` endpoint: attaches `user_id` from session
- `list_games` endpoint: filters by current user's `user_id`
- `delete_all_games` endpoint: only deletes current user's games
- `migrate_games_to_user(user_id)` — assigns `user_id` to games without one (for migration)

---

## 3. Puzzle Generation & Solver (`sudoku.py`)

### 3.1 Puzzle Generation

```
generate_puzzle(difficulty=40) → (puzzle, solution)
```

1. `generate_solved_board()`:
   - `fill_diagonal_boxes()` — fills 3 diagonal 3×3 boxes with shuffled 1-9 (independent, no conflicts)
   - `_solve(board)` — backtracking to fill remaining cells
2. Copy solved board
3. Shuffle all 81 cell positions
4. Remove up to `difficulty` cells — after each removal, verify unique solution via `_count_solutions(puzzle, limit=2) == 1`
5. Only keeps removal if unique solution maintained
6. Returns `(puzzle, solution)` tuple

### 3.2 Solver Functions

| Function | Description |
|----------|-------------|
| `_is_valid(board, row, col, num)` | Checks row, column, 3×3 box constraints |
| `_has_conflicts(board)` | Checks for duplicate non-zero values in any row/col/box |
| `_solve(board)` | Recursive backtracking, mutates board in place, returns bool |
| `_count_solutions(board, limit=2)` | Counts solutions up to limit, does NOT mutate board (uses copy) |

### 3.3 Difficulty Levels

| Level | Cells Removed | Name |
|-------|---------------|------|
| Easy | 30 | Easy |
| Medium | 40 | Medium |
| Hard | 50 | Hard |
| Expert | 58 | Expert |

> **Note:** At Expert (58), may not be possible to remove all cells while maintaining uniqueness — generator removes as many as it can (typically 55-57).

---

## 4. Game Play — Frontend Features

### 4.1 Game State Variables

```javascript
let puzzle = [];        // 9x9 original puzzle (0 = empty)
let solution = [];      // 9x9 solved board
let board = [];         // 9x9 current board state
let given = [];         // 9x9 boolean (true = pre-filled/given)
let notes = [];         // notes[r][c] = array of 9 booleans
let autoNotesMask = []; // tracks which notes are auto-generated
let autoNotesActive = false;
let selected = null;     // {r, c} or null
let mistakes = 0;
let elapsed = 0;
let difficulty = 40;
let mode = 'final';     // 'final' | 'notes'
let currentGameId = null;
let gameCompleted = false;
let hintsUsed = 0;
let isPaused = false;
let undoStack = [];
let redoStack = [];
const MAX_HISTORY = 200;
const STORAGE_KEY = 'sudoku_current_game';
const DIFF_NAMES = { 30: 'Easy', 40: 'Medium', 50: 'Hard', 58: 'Expert' };
```

### 4.2 Cell Selection & Highlighting

`selectCell(r, c)` sets the selected cell and `applyHighlights()` applies:

| CSS Class | Trigger | Visual |
|-----------|---------|--------|
| `.selected` | Active cell | Accent glow + inset border |
| `.highlight` | Row, column, 3×3 box of selected | Subtle background |
| `.same-num` | Cells with same value as selected | Slightly stronger background |
| `.conflict` | Real-time: duplicate numbers in same row/col/box | Amber highlight |

**Hint interaction:** If hint is previewing and you click its cell → commits hint; click elsewhere → cancels.

### 4.3 Number Placement

`placeNumber(num)` flow:
1. If no cell selected → "Select a cell first." hint
2. If cell is `given` → "That cell is pre-filled." hint
3. **num=0 (erase):**
   - If cell has final number → remove number, preserved pencil marks reappear
   - If no final number → clear all pencil marks in cell
4. **mode='notes':** `toggleNote(r, c, num)` — toggles pencil mark, marks as user-entered (not auto)
5. **mode='final':** `placeFinal(r, c, num)`:
   - Sets board value
   - Hides pencil marks (preserved, reappear on erase)
   - Auto-removes same digit from pencil marks in row/col/box
   - Checks for row/col/box conflicts — marks with `.conflict` class (amber) but **allows placement**
   - Does NOT compare against solution — numbers always placed
   - Does NOT increment mistakes counter — only Check button does that

### 4.4 Undo/Redo

- `snapshot()` captures: `board`, `notes`, `given`, `mistakes`
- `pushHistory()` — pushes snapshot to `undoStack`, clears `redoStack`, caps at 200 entries
- `undo()` — moves current to redo, restores last undo
- `redo()` — moves current to undo, restores last redo
- Buttons auto-disable when stack empty
- New game clears both stacks

### 4.5 Hint System (Click-to-Toggle)

- `startHintPreview()` — picks random empty cell where `board ≠ solution`, shows correct value in amber with glowing border
- `commitHint()` — applies hint: sets board value, marks as `given`, clears notes, adds to undo history, increments `hintsUsed`, checks win
- `cancelHintPreview()` — removes preview
- **Click behavior:** First click shows hint + button gets `.active` class (depressed look); second click hides hint
- **Hint cell click:** Accepts hint as placed value, exits hint mode
- **Escape key:** Cancels hint
- **Click elsewhere:** Cancels hint
- Button loses `.active` class on commit, cancel, or toggle off

### 4.6 Auto-Notes (Toggle)

- `autoNotesMask[r][c][n-1]` tracks auto-generated notes
- **Turn ON:** Fills all possible notes (checks row/col/box constraints), marks them in `autoNotesMask`. User-entered notes preserved (not overwritten, not marked as auto)
- **Turn OFF:** Clears only auto-generated notes (where `autoNotesMask` is true AND `notes` is true). User-entered notes (`autoNotesMask` false) preserved
- Button shows `.active` state when on
- `toggleNote()` marks user-toggled notes as non-auto in mask

### 4.7 Other Game Actions

| Action | Function | Behavior |
|--------|----------|----------|
| Check | `checkBoard()` | Compares board to solution, marks wrong cells with `.error`. Also calls `/api/validate` for conflict count and uniqueness |
| Solve | `solvePuzzle()` | Confirm dialog → fills all non-given cells with solution, marks `gameCompleted`, shows modal |
| Clear Notes | `clearNotes()` | Clears ALL pencil marks (both auto and user) |
| Reset Board | `resetBoard()` | Confirm dialog → resets all non-given cells to 0, clears all notes |
| Pause | `togglePause()` | Stops/resumes timer, board gets `blur(12px)` + `pointer-events:none`, shows "⏸ Paused" overlay |

### 4.8 Win Detection

- `checkWin()` — compares all 81 cells to solution
- On win: stops timer, saves game, flashes all cells green (`.win-flash` animation), shows win modal
- Win modal shows: time, level, mistakes, hints
- Fetches best times, shows "🏆 New best time!" if beaten
- Performance rating: ⭐⭐⭐ Perfect (0 mistakes, 0 hints) / ⭐⭐ Great / ⭐ Good

### 4.9 Timer

- `formatTime(s)` — `MM:SS` format
- `startTimer()` — resets to 0, starts `setInterval` (1 second)
- `resumeTimer()` — continues from `elapsed`
- Timer also triggers auto-save every 30 seconds (`elapsed % 30 === 0`) even without other state changes
- `stopTimer()` / `resetTimer()` helpers

### 4.10 Numpad

- `updateNumpad()` — disables buttons when all 9 instances of a number are placed
- Shows remaining count badge (`.num-remaining`)
- Erase button (⌫) always enabled

### 4.11 Progress Display

- `updateProgress()` — counts filled cells vs total empty cells, shows percentage
- Color: green at 100%, amber at ≥50%, default otherwise

---

## 5. Game Management & Persistence

### 5.1 Storage Architecture

| Class | Backend | Use Case |
|-------|---------|----------|
| `GameStorage` | Abstract interface | — |
| `InMemoryStorage` | Dict keyed by `game_id` | Local dev, testing |
| `FirestoreStorage` | Firestore documents | Production |

- `get_storage()` factory — singleton, uses Firestore if `FIRESTORE_PROJECT` env var set

### 5.2 Firestore Serialization

Firestore doesn't allow nested arrays. `FirestoreStorage` serializes these fields as JSON strings:

```python
_ARRAY_FIELDS = {"puzzle", "solution", "board", "given", "notes", "undoStack", "redoStack"}
```

- `_serialize()` — converts array fields to JSON strings before write
- `_deserialize()` — converts JSON strings back to arrays on read

### 5.3 Game State Schema

Full game state saved by frontend (`serializeState()`):

```json
{
  "puzzle": [[6,0,1,...],...],
  "solution": [[6,9,1,...],...],
  "board": [[6,5,1,...],...],
  "given": [[true,false,...],...],
  "notes": [[[false,true,...],...],...],
  "undoStack": [...],
  "redoStack": [...],
  "mistakes": 2,
  "elapsed": 300,
  "difficulty": 40,
  "completed": false,
  "paused": false,
  "hintsUsed": 1
}
```

### 5.4 Storage Methods

| Method | Description |
|--------|-------------|
| `create_game(state, user_id)` | UUID, sets `created_at`/`updated_at`, stores with `user_id` |
| `get_game(game_id)` | Returns full game state or `None` |
| `save_game(game_id, state)` | Merge update + `updated_at` |
| `list_games(limit, user_id)` | Sort by `updated_at` desc, filter by `user_id`, return summaries |
| `delete_game(game_id)` | Delete, return bool |
| `migrate_games_to_user(user_id)` | Assign `user_id` to games without one, return count |

### 5.5 List Game Summary (`_summarize()`)

Returns metadata only (no board/solution/stacks):

```json
{
  "game_id": "uuid",
  "difficulty": 40,
  "mistakes": 2,
  "elapsed": 300,
  "completed": false,
  "created_at": "ISO timestamp",
  "updated_at": "ISO timestamp",
  "progress": "12/40",
  "hintsUsed": 1,
  "archived": false,
  "tags": ["cloned"],
  "rating": 0,
  "notes": "",
  "favorite": false
}
```

### 5.6 Auto-Save Behavior

- `scheduleAutoSave()` — saves immediately on every state change
- `createGameOnServer()` — POST to `/api/games` on new game start
- `saveGameToServer()` — PUT to `/api/games/{id}` on state change
- `beforeunload` event — uses `navigator.sendBeacon()` for reliable save on page close
- localStorage stores only `{game_id}` for resume
- `tryResumeLastGame()` — fetches game from server by ID in localStorage

### 5.7 Clone Game

- POST `/api/games/<id>/clone` copies puzzle, solution, difficulty from source
- Resets board to puzzle state, clears notes, mistakes, elapsed, hintsUsed
- Sets `given` from puzzle (non-zero cells)
- Adds tag "cloned" and `sourceGameId` field

### 5.8 Import/Export

- **Export:** base64-urlsafe-encode JSON of game state (minus `game_id`, `created_at`, `updated_at`)
- **Import:** decode base64, parse JSON, create new game
- **Share URL format:** `{origin}/?import={share_code}`
- Frontend checks URL param `import` on load, POSTs to `/api/games/import`, loads game, cleans URL

---

## 6. API Reference

### 6.1 Page Route

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Renders `index.html` |

### 6.2 Auth Endpoints

See [§2.4](#24-auth-api-endpoints).

### 6.3 Puzzle Generation

| Endpoint | Method | Params | Response |
|----------|--------|--------|----------|
| `/api/new-game` | GET | `difficulty` (int, default 40), `seed` (string, optional) | `{puzzle, solution, seed}` |
| `/api/daily-puzzle` | GET | — | `{puzzle, solution, date, seed}` — seeded by `daily-{YYYY-MM-DD}`, difficulty 40 |
| `/api/weekly-puzzle` | GET | — | `{puzzle, solution, week, seed, difficulty: 50}` — seeded by `weekly-{Monday's date}`, difficulty 50 |

### 6.4 Game CRUD

| Endpoint | Method | Request/Params | Success | Errors |
|----------|--------|----------------|---------|--------|
| `/api/games` | GET | `limit` (int, default 50) | `200: {games: [...]}` | — |
| `/api/games` | POST | Full game state JSON | `201: {game_id}` | — |
| `/api/games` | DELETE | — | `200: {ok, deleted_count}` | — |
| `/api/games/<game_id>` | GET | — | `200: {full game state}` | `404` |
| `/api/games/<game_id>` | PUT | Full game state JSON | `200: {ok, game_id}` | `404` |
| `/api/games/<game_id>` | DELETE | — | `200: {ok, deleted}` | `404` |
| `/api/games/<game_id>/clone` | POST | — | `201: {game_id, source_game_id}` | `404` |

### 6.5 Game Sub-resources

| Endpoint | Method | Request | Response | Notes |
|----------|--------|---------|----------|-------|
| `/api/games/<game_id>/rate` | PUT | `{rating: int 1-5}` | `{ok, game_id, rating}` | Only on completed games; `400` if not completed or invalid |
| `/api/games/<game_id>/archive` | PUT | `{archived: bool}` | `{ok, game_id, archived}` | — |
| `/api/games/<game_id>/certificate` | GET | — | `{game_id, difficulty, difficulty_label, elapsed, mistakes, hintsUsed, rating, performance, created_at, completed}` | Only completed games; `400` if not |
| `/api/games/<game_id>/progress` | GET | — | `{filled, total_cells, total_empty, progress_pct, correct, incorrect}` | — |
| `/api/games/<game_id>/export` | GET | — | `{share_code: "base64..."}` | Strips game_id, created_at, updated_at |
| `/api/games/compare` | GET | `a`, `b` (game IDs) | `{game_a: {...}, game_b: {...}, differences: {...}}` | Compares difficulty, elapsed, mistakes, hintsUsed, rating |
| `/api/games/import` | POST | `{share_code: "base64..."}` | `201: {game_id}` | `400` if invalid code |

### 6.6 Solver/Validator

| Endpoint | Method | Request | Response | Errors |
|----------|--------|---------|----------|--------|
| `/api/solve` | POST | `{board: 9x9}` | `{solved: 9x9, unique: bool, num_solutions: int}` | `400` if not 9x9, conflicts, or no solution |
| `/api/hint` | POST | `{board: 9x9}` | `{row, col, value, technique}` | `200 {message}` if complete; `400` if conflicts |
| `/api/validate` | POST | `{board: 9x9}` | `{valid, complete, filled, empty, conflicts, unique_solution}` | `400` if not 9x9 |
| `/api/analyze` | POST | `{puzzle: 9x9}` | `{empty_cells, filled_cells, has_conflicts, unique_solution, difficulty_rating}` | `400` if not 9x9 |

#### Hint Techniques (in order)
1. `naked_single` — cell with only one possible candidate
2. `hidden_single_row` / `hidden_single_column` / `hidden_single_box` — number that can only go in one cell of a unit
3. `backtracking` — fallback, solves board and returns first empty cell's value

### 6.7 Statistics & Analytics

| Endpoint | Method | Params | Response |
|----------|--------|--------|----------|
| `/api/best-times` | GET | — | `{"30": 120, "40": 300}` — best time per difficulty |
| `/api/stats` | GET | — | `{total_games, completed_games, completion_rate, completion_pct, total_time, total_mistakes, total_hints, avg_completion_time, best_time, avg_mistakes, avg_rating, by_difficulty: {...}, achievements: [...]}` |
| `/api/stats/export` | GET | — | `{exported_at, summary: {...}, by_difficulty: {...}, achievements: [...], top_5_fastest: [...]}` |
| `/api/leaderboard` | GET | `limit` (default 10, max 50), `difficulty` (optional) | `{leaderboard: [...], count}` |
| `/api/recommend-difficulty` | GET | — | `{recommended_difficulty, current_difficulty?, best_time?, avg_time?, completed_at_level?, reasoning}` |
| `/api/history` | GET | `limit` (default 20, max 100), `completed` (bool), `difficulty` (int) | `{history: [...], count, total}` |
| `/api/streaks` | GET | — | `{current_streak, best_streak, total_completions, total_games, completion_rate}` |
| `/api/profile` | GET | — | Comprehensive: stats + achievements + streaks + recommendation + level |

### 6.8 Achievement Types

| Achievement | Condition |
|-------------|-----------|
| `first_win` | Completed ≥1 game |
| `perfect_game` | Completed with 0 mistakes AND 0 hints |
| `speed_run` | Completed in <60 seconds |
| `no_hints` | Completed without using hints |
| `dedicated` | 10+ completed games |
| `expert_winner` | Completed an Expert (difficulty 58) puzzle |

### 6.9 Performance Ratings (certificate endpoint)

| Rating | Condition |
|--------|-----------|
| `perfect` | 0 mistakes AND 0 hints |
| `excellent` | ≤1 mistake, 0 hints, <120s |
| `good` | <3 mistakes, <300s |
| `completed` | anything else |

### 6.10 Difficulty Recommendation Logic

- No completed games → suggest 30 (easy)
- Best time <60s on most-used difficulty → suggest harder (most_used + 10, max 58)
- Average time >300s → suggest easier (most_used - 10, min 20)
- Otherwise → suggest current most-used difficulty

---

## 7. UI/UX — Frontend Interactions

### 7.1 Page Structure

```
<div class="app">
  <header class="header">
    <div class="brand"> 9×9 logo + "Sudoku" + tagline
    <button class="theme-toggle"> 🌙/☀️
    <div class="user-info"> username + logout (hidden when not logged in)
    <div class="stats"> Time, Mistakes, Level, Progress
  </header>
  <main class="game">
    <div class="board"> 9×9 grid
    <aside class="panel">
      Difficulty buttons (Easy/Medium/Hard/Expert)
      Mode toggle (Final ✏️ / Notes 📝)
      Number pad (1-9 + ⌫)
      Action buttons (grouped in 2-column rows):
        - New Game (full width, primary)
        - Daily / Pause
        - Undo / Redo
        - Check / Hint
        - Auto-Notes / Clear Notes
        - Reset Board / Solve
        - Load Games / Help
      Hint text
    </aside>
  </main>
  <footer> Built with Flask + game ID display
  <div class="overlay" id="helpOverlay"> Keyboard shortcuts table
  <div class="overlay" id="overlay"> Win/solution modal
  <div class="overlay" id="gamesOverlay"> Saved games list with sort/filter
  <div class="overlay show" id="loginOverlay"> Login/Register form
</div>
```

### 7.2 Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `1`-`9` | Place number (final or notes mode) |
| `0`/`Backspace`/`Delete` | Erase cell |
| `N` | Toggle Final/Notes mode |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` / `Ctrl+Shift+Z` | Redo |
| `Escape` | Dismiss hint / close modals |
| `L` | Open Load Games modal |
| `A` | Auto-fill pencil marks |
| `D` | Daily puzzle |
| `R` | Reset board |
| `T` | Toggle theme |
| `?` | Show help |
| `Space` | Pause/Resume |
| `↑↓←→` | Move selection |

### 7.3 Games List Modal

- Table with columns: Difficulty, Progress, Mistakes, Hints, Time, Last Played, Actions
- Sort by: Last Played, Time, Difficulty, Mistakes, Progress
- Filter checkboxes: Completed, In Progress
- Actions per game: Resume/View, Share (copies link), Delete
- "Clear All" button with confirmation
- Stats summary bar at top (total, completed, best time, per-difficulty counts)

### 7.4 Game Sharing Flow

1. Click Share on a game → GET `/api/games/{id}/export` → get `share_code`
2. Build URL: `{origin}/?import={share_code}`
3. Copy to clipboard via `navigator.clipboard.writeText()`
4. Visiting the link: app checks URL param `import`, POSTs to `/api/games/import`, loads game, cleans URL

### 7.5 Theme System

- Default: dark mode
- Toggle adds/removes `.light` class on `<html>`
- Preference saved to `localStorage` key `sudoku_theme` (values: `light` / `dark`)
- Toggle button shows 🌙 (dark) or ☀️ (light)

---

## 8. CSS Theming System

### 8.1 Dark Theme Variables (default, `:root`)

```css
--bg: #0f1117
--bg-grad-1: #14182a
--bg-grad-2: #0a0c12
--surface: rgba(26, 29, 42, 0.7)
--surface-solid: #1a1d2a
--surface-hi: #232838
--border: rgba(255, 255, 255, 0.08)
--border-strong: rgba(255, 255, 255, 0.18)
--text: #f4f6fb
--text-dim: #9aa0b4
--text-mute: #6b7080
--accent: #7c5cff (purple)
--accent-hi: #9b82ff
--accent-glow: rgba(124, 92, 255, 0.45)
--success: #3ddc97 (green)
--danger: #ff5470 (red)
--warning: #ffb84d (amber)
--given: #c8cde0
--user-input: #7c5cff
--highlight: rgba(124, 92, 255, 0.12)
--same-num: rgba(124, 92, 255, 0.22)
--error-bg: rgba(255, 84, 112, 0.14)
--shadow: 0 20px 60px rgba(0, 0, 0, 0.5)
--radius: 16px
--radius-sm: 10px
```

### 8.2 Light Theme Variables (`:root.light`)

```css
--bg: #f0f2f8
--bg-grad-1: #e8eaf3
--bg-grad-2: #f5f7fa
--surface: rgba(255, 255, 255, 0.8)
--surface-solid: #ffffff
--surface-hi: #f0f2f8
--border: rgba(0, 0, 0, 0.1)
--border-strong: rgba(0, 0, 0, 0.2)
--text: #1a1d2a
--text-dim: #5a6070
--text-mute: #8a8e9a
--accent: #6b4ce6
--accent-hi: #7c5cff
--accent-glow: rgba(107, 76, 230, 0.3)
--given: #4a4a5a
--user-input: #6b4ce6
--highlight: rgba(107, 76, 230, 0.1)
--same-num: rgba(107, 76, 230, 0.2)
--error-bg: rgba(255, 84, 112, 0.1)
--shadow: 0 10px 40px rgba(0, 0, 0, 0.15)
```

### 8.3 Key CSS Classes

| Class | Purpose |
|-------|---------|
| `.cell.given` | Pre-filled cells (cursor: default) |
| `.cell.user` | User-placed numbers (accent color) |
| `.cell.selected` | Active cell (accent glow + inset border) |
| `.cell.highlight` | Row/col/box highlight |
| `.cell.same-num` | Same number highlight |
| `.cell.error` | Wrong number (red + shake animation) |
| `.cell.conflict` | Duplicate in row/col/box (amber) |
| `.cell.hint-preview` | Hint showing (amber bg + border) |
| `.cell.hint-flash` | Hint applied animation (scale pulse) |
| `.cell.win-flash` | Win celebration (green flash) |
| `.board.paused` | Blur(12px) + pointer-events:none + "⏸ Paused" overlay |
| `.mode-btn.active` | Active mode button (gradient bg) |
| `.diff-btn.active` | Active difficulty button (gradient bg) |
| `.action-btn.primary` | Primary action (gradient bg + glow) |
| `.action-btn.active` | Depressed/toggled action (hint, auto-notes) |
| `.action-btn.danger` | Destructive action (red bg) |
| `.difficulty-badge.easy/medium/hard/expert` | Colored difficulty badges |
| `.pencil-marks` | 3×3 mini-grid for notes |
| `.pencil-marks span.on` | Visible pencil mark |

### 8.4 Animations

| Name | Duration | Purpose |
|------|----------|---------|
| `shake` | 0.4s | Error cells (translateX) |
| `mistakePulse` | 0.5s | Mistake flash (scale + color) |
| `winFlash` | 1s | Win celebration (green bg + scale) |
| `hintPulse` | 0.6s | Hint applied (scale + glow) |
| `fadeIn` | 0.3s | Overlay appearance |
| `pop` | 0.4s | Modal appearance (scale from 0.85) |

### 8.5 Responsive Breakpoints

| Breakpoint | Layout Changes |
|------------|-----------------|
| `max-width: 820px` | Single column layout, panel below board |
| `max-width: 600px` | Smaller cells, compact numpad |
| `max-width: 400px` | 2-column sidebar grid, 5-column numpad |

### 8.6 Fonts

- **Primary:** `Outfit` (weights: 300, 400, 600, 700, 800)
- **Monospace:** `JetBrains Mono` (weights: 400, 600, 700)

### 8.7 Board Grid Structure

- 9×9 CSS grid with `aspect-ratio: 1`
- 3×3 box dividers via `border-left` on columns 3,6 and `border-top` on rows 3,6
- Cell font size: `clamp(16px, 3vw, 24px)`

---

## 9. Deployment Architecture

### 9.1 Container (Dockerfile)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==21.2.0
COPY app.py sudoku.py storage.py auth.py ./
COPY static/ ./static/
COPY templates/ ./templates/
ENV PORT=8080
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "0", "app:app"]
```

### 9.2 Requirements

```
flask==3.0.3
google-cloud-firestore==2.19.0
playwright
requests
```

### 9.3 Terraform Infrastructure

#### Resources Created

| Resource | File | Purpose |
|----------|------|---------|
| Core APIs (5) | `providers.tf` | run, artifactregistry, cloudbuild, compute, iamcredentials |
| Firestore API | `firestore.tf` | firestore.googleapis.com |
| Optional IAP APIs (6) | `providers.tf` | iap, certificatemanager, networkservices, networksecurity, servicecontrol, servicemanagement |
| Artifact Registry repo | `artifact_registry.tf` | `sudoku-repo` Docker repository |
| Firestore database | `firestore.tf` | `(default)` database, Native mode, location `nam5` (multi-region) |
| Cloud Run service | `cloud_run.tf` | `sudoku` service, gunicorn on :8080 |
| IAM: run.invoker | `cloud_run.tf` | Grants current user invoke permission |
| IAM: datastore.user | `cloud_run.tf` | Grants SA Firestore access |
| Optional: IAP + LB | `iap.tf` | Global HTTPS LB + IAP (when `enable_iap=true`) |

#### Environment Variables Injected into Cloud Run

| Variable | Value |
|----------|-------|
| `FIRESTORE_PROJECT` | project_id |
| `FIRESTORE_COLLECTION` | `"games"` |
| `PORT` | 8080 (set by Cloud Run automatically) |

#### Terraform Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `project_id` | (required) | GCP project ID |
| `region` | `us-central1` | GCP region |
| `app_name` | `sudoku` | Resource name prefix |
| `image_tag` | `latest` | Container image tag |
| `service_account_email` | `null` | SA for Cloud Run (null = default CE SA) |
| `concurrency` | `80` | Max concurrent requests per instance |
| `max_instance_count` | `10` | Max container instances |
| `min_instance_count` | `0` | Min instances (0 = scale to zero) |
| `memory` | `512Mi` | Memory per instance |
| `cpu` | `1` | CPU per instance |
| `allow_unauthenticated` | `true` | If true + no invoker_members, grants current user |
| `invoker_members` | `[]` | Explicit IAM members for run.invoker |
| `enable_iap` | `false` | Create IAP + LB |
| `iap_lb_scheme` | `EXTERNAL` | LB scheme (EXTERNAL or EXTERNAL_MANAGED) |
| `iap_allowed_users` | `[]` | IAP allowed users |
| `domain` | `null` | Custom domain for IAP LB |
| `firestore_location` | `nam5` | Firestore database location |
| `firestore_enable_pitr` | `false` | Point-in-time recovery |

### 9.4 Deploy Script (`deploy.sh`) — 4 Phases

1. **Service Account Setup** — Checks if default CE SA exists; if not, creates `sudoku-sa` with `cloudbuild.builder`, `artifactregistry.writer`, `storage.objectAdmin` roles + logs bucket
2. **Phase 1: Bootstrap** — `terraform apply` (targeted) enables APIs, creates AR repo + Firestore DB. Retry loop (5 attempts, 90s delay) for API deactivation races
3. **Phase 2: Build** — `gcloud builds submit` via Cloud Build (no local Docker needed). Retry loop (5 attempts, 60s delay)
4. **Phase 3: Deploy** — `terraform apply` (full) creates Cloud Run service + IAM, then `gcloud run deploy` rolls new revision

#### Deploy Command

```bash
PROJECT_ID=ppardyak-cad ./scripts/deploy.sh
# Optional env vars: REGION, APP_NAME, IMAGE_TAG, TF_ARGS, SKIP_AUDITS
# Quick redeploy (skip audits):
PROJECT_ID=ppardyak-cad SKIP_AUDITS=true TF_ARGS="" ./scripts/deploy.sh
```

### 9.5 Per-Project State Isolation

- State file: `terraform/terraform.tfstate.{PROJECT_ID}` — separate per project
- No global `gcloud config set project` — all commands use explicit `--project`/`--region` flags
- Supports parallel deploys to different projects

### 9.6 Access Methods

1. **Local proxy (default):** `gcloud run services proxy sudoku --region=us-central1 --project=ppardyak-cad --port=8080` → http://localhost:8080
2. **IAP (optional):** Global HTTPS LB + IAP with Google login. Requires org policy to allow EXTERNAL_HTTP_HTTPS LBs.

### 9.7 Cleanup Script (`cleanup.sh`) — 8 Phases

1. `terraform destroy` (auto-approved)
2. Delete Cloud Run service (if TF didn't)
3. Delete Artifact Registry repo
4. Delete Cloud Build buckets (logs + source)
5. Delete dedicated `sudoku-sa` service account
6. Remove per-project Terraform state file
7. API cleanup (handled by TF `disable_on_destroy`)
8. Delete Firestore database (slow, can survive terraform destroy)

### 9.8 Audit System

- `scripts/audit_gcp_project.sh` (39KB) — audits project state
- `scripts/run_audit.sh` — wrapper that runs audit with state validation
- Runs pre-deploy (expect clean) and post-deploy (expect deployed)
- Reports saved to `audits/` with timestamps (gitignored)
- Set `SKIP_AUDITS=true` to skip

---

## 10. Test Architecture

### 10.1 Test Categories

| Category | Description | Test Modules |
|----------|-------------|--------------|
| Unit | Pure function tests | 10 modules: test_sudoku, test_is_valid, test_solver_edge_cases, test_solver_robustness, test_solver_techniques, test_generation_stress, test_puzzle_quality, test_difficulty_validation, test_validation, test_performance |
| Storage | Data layer tests | 5 modules: test_storage, test_storage_behavior, test_storage_boundaries, test_storage_merge, test_firestore_serialization |
| Integration | API endpoint tests | 78 modules covering all endpoints |
| Deployed | HTTP smoke tests | 1 module: test_deployed_service |
| E2E | Browser tests (Playwright) | 1 module: test_e2e_sudoku |
| Auth | Auth unit tests | 1 module: test_auth |

**Total: 991 tests (888 API + 103 E2E), 1 skipped**

### 10.2 Test Runner

```bash
# Run all except E2E
venv/bin/python3 run_all_tests.py

# Run everything including E2E
venv/bin/python3 run_all_tests.py --all

# Specific category
venv/bin/python3 run_all_tests.py --category unit
venv/bin/python3 run_all_tests.py --category storage
venv/bin/python3 run_all_tests.py --category integration
venv/bin/python3 run_all_tests.py --category e2e

# Flags
--fail-fast    # Stop on first failure
--watch        # Re-run on file changes
```

### 10.3 E2E Test Suites

46 test classes covering: page load, gameplay, UI features, game storage, difficulty buttons, check button, solve button, hint button, auto-notes, reset board, notes mode, conflict highlighting, progress display, cell highlighting, numpad state, keyboard shortcuts, games modal, game ID display, timer display, win flow, load game, pause timer, error correction, expert difficulty, play again, game persistence, same number highlighting, conflict detection, delete game, share game, difficulty change, games modal sort/filter, stats summary, space key pause, medium difficulty, new game from win modal, button layout, difficulty selection only, auto-notes toggle, hint button toggle, allow user errors, pause blur, auth.

### 10.4 E2E Test Infrastructure

- Uses Playwright with headless Chromium
- Auto-starts Flask dev server on localhost:5000 if not running
- Logs in as `testuser`/`password` for API cleanup
- `setUp()` logs in as testuser before each test via browser UI
- `_login()` / `_logout()` helper methods
- Clears all games between test class setup
- API session (`requests.Session`) for authenticated cleanup

### 10.5 Auth Tests (`test_auth.py`)

| Class | Tests | Coverage |
|-------|-------|----------|
| `TestPasswordHashing` | 5 | Hash format, salt-based, verify correct/wrong/empty |
| `TestUserStore` | 5 | Create user, hashed password stored, duplicate raises, authenticate success/failure |
| `TestEnsureDefaultUser` | 2 | Creates testuser if not exists, doesn't overwrite |
| `TestAuthAPI` | 4 | Register, login, logout, /api/me endpoints via Flask test client |
| `TestGameScoping` | 4+ | Games scoped by user_id, migration |

### 10.6 Skipped Test

- `test_solve_with_minimal_clues` — solves 17-clue Sudoku (mathematical minimum for unique solution). Naive backtracking explores millions of branches. Run with `SUDOKU_RUN_SLOW=1`.

---

## 11. Environment Variables

| Variable | Default | Where Used | Purpose |
|----------|---------|------------|---------|
| `FLASK_SECRET_KEY` | `sudoku-dev-secret-key-change-in-prod` | `app.py` | Flask session encryption |
| `FIRESTORE_PROJECT` | (unset) | `storage.py`, `auth.py` | GCP project for Firestore (unset = in-memory) |
| `FIRESTORE_COLLECTION` | `games` | `storage.py` | Firestore collection name |
| `PORT` | `8080` (Cloud Run) / `5000` (dev) | `Dockerfile`, `app.py` | Server port |
| `SUDOKU_RUN_SLOW` | (unset) | `tests/` | Forces slow 17-clue solver test |

---

## 12. Design Decisions

### 12.1 Button Layout Reorganization

Buttons moved from single-column flex to 2-column grids (`.action-row`). New Game spans full width. Reduces vertical height ~40%, aligns with board.

### 12.2 Difficulty Selection Only

Clicking difficulty buttons only updates selection + label, shows hint message. Does NOT create new game. New Game button uses selected difficulty.

### 12.3 Auto-Notes Toggle

Toggle behavior using `autoNotesMask` array. Toggle off clears only auto notes, preserves user-entered. Button shows active state.

### 12.4 Hint Click-to-Toggle

Changed from hold-to-preview to click-to-toggle. Button gets active class (depressed look). Hint stays until clicked again, cell clicked to accept, or Escape.

### 12.5 Allow User Errors

Removed solution comparison from `placeFinal` — numbers always placed. Conflict detection highlights row/col/box conflicts in amber. Mistakes counter only incremented by Check button (compares against solution).

### 12.6 Pause Board Blur

Board gets `blur(12px)` + `pointer-events:none` when paused. "Paused" overlay shown. Unblurs on resume/new game/restore. Prevents cheating by hiding the board.

### 12.7 User Authentication

Session-based auth with pbkdf2_hmac (no external dependencies). Games scoped by user_id. Default user `testuser`/`password` created on startup. Login/register UI overlay. User info + logout in header.

---

## 13. Known Issues & Gotchas

### 13.1 Deployment Gotchas

| Issue | Mitigation |
|-------|------------|
| Firestore deletion is slow | Cleanup script Phase 0 deletes Firestore before terraform destroys the API |
| Firestore propagation delay | Wait ~30s after deleting Firestore before redeploying or get 409 "Database already exists" |
| gcloud auth expiry | Run `gcloud auth login` + `gcloud auth application-default login`. Daily 9 AM reminder set up. |
| Artifact Registry persistence | If deploy fails mid-way, AR repo may persist and block next deploy's audit. Delete manually or run cleanup. |
| compute.googleapis.com deactivation | Can take 5+ minutes. Deploy script retries 5 times with 90s delay. |

### 13.2 Expert Difficulty Edge Case

At Expert (58 cells removed), may not be possible to remove all cells while maintaining unique solution. Generator removes as many as it can (typically 55-57).

### 13.3 Auto-Save

`scheduleAutoSave()` saves immediately on every state change (not debounced). Additionally, the timer interval triggers `scheduleAutoSave()` every 30 seconds (`elapsed % 30 === 0`) to persist elapsed time even without other changes. `beforeunload` uses `navigator.sendBeacon()` for reliable save on page close.

### 13.4 Player Level

`level = min(completed_count, 100)` — 1 level per completion, cap at 100.

### 13.5 Week Calculation (Weekly Puzzle)

Finds Monday of current week: `today - timedelta(days=today.weekday())`. Seeds with `weekly-{Monday's ISO date}`.

### 13.6 Difficulty Labels (Certificate Endpoint)

| Empty Cells | Label |
|-------------|-------|
| ≤25 | Easy |
| ≤35 | Medium |
| ≤45 | Hard |
| >45 | Expert |

### 13.7 Analyze Difficulty Rating

| Empty Cells | Rating | Label |
|-------------|--------|-------|
| ≤25 | 1 | Easy |
| ≤35 | 2 | Medium-Easy |
| ≤45 | 3 | Medium |
| ≤52 | 4 | Hard |
| >52 | 5 | Expert |

---

*End of Product Specification*
