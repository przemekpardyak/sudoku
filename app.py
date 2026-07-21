"""Flask web application for playing Sudoku with game persistence."""
from flask import Flask, jsonify, render_template, request

from storage import get_storage
from sudoku import generate_puzzle

app = Flask(__name__)


@app.route("/")
def index() -> str:
    """Render the main game page."""
    return render_template("index.html")


@app.route("/api/new-game")
def new_game() -> object:
    """Generate a new sudoku puzzle and return it as JSON.

    If a game_id is provided (via the ?game_id= query param), the new game
    is created in storage with that ID. Otherwise a new game is created server-side.
    """
    difficulty = int(request.args.get("difficulty", 40))
    puzzle, solution = generate_puzzle(difficulty=difficulty)
    return jsonify({"puzzle": puzzle, "solution": solution})


# --- Game persistence endpoints ---


@app.route("/api/games", methods=["GET"])
def list_games() -> object:
    """List saved games (metadata only — no board/solution data)."""
    limit = int(request.args.get("limit", 50))
    storage = get_storage()
    games = storage.list_games(limit=limit)
    return jsonify({"games": games})


@app.route("/api/games", methods=["POST"])
def create_game() -> object:
    """Create a new saved game with full state."""
    data = request.get_json(force=True)
    storage = get_storage()
    game_id = storage.create_game(data)
    return jsonify({"game_id": game_id}), 201


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


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
