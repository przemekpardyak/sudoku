# 🎯 Sudoku

A modern, interactive Sudoku web application built with **Python** and **Flask**.
Generate fresh puzzles, play in your browser, and track your time and mistakes.

![Tech](https://img.shields.io/badge/Python-3.11-blue) ![Tech](https://img.shields.io/badge/Flask-3.0.3-black)

---

## ✨ Features

### Core Gameplay
- **Procedural Puzzle Generation** — every game produces a unique, solvable Sudoku via a backtracking algorithm
- **4 Difficulty Levels** — Easy, Medium, Hard, Expert (30–58 empty cells)
- **Smart Highlighting** — selecting a cell highlights its row, column, 3×3 box, and all matching numbers
- **Real-time Validation** — incorrect entries are flagged instantly in red
- **Mistake Tracker** — keeps count of wrong placements
- **Check Button** — scan the entire board for errors at any time
- **3×3 Box Dividers** — clear visual grid lines separating the nine 3×3 boxes
- **Built-in Timer** — tracks elapsed time; win screen shows your final stats
- **Modern UI** — dark glassmorphism theme, gradient accents, smooth micro-animations

### Pencil Marks (Notes)
- Toggle between **Final** (✏️) and **Notes** (📝) mode using the buttons in the right panel, or press `N`
- In **Notes mode**, clicking a number (1–9) toggles a small pencil mark in the selected cell's 3×3 mini-grid
- In **Final mode**, clicking a number places the big number. This hides the cell's pencil marks and auto-removes that same digit from pencil marks in the same row, column, and 3×3 box
- Erasing a final number reveals the preserved pencil marks again

### Smart Numpad
- Number pad buttons **auto-disable** when all 9 instances of a digit have been placed on the board
- Disabled buttons are greyed out and non-interactive
- Buttons re-enable automatically when a digit is removed

### Undo / Redo
- Full **undo/redo** support for every action: placing numbers, toggling notes, erasing, and applying hints
- Up to **200 history snapshots** tracked (board state, notes, given cells, mistakes)
- Buttons in the panel auto-disable when the stack is empty
- Starting a new game clears both stacks

### Hint (Press to Preview)
- **Press the Hint button** — a random empty cell reveals its correct number in **amber/orange** with a glowing border
- **Release the button** — the preview stays; nothing is committed yet
- **Click the amber cell** to apply the hint (committed as a permanent given)
- **Click anywhere else** or **press Escape** to dismiss the preview without applying

---

## 🎮 How to Play

1. Click any empty cell to select it (or use arrow keys to navigate).
2. Toggle between **Final** and **Notes** mode using the buttons in the right panel (or press `N`).
3. Enter a number (1–9) by:
   - Clicking the on-screen number pad, **or**
   - Pressing the corresponding key on your keyboard.
4. To erase a number, press **Backspace/Delete** or click the **⌫** button.
5. The board flags incorrect numbers in red — try again!
6. Use the tools on the right panel when needed:
   - **Check** — highlights all current errors
   - **Hint** — press to preview a correct cell, then click it to apply (or dismiss)
   - **Undo / Redo** — revert or reapply your last actions
7. Fill every cell correctly to win. Your time and mistake count are shown on the win screen.

### Using Pencil Marks (Notes Mode)

- Toggle between **Final** (✏️) and **Notes** (📝) mode using the buttons in the right panel, or press `N` on your keyboard.
- In **Notes mode**, clicking a number (1–9) toggles a small pencil mark in the selected cell's 3×3 mini-grid.
- In **Final mode**, clicking a number places the big number. This hides the cell's pencil marks and auto-removes the same digit from pencil marks in the row, column, and 3×3 box.
- Press **Backspace** or click **⌫** to erase — if the cell has a final number, only the number is removed and preserved pencil marks reappear. Pressing erase again clears all pencil marks.

### Using the Hint

1. **Press** (click and hold) the Hint button — a random empty cell lights up in amber showing its correct number.
2. **Release** the button — the preview stays on screen.
3. **Click the amber cell** to commit the hint (it becomes a permanent given and is added to the undo history).
4. To **dismiss without applying**, click anywhere else on the board or press `Escape`.

### Using Undo / Redo

- Click the **↶ Undo** button to revert your last action (or press `Ctrl+Z`)
- Click the **↷ Redo** button to reapply a reverted action (or press `Ctrl+Y` / `Ctrl+Shift+Z`)
- Works for all actions: placing numbers, toggling notes, erasing, and applying hints
- Up to 200 steps are tracked

### Difficulty Levels

| Level   | Empty Cells | Description                          |
|---------|-------------|--------------------------------------|
| Easy    | 30          | Few blanks, great for beginners       |
| Medium  | 40          | Balanced challenge                   |
| Hard    | 50          | Tough logical deductions required    |
| Expert  | 58          | Minimal clues, for seasoned players |

---

## 📁 Project Structure

```
sudoku/
├── app.py              # Flask application and API endpoints
├── sudoku.py           # Puzzle generator & backtracking solver
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── static/
│   ├── styles.css      # Dark glassmorphism theme & animations
│   └── app.js          # Game logic: rendering, input, validation, undo/redo, hints
└── templates/
    └── index.html      # Main game UI
```

### File Responsibilities

| File               | Purpose                                                              |
|--------------------|----------------------------------------------------------------------|
| `app.py`           | Flask server exposing `/` (game page) and `/api/new-game` (puzzle)  |
| `sudoku.py`        | Core logic: `generate_puzzle()`, `generate_solved_board()`, `_solve()` |
| `templates/index.html` | HTML structure: board, numpad, mode toggle, undo/redo, hint, win modal |
| `static/styles.css`    | Visual design: layout, colors, animations, disabled states, hint preview |
| `static/app.js`        | Client logic: cell selection, number/notes placement, undo/redo, numpad disable, hint preview, timer, win detection |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+** (tested with 3.11)
- **pip** (Python package manager)

### Standard Installation & Running

```bash
# 1. Navigate to the project folder
cd /usr/local/google/home/ppardyak/Dogfood/sudoku

# 2. (Optional) Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate     # on Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the Flask server
python3 app.py
```

The app will be available at **[http://localhost:5000](http://localhost:5000)**.

### Alternative: Virtualenv Without `ensurepip` (Corporate Environments)

If `python3 -m venv` fails because `ensurepip` is not available (common in restricted corporate environments), you can bootstrap pip manually:

```bash
# 1. Navigate to the project folder
cd /usr/local/google/home/ppardyak/Dogfood/sudoku

# 2. Create a venv without pip
python3 -m venv --without-pip venv

# 3. Bootstrap pip via get-pip.py
curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
venv/bin/python3 /tmp/get-pip.py --quiet

# 4. Install Flask into the venv
venv/bin/python3 -m pip install -r requirements.txt

# 5. Start the Flask server using the venv Python
venv/bin/python3 app.py
```

### Development Mode

The server runs in debug mode by default (`app.run(debug=True)`), so changes to
Python files will auto-reload the server. Static files (JS/CSS) are served as-is —
do a hard refresh in your browser (`Ctrl+Shift+R`) after editing them.

---

## ⌨️ Keyboard Shortcuts

| Key               | Action                          |
|-------------------|---------------------------------|
| `1` – `9`         | Place the number in the selected cell (final or notes mode) |
| `Backspace` / `Delete` / `0` | Erase the selected cell       |
| `N`               | Toggle between Final and Notes mode |
| `Ctrl+Z`          | Undo last action                |
| `Ctrl+Y` or `Ctrl+Shift+Z` | Redo last undone action  |
| `Escape`          | Dismiss hint preview            |
| `↑` `↓` `←` `→`   | Move the selection between cells |

---

## 🔌 API Reference

### `GET /`

Returns the main HTML game page.

### `GET /api/new-game?difficulty=<int>`

Generates a new Sudoku puzzle and its solution.

| Parameter     | Type | Default | Description                                   |
|---------------|------|---------|-----------------------------------------------|
| `difficulty`  | int  | `40`    | Number of cells to remove (30–58 recommended) |

**Response:**

```json
{
  "puzzle": [[6, 0, 1, ...], ...],
  "solution": [[6, 9, 1, ...], ...]
}
```

- `puzzle`: 9×9 grid where `0` represents an empty cell
- `solution`: 9×9 grid with the complete, solved board

---

## 🧠 How Puzzle Generation Works

The generator in [`sudoku.py`](sudoku.py) uses a classic **backtracking algorithm**:

1. **Fill diagonal 3×3 boxes** with random permutations of 1–9.
   (Diagonal boxes don't share rows/columns, so they can be filled independently.)
2. **Solve the rest** via backtracking to produce a fully solved board.
3. **Remove cells** randomly up to the requested difficulty count.

This guarantees every generated puzzle has a valid unique solution.

---

## 🛠️ Troubleshooting

<details>
<summary><b>ModuleNotFoundError: No module named 'flask'</b></summary>

Flask isn't installed. Run:

```bash
pip install -r requirements.txt
```

If pip is unavailable, install pip first:

```bash
python3 -m ensurepip --upgrade
```

If `ensurepip` is not available, use the alternative venv method in [Getting Started](#alternative-virtualenv-without-ensurepip-corporate-environments).

</details>

<details>
<summary><b>"The virtual environment was not created successfully because ensurepip is not available"</b></summary>

On Debian/Ubuntu systems, either install the venv package:

```bash
apt install python3.11-venv
```

Or create the venv without pip and bootstrap it manually:

```bash
python3 -m venv --without-pip venv
curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
venv/bin/python3 /tmp/get-pip.py --quiet
venv/bin/python3 -m pip install -r requirements.txt
```

</details>

<details>
<summary><b>Port 5000 already in use</b></summary>

Another process is using the port. Either stop it or change the port in `app.py`:

```python
app.run(debug=True, host="0.0.0.0", port=5001)
```

</details>

<details>
<summary><b>Corporate environment blocking pip installs</b></summary>

If you're behind a package install restriction (e.g., Corp Airlock), either:
- Use a pre-approved virtual environment image, or
- Request an exception at your organization's package governance portal.
- Alternatively, bootstrap pip via `get-pip.py` inside a `--without-pip` venv (see [Getting Started](#alternative-virtualenv-without-ensurepip-corporate-environments)).

</details>

<details>
<summary><b>Changes not showing in browser</b></summary>

Static files (JS/CSS) are cached by the browser. Do a **hard refresh**:
- **Windows/Linux**: `Ctrl+Shift+R`
- **Mac**: `Cmd+Shift+R`

</details>

---

## 📝 License

This project is provided as-is for educational and personal use.

---

<p align="center">Built with 🧡 using Flask</p>
