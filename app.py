from __future__ import annotations

import base64
import json as _json
import os
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request, session

from auth import authenticate, create_user, ensure_default_user, get_default_user
from storage import get_storage
from sudoku import generate_puzzle
from tutorial import get_all_lessons, get_lesson, get_initial_progress

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "sudoku-dev-secret-key-change-in-prod")

# App version
APP_VERSION = "1.0.0"


def _get_git_commit() -> str:
    """Get short git commit hash, or 'unknown' if not available."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


# Ensure default user exists on import
ensure_default_user()


@app.route("/")
def index() -> str:
    """Render the main game page."""
    return render_template("index.html", app_version=APP_VERSION)


@app.route("/api/version")
def version() -> object:
    """Return app version info."""
    return jsonify({
        "version": APP_VERSION,
        "git_commit": _get_git_commit(),
        "deployed_at": os.environ.get("DEPLOYED_AT", ""),
    })


def get_current_user_id() -> str | None:
    """Return the current user's ID from the session, or None."""
    return session.get("user_id")


# --- Auth endpoints ---


@app.route("/api/register", methods=["POST"])
def register() -> object:
    """Register a new user.

    Request body (JSON):
        username: Desired username.
        password: Plaintext password.

    Returns:
        201 with user_id and username on success.
        400 if username or password is missing.
        409 if username already exists.
    """
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    try:
        user = create_user(username, password)
    except ValueError:
        return jsonify({"error": "Username already exists"}), 409
    return jsonify({"user_id": user["user_id"], "username": user["username"]}), 201


@app.route("/api/login", methods=["POST"])
def login() -> object:
    """Authenticate a user and set the session.

    Request body (JSON):
        username: Username.
        password: Plaintext password.

    Returns:
        200 with username on success.
        401 if credentials are invalid.
    """
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    user = authenticate(username, password)
    if user is None:
        return jsonify({"error": "Invalid credentials"}), 401
    session["user_id"] = user["user_id"]
    session["username"] = user["username"]
    return jsonify({"user_id": user["user_id"], "username": user["username"]})


@app.route("/api/logout", methods=["POST"])
def logout() -> object:
    """Clear the session and log the user out."""
    session.clear()
    return jsonify({"ok": True})


@app.route("/api/me", methods=["GET"])
def me() -> object:
    """Return the current user info from the session."""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"authenticated": False})
    from auth import get_user
    user = get_user(user_id)
    if user is None:
        session.clear()
        return jsonify({"authenticated": False})
    return jsonify({
        "authenticated": True,
        "user_id": user["user_id"],
        "username": user["username"],
    })


@app.route("/api/new-game")
def new_game() -> object:
    """Generate a new sudoku puzzle and return it as JSON.

    Query params:
        difficulty: Number of cells to remove (default 40).
        seed: Optional seed for reproducible puzzle generation.
    """
    import random as _random
    try:
        difficulty = int(request.args.get("difficulty", 40))
    except (ValueError, TypeError):
        difficulty = 40
    seed = request.args.get("seed")
    if seed:
        _random.seed(seed)
    puzzle, solution = generate_puzzle(difficulty=difficulty)
    return jsonify({"puzzle": puzzle, "solution": solution, "seed": seed})


@app.route("/api/daily-puzzle")
def daily_puzzle() -> object:
    """Get today's daily puzzle — same for everyone on the same date."""
    from datetime import date
    import random as _random
    today = date.today().isoformat()
    _random.seed(f"daily-{today}")
    puzzle, solution = generate_puzzle(difficulty=40)
    return jsonify({
        "puzzle": puzzle,
        "solution": solution,
        "date": today,
        "seed": f"daily-{today}",
    })


@app.route("/api/weekly-puzzle")
def weekly_puzzle() -> object:
    """Get this week's puzzle — a harder puzzle that changes every Monday."""
    from datetime import date, timedelta
    import random as _random
    today = date.today()
    # Find Monday of the current week
    monday = today - timedelta(days=today.weekday())
    week_str = monday.isoformat()
    _random.seed(f"weekly-{week_str}")
    puzzle, solution = generate_puzzle(difficulty=50)
    return jsonify({
        "puzzle": puzzle,
        "solution": solution,
        "week": week_str,
        "seed": f"weekly-{week_str}",
        "difficulty": 50,
    })


# --- Game persistence endpoints ---


@app.route("/api/games", methods=["GET"])
def list_games() -> object:
    """List saved games (metadata only — no board/solution data).

    Games are scoped to the current logged-in user.
    """
    try:
        limit = int(request.args.get("limit", 50))
    except (ValueError, TypeError):
        limit = 50
    storage = get_storage()
    user_id = get_current_user_id()
    games = storage.list_games(limit=limit, user_id=user_id)
    return jsonify({"games": games})


@app.route("/api/games", methods=["DELETE"])
def delete_all_games() -> object:
    """Delete all saved games. Returns count of deleted games.

    Only deletes the current user's games.
    """
    storage = get_storage()
    user_id = get_current_user_id()
    games = storage.list_games(limit=500, user_id=user_id)
    count = 0
    for game in games:
        if storage.delete_game(game["game_id"]):
            count += 1
    return jsonify({"ok": True, "deleted_count": count})


@app.route("/api/games", methods=["POST"])
def create_game() -> object:
    """Create a new saved game with full state.

    The game is associated with the current logged-in user's user_id.
    """
    data = request.get_json(force=True)
    storage = get_storage()
    user_id = get_current_user_id()
    game_id = storage.create_game(data, user_id=user_id)
    return jsonify({"game_id": game_id}), 201


@app.route("/api/games/<game_id>/clone", methods=["POST"])
def clone_game(game_id: str) -> object:
    """Clone a game's puzzle to start fresh with a new game.

    Copies puzzle, solution, difficulty from the source game.
    Resets board to the original puzzle state, clears notes, mistakes, etc.
    """
    storage = get_storage()
    game = storage.get_game(game_id)
    if game is None:
        return jsonify({"error": "Game not found"}), 404

    import copy
    puzzle = game.get("puzzle", [[0]*9]*9)
    solution = game.get("solution", [[0]*9]*9)
    difficulty = game.get("difficulty", 40)

    cloned = {
        "puzzle": copy.deepcopy(puzzle),
        "solution": copy.deepcopy(solution),
        "board": copy.deepcopy(puzzle),  # Fresh start — board = puzzle
        "given": [[puzzle[r][c] != 0 for c in range(9)] for r in range(9)],
        "notes": [[[False]*9 for _ in range(9)] for _ in range(9)],
        "undoStack": [],
        "redoStack": [],
        "difficulty": difficulty,
        "elapsed": 0,
        "mistakes": 0,
        "completed": False,
        "hintsUsed": 0,
        "archived": False,
        "tags": ["cloned"],
        "sourceGameId": game_id,
    }
    new_id = storage.create_game(cloned)
    return jsonify({"game_id": new_id, "source_game_id": game_id}), 201


@app.route("/api/games/<game_id>", methods=["GET"])
def get_game(game_id: str) -> object:
    """Retrieve a saved game's full state."""
    storage = get_storage()
    game = storage.get_game(game_id)
    if game is None:
        return jsonify({"error": "Game not found"}), 404
    return jsonify(game)


@app.route("/api/games/<game_id>", methods=["PUT"])
def save_game(game_id: str) -> object:
    """Update a saved game's full state."""
    data = request.get_json(force=True)
    storage = get_storage()
    try:
        storage.save_game(game_id, data)
    except KeyError:
        return jsonify({"error": "Game not found"}), 404
    return jsonify({"ok": True, "game_id": game_id})


@app.route("/api/games/<game_id>", methods=["DELETE"])
def delete_game(game_id: str) -> object:
    """Delete a saved game."""
    storage = get_storage()
    deleted = storage.delete_game(game_id)
    if not deleted:
        return jsonify({"error": "Game not found"}), 404
    return jsonify({"ok": True, "deleted": game_id})


@app.route("/api/games/<game_id>/rate", methods=["PUT"])
def rate_game(game_id: str) -> object:
    """Rate a game (1-5 stars). Only works on completed games."""
    storage = get_storage()
    game = storage.get_game(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404
    if not game.get("completed", False):
        return jsonify({"error": "Can only rate completed games"}), 400
    data = request.get_json(silent=True) or {}
    rating = data.get("rating")
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"error": "Rating must be an integer 1-5"}), 400
    storage.save_game(game_id, {"rating": rating})
    return jsonify({"ok": True, "game_id": game_id, "rating": rating})


@app.route("/api/games/<game_id>/archive", methods=["PUT"])
def archive_game(game_id: str) -> object:
    """Archive or unarchive a game."""
    storage = get_storage()
    game = storage.get_game(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json(silent=True) or {}
    archived = data.get("archived", True)
    storage.save_game(game_id, {"archived": archived})
    return jsonify({"ok": True, "game_id": game_id, "archived": archived})


@app.route("/api/games/<game_id>/certificate")
def completion_certificate(game_id: str) -> object:
    """Get a completion certificate for a finished game.

    Returns detailed game stats with a performance rating.
    Only available for completed games.
    """
    storage = get_storage()
    game = storage.get_game(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404
    if not game.get("completed"):
        return jsonify({"error": "Game not completed"}), 400

    difficulty = game.get("difficulty", 30)
    elapsed = game.get("elapsed", 0)
    mistakes = game.get("mistakes", 0)
    hints_used = game.get("hintsUsed", 0)

    # Difficulty label
    if difficulty <= 25:
        diff_label = "Easy"
    elif difficulty <= 35:
        diff_label = "Medium"
    elif difficulty <= 45:
        diff_label = "Hard"
    else:
        diff_label = "Expert"

    # Performance rating
    if mistakes == 0 and hints_used == 0:
        performance = "perfect"
    elif mistakes <= 1 and hints_used == 0 and elapsed < 120:
        performance = "excellent"
    elif mistakes <= 3 and elapsed < 300:
        performance = "good"
    else:
        performance = "completed"

    return jsonify({
        "game_id": game_id,
        "difficulty": difficulty,
        "difficulty_label": diff_label,
        "elapsed": elapsed,
        "mistakes": mistakes,
        "hintsUsed": hints_used,
        "rating": game.get("rating", 0),
        "performance": performance,
        "created_at": game.get("created_at"),
        "completed": True,
    })


@app.route("/api/games/<game_id>/progress")
def game_progress(game_id: str) -> object:
    """Get detailed progress metrics for a game.

    Returns:
        JSON with filled count, correct/incorrect cells, progress percentage.
    """
    storage = get_storage()
    game = storage.get_game(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    puzzle = game.get("puzzle", [[0]*9]*9)
    solution = game.get("solution", [[0]*9]*9)
    board = game.get("board", [[0]*9]*9)

    total_cells = 81
    given_count = sum(1 for r in range(9) for c in range(9) if puzzle[r][c] != 0)
    total_empty = total_cells - given_count

    filled = 0
    correct = 0
    incorrect = 0
    for r in range(9):
        for c in range(9):
            if puzzle[r][c] == 0 and board[r][c] != 0:
                filled += 1
                if board[r][c] == solution[r][c]:
                    correct += 1
                else:
                    incorrect += 1

    progress_pct = round(filled / total_empty * 100, 1) if total_empty > 0 else 100

    return jsonify({
        "filled": filled,
        "total_cells": total_cells,
        "total_empty": total_empty,
        "progress_pct": progress_pct,
        "correct": correct,
        "incorrect": incorrect,
    })


@app.route("/api/games/compare")
def compare_games() -> object:
    """Compare two games and show differences.

    Query parameters:
        a: First game ID
        b: Second game ID

    Returns:
        JSON with both game summaries and differences (b - a).
    """
    a_id = request.args.get("a")
    b_id = request.args.get("b")
    if not a_id or not b_id:
        return jsonify({"error": "Both 'a' and 'b' parameters are required"}), 400

    storage = get_storage()
    game_a = storage.get_game(a_id)
    game_b = storage.get_game(b_id)
    if not game_a or not game_b:
        return jsonify({"error": "Game not found"}), 404

    fields = ["difficulty", "elapsed", "mistakes", "hintsUsed", "rating"]
    summary_a = {f: game_a.get(f, 0) for f in fields}
    summary_a["game_id"] = a_id
    summary_b = {f: game_b.get(f, 0) for f in fields}
    summary_b["game_id"] = b_id

    differences = {f: summary_b[f] - summary_a[f] for f in fields}

    return jsonify({
        "game_a": summary_a,
        "game_b": summary_b,
        "differences": differences,
    })


@app.route("/api/solve", methods=["POST"])
def solve_board() -> object:
    """Solve a Sudoku board.

    Request body (JSON):
        board: 9x9 array of integers (0 = empty)

    Returns:
        JSON with the solved board, or an error if unsolvable.
    """
    data = request.get_json(silent=True) or {}
    board = data.get("board")
    if not isinstance(board, list) or len(board) != 9 or not all(isinstance(r, list) and len(r) == 9 for r in board):
        return jsonify({"error": "Board must be a 9x9 array"}), 400

    from sudoku import _has_conflicts, _solve, _count_solutions

    if _has_conflicts(board):
        return jsonify({"error": "Board has conflicts and cannot be solved"}), 400

    # Check for unique solution
    num_solutions = _count_solutions(board, limit=2)
    if num_solutions == 0:
        return jsonify({"error": "Board has no solution"}), 400

    # Solve it
    import copy
    solved = copy.deepcopy(board)
    _solve(solved)

    return jsonify({
        "solved": solved,
        "unique": num_solutions == 1,
        "num_solutions": num_solutions,
    })


@app.route("/api/hint", methods=["POST"])
def hint_board() -> object:
    """Find the next logical move for a Sudoku board.

    Uses naked single technique: finds an empty cell that has only one
    possible candidate based on row, column, and box constraints.

    Request body (JSON):
        board: 9x9 array of integers (0 = empty)

    Returns:
        JSON with the cell coordinates, value, and technique used.
    """
    data = request.get_json(silent=True) or {}
    board = data.get("board")
    if not isinstance(board, list) or len(board) != 9 or not all(isinstance(r, list) and len(r) == 9 for r in board):
        return jsonify({"error": "Board must be a 9x9 array"}), 400

    from sudoku import _has_conflicts

    if _has_conflicts(board):
        return jsonify({"error": "Board has conflicts"}), 400

    # Find naked singles — cells with only one possible candidate
    for r in range(9):
        for c in range(9):
            if board[r][c] != 0:
                continue
            # Calculate candidates
            used = set()
            # Row
            used.update(board[r])
            # Column
            used.update(board[i][c] for i in range(9))
            # Box
            br, bc = (r // 3) * 3, (c // 3) * 3
            for r2 in range(br, br + 3):
                for c2 in range(bc, bc + 3):
                    used.add(board[r2][c2])
            candidates = [n for n in range(1, 10) if n not in used]
            if len(candidates) == 1:
                return jsonify({
                    "row": r,
                    "col": c,
                    "value": candidates[0],
                    "technique": "naked_single",
                })

    # Find hidden singles — a number that can only go in one cell of a unit
    for unit_type, unit_cells in [
        ("row", [[(r, c) for c in range(9)] for r in range(9)]),
        ("column", [[(r, c) for r in range(9)] for c in range(9)]),
        ("box", [[(br + dr, bc + dc) for dr in range(3) for dc in range(3)]
                 for br in range(0, 9, 3) for bc in range(0, 9, 3)]),
    ]:
        for unit in unit_cells:
            for num in range(1, 10):
                # Skip if number already in unit
                if any(board[r][c] == num for r, c in unit):
                    continue
                possible_cells = []
                for r, c in unit:
                    if board[r][c] != 0:
                        continue
                    used = set()
                    used.update(board[r])
                    used.update(board[i][c] for i in range(9))
                    br2, bc2 = (r // 3) * 3, (c // 3) * 3
                    for r2 in range(br2, br2 + 3):
                        for c2 in range(bc2, bc2 + 3):
                            used.add(board[r2][c2])
                    if num not in used:
                        possible_cells.append((r, c))
                if len(possible_cells) == 1:
                    r, c = possible_cells[0]
                    return jsonify({
                        "row": r,
                        "col": c,
                        "value": num,
                        "technique": f"hidden_single_{unit_type}",
                    })

    # No logical move found — fall back to first empty cell
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                from sudoku import _solve, _count_solutions
                import copy
                solved = copy.deepcopy(board)
                _solve(solved)
                return jsonify({
                    "row": r,
                    "col": c,
                    "value": solved[r][c],
                    "technique": "backtracking",
                })

    return jsonify({"message": "Board is already complete"}), 200


@app.route("/api/best-times")
def best_times() -> object:
    """Get the best completion time per difficulty level.

    Returns a dict like {"30": 120, "40": 300} where keys are difficulty
    levels and values are the best (lowest) completion time in seconds.
    """
    storage = get_storage()
    games = storage.list_games(limit=500)
    best = {}
    for game in games:
        if not game.get("completed"):
            continue
        diff = str(game.get("difficulty", 40))
        elapsed = game.get("elapsed", 0)
        if diff not in best or elapsed < best[diff]:
            best[diff] = elapsed
    return jsonify(best)


@app.route("/api/stats")
def stats() -> object:
    """Get player statistics across all games.

    Returns total games, completed games, completion rate, total time,
    total mistakes, and average completion time.
    """
    storage = get_storage()
    games = storage.list_games(limit=500)
    total = len(games)
    completed = [g for g in games if g.get("completed")]
    completed_count = len(completed)
    total_time = sum(g.get("elapsed", 0) for g in games)
    total_mistakes = sum(g.get("mistakes", 0) for g in games)
    total_hints = sum(g.get("hintsUsed", 0) for g in games)
    avg_time = (
        sum(g["elapsed"] for g in completed) / completed_count
        if completed_count > 0
        else 0
    )

    # Per-difficulty breakdown
    diff_names = {30: "easy", 40: "medium", 50: "hard", 58: "expert"}
    by_difficulty = {}
    for diff_val, diff_name in diff_names.items():
        diff_games = [g for g in games if g.get("difficulty") == diff_val]
        diff_completed = [g for g in diff_games if g.get("completed")]
        by_difficulty[diff_name] = {
            "total": len(diff_games),
            "completed": len(diff_completed),
            "best_time": min((g["elapsed"] for g in diff_completed), default=0),
            "avg_time": round(
                sum(g["elapsed"] for g in diff_completed) / len(diff_completed), 1
            ) if diff_completed else 0,
            "avg_mistakes": round(
                sum(g.get("mistakes", 0) for g in diff_completed) / len(diff_completed), 1
            ) if diff_completed else 0,
        }

    # Average rating
    rated = [g for g in completed if g.get("rating", 0) > 0]
    avg_rating = round(
        sum(g["rating"] for g in rated) / len(rated), 1
    ) if rated else 0

    # Calculate achievements
    achievements = []
    if completed_count > 0:
        achievements.append("first_win")
    # Perfect game: 0 mistakes, 0 hints
    if any(g.get("mistakes", 0) == 0 and g.get("hintsUsed", 0) == 0
           for g in completed):
        achievements.append("perfect_game")
    # Speed run: completed in under 60s
    if any(g.get("elapsed", 0) < 60 for g in completed):
        achievements.append("speed_run")
    # No hints: completed without using any hints
    if any(g.get("hintsUsed", 0) == 0 for g in completed):
        achievements.append("no_hints")
    # Dedicated: 10+ completed games
    if completed_count >= 10:
        achievements.append("dedicated")
    # Expert winner: completed an expert puzzle
    if any(g.get("difficulty") == 58 and g.get("completed")
           for g in games):
        achievements.append("expert_winner")

    return jsonify({
        "total_games": total,
        "completed_games": completed_count,
        "completion_rate": completed_count / total if total > 0 else 0,
        "completion_pct": round(completed_count / total * 100, 1) if total > 0 else 0,
        "total_time": total_time,
        "total_mistakes": total_mistakes,
        "total_hints": total_hints,
        "avg_completion_time": round(avg_time, 1),
        "best_time": min((g["elapsed"] for g in completed), default=0),
        "avg_mistakes": round(
            sum(g.get("mistakes", 0) for g in completed) / completed_count, 1
        ) if completed_count > 0 else 0,
        "avg_rating": avg_rating,
        "by_difficulty": by_difficulty,
        "achievements": achievements,
    })


@app.route("/api/games/<game_id>/export")
def export_game(game_id: str) -> object:
    """Export a game as a shareable base64-encoded code."""
    storage = get_storage()
    game = storage.get_game(game_id)
    if game is None:
        return jsonify({"error": "Game not found"}), 404
    # Remove internal fields
    export_data = {k: v for k, v in game.items()
                   if k not in ("game_id", "created_at", "updated_at")}
    encoded = base64.urlsafe_b64encode(
        _json.dumps(export_data).encode()
    ).decode()
    return jsonify({"share_code": encoded})


@app.route("/api/games/import", methods=["POST"])
def import_game() -> object:
    """Import a game from a shareable base64-encoded code."""
    data = request.get_json(force=True)
    share_code = data.get("share_code", "")
    try:
        decoded = base64.urlsafe_b64decode(share_code.encode()).decode()
        state = _json.loads(decoded)
    except Exception:
        return jsonify({"error": "Invalid share code"}), 400
    storage = get_storage()
    game_id = storage.create_game(state)
    return jsonify({"game_id": game_id}), 201


@app.route("/api/validate", methods=["POST"])
def validate_board() -> object:
    """Validate a Sudoku board state.

    Request body (JSON):
        board: 9x9 array of integers (0 = empty)
        solution: 9x9 array (optional, for solution comparison)

    Returns:
        JSON with validity status, conflicts, and completion info.
    """
    data = request.get_json(silent=True) or {}
    board = data.get("board")
    if not isinstance(board, list) or len(board) != 9 or not all(isinstance(r, list) and len(r) == 9 for r in board):
        return jsonify({"error": "Board must be a 9x9 array"}), 400

    from sudoku import _has_conflicts, _count_solutions

    has_conflicts = _has_conflicts(board)
    filled = sum(1 for r in range(9) for c in range(9) if board[r][c] != 0)
    is_complete = filled == 81 and not has_conflicts

    # Find conflicting cells
    conflicts = []
    if has_conflicts:
        for i in range(9):
            for j in range(9):
                v = board[i][j]
                if v == 0:
                    continue
                # Check row
                if board[i].count(v) > 1:
                    conflicts.append([i, j])
                    continue
                # Check column
                if sum(1 for r in range(9) if board[r][j] == v) > 1:
                    conflicts.append([i, j])
                    continue
                # Check box
                br, bc = (i // 3) * 3, (j // 3) * 3
                count = 0
                for r2 in range(br, br + 3):
                    for c2 in range(bc, bc + 3):
                        if board[r2][c2] == v:
                            count += 1
                if count > 1:
                    conflicts.append([i, j])

    # Check solution uniqueness if board has no conflicts
    unique = None
    if not has_conflicts and 0 < filled < 81:
        unique = _count_solutions(board, limit=2) == 1

    return jsonify({
        "valid": not has_conflicts,
        "complete": is_complete,
        "filled": filled,
        "empty": 81 - filled,
        "conflicts": conflicts,
        "unique_solution": unique,
    })


@app.route("/api/leaderboard")
def leaderboard() -> object:
    """Get the top fastest completed games.

    Query parameters:
        limit: Number of entries (default 10, max 50).
        difficulty: Filter by difficulty level.

    Returns:
        JSON array of top games sorted by elapsed time (fastest first).
    """
    limit = min(int(request.args.get("limit", 10)), 50)
    difficulty = request.args.get("difficulty")
    storage = get_storage()
    games = storage.list_games(limit=500)
    completed = [g for g in games if g.get("completed")]
    if difficulty is not None:
        try:
            diff = int(difficulty)
            completed = [g for g in completed if g.get("difficulty") == diff]
        except (ValueError, TypeError):
            pass
    completed.sort(key=lambda g: g.get("elapsed", 999999))
    top = completed[:limit]
    return jsonify({
        "leaderboard": [
            {
                "game_id": g["game_id"],
                "difficulty": g.get("difficulty", 0),
                "elapsed": g.get("elapsed", 0),
                "mistakes": g.get("mistakes", 0),
                "hintsUsed": g.get("hintsUsed", 0),
                "rating": g.get("rating", 0),
                "created_at": g.get("created_at"),
                "completed": True,
            }
            for g in top
        ],
        "count": len(top),
    })


@app.route("/api/recommend-difficulty")
def recommend_difficulty() -> object:
    """Recommend a difficulty level based on player's past performance.

    Logic:
    - No completed games: suggest 30 (easy)
    - Best time < 60s on most-used difficulty: suggest harder (most_used + 10, max 58)
    - Average time > 300s on most-used difficulty: suggest easier (most_used - 10, min 20)
    - Otherwise: suggest current most-used difficulty

    Returns:
        JSON with recommended difficulty and reasoning.
    """
    storage = get_storage()
    games = storage.list_games(limit=500)
    completed = [g for g in games if g.get("completed")]

    if not completed:
        return jsonify({
            "recommended_difficulty": 30,
            "reasoning": "No completed games yet. Starting with medium difficulty.",
        })

    # Group by difficulty
    by_diff = {}
    for g in completed:
        d = g.get("difficulty", 30)
        by_diff.setdefault(d, []).append(g)

    # Find the difficulty the player uses most
    most_used = max(by_diff.keys(), key=lambda d: len(by_diff[d]))
    games_at_level = by_diff[most_used]
    best_time = min(g.get("elapsed", 999) for g in games_at_level)
    avg_time = sum(g.get("elapsed", 0) for g in games_at_level) / len(games_at_level)

    # Recommendation logic
    difficulties = sorted(by_diff.keys())
    max_diff = max(difficulties)
    min_diff = min(difficulties)

    if best_time < 60 and most_used < 58:
        rec = min(most_used + 10, 58)
        reasoning = f"Your best time at difficulty {most_used} is {best_time}s. Try a harder puzzle!"
    elif avg_time > 300 and most_used > 20:
        rec = max(most_used - 10, 20)
        reasoning = f"Your average time at difficulty {most_used} is {avg_time:.0f}s. Try an easier puzzle."
    else:
        rec = most_used
        reasoning = f"You're performing well at difficulty {most_used}. Keep going!"

    return jsonify({
        "recommended_difficulty": rec,
        "current_difficulty": most_used,
        "best_time": best_time,
        "avg_time": round(avg_time, 1),
        "completed_at_level": len(games_at_level),
        "reasoning": reasoning,
    })


@app.route("/api/analyze", methods=["POST"])
def analyze_puzzle() -> object:
    """Analyze a Sudoku puzzle and return detailed metrics.

    Request body (JSON):
        puzzle: 9x9 array of integers (0 = empty)
        solution: 9x9 array (optional, for solution verification)

    Returns:
        JSON with puzzle metrics: empty/filled cells, difficulty rating,
        unique solution flag, conflict detection.
    """
    data = request.get_json(silent=True) or {}
    board = data.get("puzzle")
    if not isinstance(board, list) or len(board) != 9 or not all(isinstance(r, list) and len(r) == 9 for r in board):
        return jsonify({"error": "Puzzle must be a 9x9 array"}), 400

    from sudoku import _has_conflicts, _count_solutions

    filled = sum(1 for r in range(9) for c in range(9) if board[r][c] != 0)
    empty = 81 - filled
    has_conflicts = _has_conflicts(board)

    # Difficulty rating: 1-5 based on empty cells
    if empty <= 25:
        difficulty_rating = 1  # Easy
    elif empty <= 35:
        difficulty_rating = 2  # Medium-Easy
    elif empty <= 45:
        difficulty_rating = 3  # Medium
    elif empty <= 52:
        difficulty_rating = 4  # Hard
    else:
        difficulty_rating = 5  # Expert

    # Check uniqueness (only if no conflicts and not empty)
    unique = None
    if not has_conflicts and 0 < filled < 81:
        unique = _count_solutions(board, limit=2) == 1

    return jsonify({
        "empty_cells": empty,
        "filled_cells": filled,
        "has_conflicts": has_conflicts,
        "unique_solution": unique,
        "difficulty_rating": difficulty_rating,
    })


@app.route("/api/history")
def game_history() -> object:
    """Get a chronological summary of all games.

    Query parameters:
        limit: Number of entries (default 20, max 100).
        completed: Filter by completion status ('true' or 'false').
        difficulty: Filter by difficulty level.

    Returns:
        JSON with history entries (newest first), count, and total.
    """
    limit = min(int(request.args.get("limit", 20)), 100)
    completed_filter = request.args.get("completed")
    difficulty_filter = request.args.get("difficulty")
    storage = get_storage()
    games = storage.list_games(limit=500)
    total = len(games)

    # Filter by completed
    if completed_filter is not None:
        is_completed = completed_filter.lower() == 'true'
        games = [g for g in games if g.get("completed", False) == is_completed]

    # Filter by difficulty
    if difficulty_filter is not None:
        try:
            diff = int(difficulty_filter)
            games = [g for g in games if g.get("difficulty") == diff]
        except (ValueError, TypeError):
            pass

    # Sort newest first
    games.sort(key=lambda g: g.get("created_at", ""), reverse=True)

    history = [
        {
            "game_id": g["game_id"],
            "difficulty": g.get("difficulty", 0),
            "elapsed": g.get("elapsed", 0),
            "completed": g.get("completed", False),
            "mistakes": g.get("mistakes", 0),
            "hintsUsed": g.get("hintsUsed", 0),
            "rating": g.get("rating", 0),
            "created_at": g.get("created_at"),
            "updated_at": g.get("updated_at"),
        }
        for g in games[:limit]
    ]

    return jsonify({
        "history": history,
        "count": len(history),
        "total": total,
    })


@app.route("/api/streaks")
def game_streaks() -> object:
    """Get current and best completion streaks.

    A streak is consecutive completed games (in creation order).
    An incomplete game breaks the streak.

    Returns:
        JSON with current_streak, best_streak, total_completions,
        total_games, and completion_rate.
    """
    storage = get_storage()
    games = storage.list_games(limit=500)
    # Sort by created_at ascending to get chronological order
    games.sort(key=lambda g: g.get("created_at", ""))

    current_streak = 0
    best_streak = 0
    running_streak = 0
    total_completions = 0

    for g in games:
        if g.get("completed", False):
            running_streak += 1
            total_completions += 1
            best_streak = max(best_streak, running_streak)
        else:
            running_streak = 0

    # Current streak is the running streak at the end
    current_streak = running_streak

    total = len(games)
    completion_rate = round(total_completions / total * 100, 1) if total > 0 else 0

    return jsonify({
        "current_streak": current_streak,
        "best_streak": best_streak,
        "total_completions": total_completions,
        "total_games": total,
        "completion_rate": completion_rate,
    })


@app.route("/api/stats/export")
def export_stats() -> object:
    """Export all player statistics as a downloadable JSON summary.

    Returns:
        JSON with comprehensive stats, achievements, leaderboard, and game history.
    """
    storage = get_storage()
    games = storage.list_games(limit=500)
    completed = [g for g in games if g.get("completed")]

    total = len(games)
    completed_count = len(completed)

    total_time = sum(g.get("elapsed", 0) for g in completed)
    total_mistakes = sum(g.get("mistakes", 0) for g in completed)
    total_hints = sum(g.get("hintsUsed", 0) for g in completed)

    by_difficulty = {}
    for g in completed:
        d = g.get("difficulty", 0)
        by_difficulty.setdefault(d, []).append(g)

    diff_summary = {}
    for d, dgames in sorted(by_difficulty.items()):
        diff_summary[d] = {
            "count": len(dgames),
            "best_time": min(g.get("elapsed", 0) for g in dgames),
            "avg_time": round(sum(g.get("elapsed", 0) for g in dgames) / len(dgames), 1),
            "avg_mistakes": round(sum(g.get("mistakes", 0) for g in dgames) / len(dgames), 1),
        }

    rated = [g for g in completed if g.get("rating", 0) > 0]
    avg_rating = round(sum(g["rating"] for g in rated) / len(rated), 1) if rated else 0

    achievements = []
    if completed_count > 0:
        achievements.append("first_win")
    if any(g.get("mistakes", 0) == 0 and g.get("hintsUsed", 0) == 0 for g in completed):
        achievements.append("perfect_game")
    if any(g.get("elapsed", 0) < 60 for g in completed):
        achievements.append("speed_run")
    if any(g.get("hintsUsed", 0) == 0 for g in completed):
        achievements.append("no_hints")
    if completed_count >= 10:
        achievements.append("dedicated")
    if any(g.get("difficulty") == 58 and g.get("completed") for g in games):
        achievements.append("expert_winner")

    # Mini leaderboard
    completed.sort(key=lambda g: g.get("elapsed", 999999))
    top5 = [
        {
            "game_id": g["game_id"],
            "difficulty": g.get("difficulty", 0),
            "elapsed": g.get("elapsed", 0),
            "mistakes": g.get("mistakes", 0),
        }
        for g in completed[:5]
    ]

    return jsonify({
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_games": total,
            "completed_games": completed_count,
            "completion_rate": round(completed_count / total * 100, 1) if total > 0 else 0,
            "total_time": total_time,
            "total_mistakes": total_mistakes,
            "total_hints": total_hints,
            "best_time": min((g["elapsed"] for g in completed), default=0),
            "avg_completion_time": round(total_time / completed_count, 1) if completed_count > 0 else 0,
            "avg_mistakes": round(total_mistakes / completed_count, 1) if completed_count > 0 else 0,
            "avg_rating": avg_rating,
        },
        "by_difficulty": diff_summary,
        "achievements": achievements,
        "top_5_fastest": top5,
    })


@app.route("/api/profile")
def player_profile() -> object:
    """Get a comprehensive player profile.

    Aggregates stats, achievements, streaks, recommendations, and level.
    """
    storage = get_storage()
    games = storage.list_games(limit=500)
    completed = [g for g in games if g.get("completed")]

    total = len(games)
    completed_count = len(completed)
    total_time = sum(g.get("elapsed", 0) for g in completed)
    total_mistakes = sum(g.get("mistakes", 0) for g in completed)
    total_hints = sum(g.get("hintsUsed", 0) for g in completed)

    # By difficulty
    by_diff = {}
    for g in completed:
        d = g.get("difficulty", 0)
        by_diff.setdefault(d, []).append(g)
    diff_summary = {}
    for d, dgames in sorted(by_diff.items()):
        diff_summary[d] = {
            "count": len(dgames),
            "best_time": min(g.get("elapsed", 0) for g in dgames),
            "avg_time": round(sum(g.get("elapsed", 0) for g in dgames) / len(dgames), 1),
        }

    # Achievements
    achievements = []
    if completed_count > 0:
        achievements.append("first_win")
    if any(g.get("mistakes", 0) == 0 and g.get("hintsUsed", 0) == 0 for g in completed):
        achievements.append("perfect_game")
    if any(g.get("elapsed", 0) < 60 for g in completed):
        achievements.append("speed_run")
    if any(g.get("hintsUsed", 0) == 0 for g in completed):
        achievements.append("no_hints")
    if completed_count >= 10:
        achievements.append("dedicated")
    if any(g.get("difficulty") == 58 and g.get("completed") for g in games):
        achievements.append("expert_winner")

    # Streaks
    sorted_games = sorted(games, key=lambda g: g.get("created_at", ""))
    current_streak = 0
    best_streak = 0
    running = 0
    for g in sorted_games:
        if g.get("completed"):
            running += 1
            best_streak = max(best_streak, running)
        else:
            running = 0
    current_streak = running

    # Rating
    rated = [g for g in completed if g.get("rating", 0) > 0]
    avg_rating = round(sum(g["rating"] for g in rated) / len(rated), 1) if rated else 0

    # Recommendation
    if not completed:
        rec_diff = 30
        rec_reason = "No completed games yet. Starting with medium difficulty."
    else:
        most_used = max(by_diff.keys(), key=lambda d: len(by_diff[d]))
        games_at_level = by_diff[most_used]
        best_time = min(g.get("elapsed", 999) for g in games_at_level)
        avg_time = sum(g.get("elapsed", 0) for g in games_at_level) / len(games_at_level)
        if best_time < 60 and most_used < 58:
            rec_diff = min(most_used + 10, 58)
            rec_reason = f"Your best time at difficulty {most_used} is {best_time}s. Try harder!"
        elif avg_time > 300 and most_used > 20:
            rec_diff = max(most_used - 10, 20)
            rec_reason = f"Your average at difficulty {most_used} is {avg_time:.0f}s. Try easier."
        else:
            rec_diff = most_used
            rec_reason = f"You're performing well at difficulty {most_used}. Keep going!"

    # Player level (1 per completion, cap at 100)
    level = min(completed_count, 100)

    return jsonify({
        "total_games": total,
        "completed_games": completed_count,
        "completion_pct": round(completed_count / total * 100, 1) if total > 0 else 0,
        "total_time": total_time,
        "total_mistakes": total_mistakes,
        "total_hints": total_hints,
        "best_time": min((g["elapsed"] for g in completed), default=0),
        "avg_completion_time": round(total_time / completed_count, 1) if completed_count > 0 else 0,
        "avg_rating": avg_rating,
        "by_difficulty": diff_summary,
        "achievements": achievements,
        "current_streak": current_streak,
        "best_streak": best_streak,
        "recommended_difficulty": rec_diff,
        "recommendation_reasoning": rec_reason,
        "level": level,
    })


# --- Tutorial endpoints ---


@app.route("/api/tutorials/lessons")
def tutorial_lessons():
    """List all available tutorial lessons."""
    return jsonify({"lessons": get_all_lessons()})


@app.route("/api/tutorials/lessons/<lesson_id>")
def tutorial_lesson_detail(lesson_id: str):
    """Get detailed lesson content including steps."""
    lesson = get_lesson(lesson_id)
    if lesson is None:
        return jsonify({"error": "Lesson not found"}), 404
    return jsonify(lesson)


@app.route("/api/tutorials/progress")
def tutorial_progress():
    """Get the current user's tutorial progress."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    storage = get_storage()
    progress = storage.get_tutorial_progress(user_id)
    if progress is None:
        progress = get_initial_progress()
    return jsonify(progress)


@app.route("/api/tutorials/progress", methods=["POST"])
def update_tutorial_progress():
    """Update tutorial progress for the current user."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request"}), 400

    storage = get_storage()
    progress = storage.get_tutorial_progress(user_id)
    if progress is None:
        progress = get_initial_progress()

    lesson_id = data.get("lesson_id")
    step_index = data.get("step_index")
    status = data.get("status", "completed")

    if status == "completed":
        if step_index is not None:
            step_key = f"{lesson_id}:{step_index}"
            if step_key not in progress["completed_steps"]:
                progress["completed_steps"].append(step_key)
            if lesson_id not in progress["started_lessons"]:
                progress["started_lessons"].append(lesson_id)
        else:
            if lesson_id not in progress["completed_lessons"]:
                progress["completed_lessons"].append(lesson_id)

    storage.save_tutorial_progress(user_id, progress)
    return jsonify(progress)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
