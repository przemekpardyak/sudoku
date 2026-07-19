"""Flask web application for playing Sudoku."""
from flask import Flask, jsonify, render_template, request

from sudoku import generate_puzzle

app = Flask(__name__)


@app.route("/")
def index() -> str:
    """Render the main game page."""
    return render_template("index.html")


@app.route("/api/new-game")
def new_game() -> object:
    """Generate a new sudoku puzzle and return it as JSON."""
    difficulty = int(request.args.get("difficulty", 40))
    puzzle, solution = generate_puzzle(difficulty=difficulty)
    return jsonify({"puzzle": puzzle, "solution": solution})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
