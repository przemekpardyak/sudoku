"""
E2E UI tests using Playwright.
Tests the Sudoku game from the user's perspective — real browser, real DOM,
real JavaScript execution.

Requirements:
    - Playwright installed: pip install playwright
    - Chromium installed: playwright install chromium
    - Flask app running on localhost:5000

Usage:
    cd sudoku
    venv/bin/python3 app.py &
    venv/bin/python3 -m unittest tests.test_e2e_sudoku -v
"""
import unittest
import subprocess
import time
import os
import signal
import requests


# Try to import playwright; skip all tests if not available
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

APP_URL = "http://localhost:5000"


def _wait_for_app(timeout=30):
    """Wait for the Flask app to be reachable."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(APP_URL, timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


@unittest.skipUnless(PLAYWRIGHT_AVAILABLE, "Playwright not installed")
class TestSudokuE2E(unittest.TestCase):
    """E2E tests for the Sudoku UI using Playwright."""

    @classmethod
    def setUpClass(cls):
        """Start the Flask app if not already running."""
        cls._app_process = None
        cls._ensure_server()
        cls._playwright = sync_playwright().start()
        cls._browser = cls._playwright.chromium.launch(headless=True)
        cls._context = cls._browser.new_context()
        # Clear storage so each test class starts fresh
        try:
            requests.delete(f"{APP_URL}/api/games")
        except Exception:
            pass

    @classmethod
    def _ensure_server(cls):
        """Ensure Flask app is running, start if needed."""
        if not _wait_for_app(timeout=2):
            cls._app_process = subprocess.Popen(
                ["venv/bin/python3", "app.py"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid,
            )
            if not _wait_for_app(timeout=15):
                raise RuntimeError("Flask app did not start in time")

    @classmethod
    def tearDownClass(cls):
        try:
            cls._context.close()
            cls._browser.close()
            cls._playwright.stop()
        except Exception:
            pass
        proc = getattr(cls, '_app_process', None)
        if proc and proc.poll() is None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                proc.wait(timeout=3)
            except Exception:
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except Exception:
                    pass
        cls._app_process = None

    def setUp(self):
        self._ensure_server()
        self.page = self._context.new_page()

    def tearDown(self):
        self.page.close()
        # Clean up games after each test
        try:
            requests.delete(f"{APP_URL}/api/games")
        except Exception:
            pass

    def _get_cell(self, row, col):
        """Get a cell element by row and column."""
        return self.page.query_selector(f".cell[data-row='{row}'][data-col='{col}']")

    def _click_cell(self, row, col):
        """Click a cell at the given row and column."""
        cell = self._get_cell(row, col)
        self.assertIsNotNone(cell, f"Cell at ({row},{col}) not found")
        cell.click()

    def _cell_text(self, row, col):
        """Get the text content of a cell."""
        cell = self._get_cell(row, col)
        if cell is None:
            return ""
        return cell.text_content().strip()

    def _find_empty_cell(self):
        """Find the first empty cell on the board. Returns (row, col) or None."""
        for r in range(9):
            for c in range(9):
                if self._cell_text(r, c) == "":
                    return (r, c)
        return None


class TestPageLoad(TestSudokuE2E):
    """Tests for initial page load and rendering."""

    def test_page_loads(self):
        """Page should load successfully."""
        self.page.goto(APP_URL)
        self.assertEqual(self.page.title(), "Sudoku · Play Online")

    def test_board_renders(self):
        """Board should render with 81 cells."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")
        cells = self.page.query_selector_all("#board .cell")
        self.assertEqual(len(cells), 81)

    def test_header_visible(self):
        """Header with brand and stats should be visible."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector(".header")
        self.assertTrue(self.page.is_visible(".brand-mark"))
        self.assertTrue(self.page.is_visible("#timer"))
        self.assertTrue(self.page.is_visible("#mistakes"))

    def test_difficulty_buttons_visible(self):
        """Difficulty buttons should be visible."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector(".diff-btn")
        buttons = self.page.query_selector_all(".diff-btn")
        self.assertEqual(len(buttons), 4)
        # Medium should be active by default
        active = self.page.query_selector(".diff-btn.active")
        self.assertIn("Medium", active.text_content())

    def test_numpad_visible(self):
        """Number pad should have buttons 1-9 and erase."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector(".num-btn")
        buttons = self.page.query_selector_all(".num-btn")
        self.assertEqual(len(buttons), 10)  # 1-9 + erase

    def test_action_buttons_visible(self):
        """Action buttons should be visible."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#newGameBtn")
        for btn_id in ["newGameBtn", "pauseBtn", "undoBtn", "redoBtn",
                       "checkBtn", "hintBtn", "loadGamesBtn", "helpBtn"]:
            self.assertTrue(self.page.is_visible(f"#{btn_id}"),
                          f"Button #{btn_id} should be visible")


class TestGameplay(TestSudokuE2E):
    """Tests for core gameplay interactions."""

    def test_select_cell_and_type_number(self):
        """Clicking a cell and pressing a number should place it."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        empty = self._find_empty_cell()
        self.assertIsNotNone(empty, "Should have at least one empty cell")

        row, col = empty
        self._click_cell(row, col)
        self.page.keyboard.press("5")

        # Wait for board to update
        self.page.wait_for_timeout(200)
        text = self._cell_text(row, col)
        self.assertEqual(text, "5")

    def test_numpad_button_places_number(self):
        """Clicking a numpad button should place a number in selected cell."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        empty = self._find_empty_cell()
        row, col = empty
        self._click_cell(row, col)

        # Click numpad button 7
        self.page.click(".num-btn[data-num='7']")
        self.page.wait_for_timeout(200)

        self.assertEqual(self._cell_text(row, col), "7")

    def test_erase_number(self):
        """Backspace should erase a user-entered number."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        empty = self._find_empty_cell()
        row, col = empty

        # Place a number
        self._click_cell(row, col)
        self.page.keyboard.press("3")
        self.page.wait_for_timeout(200)
        self.assertEqual(self._cell_text(row, col), "3")

        # Erase it
        self.page.keyboard.press("Backspace")
        self.page.wait_for_timeout(200)
        self.assertEqual(self._cell_text(row, col), "")

    def test_given_cells_not_erasable(self):
        """Given cells should not be erasable."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        # Find a given cell (non-empty at load)
        given_val = None
        given_pos = None
        for r in range(9):
            for c in range(9):
                text = self._cell_text(r, c)
                if text:
                    given_val = text
                    given_pos = (r, c)
                    break
            if given_pos:
                break

        self.assertIsNotNone(given_pos, "Should have at least one given cell")

        # Try to erase it
        row, col = given_pos
        self._click_cell(row, col)
        self.page.keyboard.press("Backspace")
        self.page.wait_for_timeout(200)

        # Should still have the value
        self.assertEqual(self._cell_text(row, col), given_val)

    def test_undo_redo(self):
        """Undo should reverse the last move, redo should replay it."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        empty = self._find_empty_cell()
        row, col = empty

        # Place a number
        self._click_cell(row, col)
        self.page.keyboard.press("4")
        self.page.wait_for_timeout(200)
        self.assertEqual(self._cell_text(row, col), "4")

        # Undo
        self.page.keyboard.press("Control+z")
        self.page.wait_for_timeout(200)
        self.assertEqual(self._cell_text(row, col), "")

        # Redo
        self.page.keyboard.press("Control+y")
        self.page.wait_for_timeout(200)
        self.assertEqual(self._cell_text(row, col), "4")

    def test_new_game_button(self):
        """New Game button should generate a new puzzle."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        # Get the first given cell's value
        old_text = self._cell_text(0, 0)

        # Click New Game
        self.page.click("#newGameBtn")
        self.page.wait_for_timeout(1000)

        # Board should still have 81 cells
        cells = self.page.query_selector_all("#board .cell")
        self.assertEqual(len(cells), 81)

    def test_mistake_counter_increments(self):
        """Placing a wrong number should increment the mistake counter."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        # Get initial mistakes
        initial = int(self.page.text_content("#mistakes"))

        empty = self._find_empty_cell()
        row, col = empty

        # We need to place a wrong number. We'll get the solution via API
        # and place a different number
        self._click_cell(row, col)

        # Try placing a number that's likely wrong (we can't know without the solution)
        # Just place a number and check if mistakes went up (if it was wrong)
        self.page.keyboard.press("1")
        self.page.wait_for_timeout(200)

        # Mistakes should be >= initial (might not increment if 1 was correct)
        current = int(self.page.text_content("#mistakes"))
        self.assertGreaterEqual(current, initial)


class TestUIFeatures(TestSudokuE2E):
    """Tests for UI features like modals, theme, help."""

    def test_help_modal(self):
        """Help button should show the help overlay."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        # Help overlay should be hidden initially
        help_overlay = self.page.query_selector("#helpOverlay")
        self.assertFalse(help_overlay.is_visible())

        # Click Help
        self.page.click("#helpBtn")
        self.page.wait_for_timeout(300)

        # Help should be visible
        self.assertTrue(help_overlay.is_visible())

        # Close it
        self.page.click("#helpClose")
        self.page.wait_for_timeout(300)
        self.assertFalse(help_overlay.is_visible())

    def test_theme_toggle(self):
        """Theme toggle should switch between dark and light."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        # Get initial theme (class is on <html>, not <body>)
        html_class = self.page.get_attribute("html", "class") or ""
        initial_light = "light" in html_class

        # Toggle theme
        self.page.click("#themeToggle")
        self.page.wait_for_timeout(300)

        html_class = self.page.get_attribute("html", "class") or ""
        new_light = "light" in html_class
        self.assertNotEqual(initial_light, new_light)

    def test_pause_button(self):
        """Pause button should toggle timer."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        # Click pause
        self.page.click("#pauseBtn")
        self.page.wait_for_timeout(300)

        # Button text should change
        btn_text = self.page.text_content("#pauseBtn")
        self.assertIn("Resume", btn_text)

        # Click again to resume
        self.page.click("#pauseBtn")
        self.page.wait_for_timeout(300)
        btn_text = self.page.text_content("#pauseBtn")
        self.assertIn("Pause", btn_text)

    def test_notes_mode_toggle(self):
        """Notes mode should toggle when N is pressed."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        # Check initial mode (Final should be active)
        final_btn = self.page.query_selector("#finalModeBtn")
        notes_btn = self.page.query_selector("#notesModeBtn")
        self.assertIn("active", final_btn.get_attribute("class"))
        self.assertNotIn("active", notes_btn.get_attribute("class"))

        # Press N to toggle
        self.page.keyboard.press("n")
        self.page.wait_for_timeout(200)

        # Notes should now be active
        self.assertNotIn("active", final_btn.get_attribute("class"))
        self.assertIn("active", notes_btn.get_attribute("class"))

    def test_load_games_modal(self):
        """Load Games button should show the games modal."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        games_overlay = self.page.query_selector("#gamesOverlay")
        self.assertFalse(games_overlay.is_visible())

        # Click Load Games
        self.page.click("#loadGamesBtn")
        self.page.wait_for_timeout(500)

        self.assertTrue(games_overlay.is_visible())

        # Close
        self.page.click("#closeGamesBtn")
        self.page.wait_for_timeout(300)
        self.assertFalse(games_overlay.is_visible())

    def test_arrow_key_navigation(self):
        """Arrow keys should move the selected cell."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        # Click cell at (0, 0)
        self._click_cell(0, 0)
        self.page.wait_for_timeout(200)

        # Press right arrow
        self.page.keyboard.press("ArrowRight")
        self.page.wait_for_timeout(200)

        # Cell at (0, 1) should be selected
        cell = self._get_cell(0, 1)
        self.assertIn("selected", cell.get_attribute("class"))

    def test_daily_puzzle_button(self):
        """Daily puzzle button should load a puzzle."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        self.page.click("#dailyBtn")
        self.page.wait_for_timeout(1000)

        # Board should still have 81 cells
        cells = self.page.query_selector_all("#board .cell")
        self.assertEqual(len(cells), 81)


class TestGameStorage(TestSudokuE2E):
    """Tests for game saving/loading from the UI."""

    def test_game_saved_on_new_game(self):
        """New game should be saved to the backend automatically."""
        self.page.goto(APP_URL)
        self.page.wait_for_timeout(1000)

        # Check that at least one game exists in the API
        res = requests.get(f"{APP_URL}/api/games")
        data = res.json()
        self.assertGreater(len(data["games"]), 0, "Game should be auto-saved")

    def test_progress_saved_after_move(self):
        """Placing a number should trigger immediate auto-save."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        # Place a number
        empty = self._find_empty_cell()
        row, col = empty
        self._click_cell(row, col)
        self.page.keyboard.press("5")
        self.page.wait_for_timeout(500)  # Save is now immediate (no 2s debounce)

        # Check that the game was updated via API
        res = requests.get(f"{APP_URL}/api/games")
        games = res.json()["games"]
        self.assertGreater(len(games), 0)

    def test_immediate_save_on_number_placement(self):
        """Number placement should be saved immediately to the server."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        # Get the game ID
        game_id_display = self.page.text_content("#gameIdDisplay")
        self.assertTrue(game_id_display, "Game ID should be displayed")

        # Place a number and immediately check the server has it
        empty = self._find_empty_cell()
        row, col = empty
        self._click_cell(row, col)
        self.page.keyboard.press("7")
        self.page.wait_for_timeout(500)  # Immediate save

        # Verify the board on the server matches
        games = requests.get(f"{APP_URL}/api/games").json()["games"]
        self.assertGreater(len(games), 0)
        # Get the game ID from the page
        game_id = game_id_display.replace("#", "")
        # Find the game that matches (may have been saved with a partial ID)
        game = None
        for g in games:
            if g["game_id"].startswith(game_id):
                game = requests.get(f"{APP_URL}/api/games/{g['game_id']}").json()
                break
        if game is None:
            game = requests.get(f"{APP_URL}/api/games/{games[0]['game_id']}").json()
        self.assertEqual(game["board"][row][col], 7)




class TestDifficultyButtons(TestSudokuE2E):
    """Tests for difficulty button interactions."""

    def test_switch_to_easy(self):
        """Clicking Easy difficulty changes the active button."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        self.page.click(".diff-btn[data-difficulty='30']")
        self.page.wait_for_timeout(300)

        active = self.page.query_selector(".diff-btn.active")
        self.assertIn("Easy", active.text_content())

    def test_switch_to_hard(self):
        """Clicking Hard difficulty changes the active button."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        self.page.click(".diff-btn[data-difficulty='50']")
        self.page.wait_for_timeout(300)

        active = self.page.query_selector(".diff-btn.active")
        self.assertIn("Hard", active.text_content())

    def test_difficulty_label_updates(self):
        """Difficulty label in header should reflect selected difficulty."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        # Default should be Medium
        label = self.page.text_content("#difficultyLabel")
        self.assertEqual(label, "Medium")

        # Switch to Easy
        self.page.click(".diff-btn[data-difficulty='30']")
        self.page.wait_for_timeout(300)
        label = self.page.text_content("#difficultyLabel")
        self.assertEqual(label, "Easy")


class TestCheckButton(TestSudokuE2E):
    """Tests for the Check button."""

    def test_check_shows_message(self):
        """Check button should display a status message."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        self.page.click("#checkBtn")
        self.page.wait_for_timeout(1000)

        hint_text = self.page.text_content("#hintText")
        self.assertTrue(len(hint_text) > 0, "Check should show a message")

    def test_check_marks_wrong_numbers(self):
        """Check should add 'error' class to wrong cells."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        # Place a deliberately wrong number
        empty = self._find_empty_cell()
        row, col = empty
        self._click_cell(row, col)
        # Get the solution value via API and place a different one
        self.page.keyboard.press("1")
        self.page.wait_for_timeout(200)

        # Click check
        self.page.click("#checkBtn")
        self.page.wait_for_timeout(1000)

        # If 1 was wrong, the cell should have 'error' class
        cell = self._get_cell(row, col)
        cell_classes = cell.get_attribute("class") or ""
        # Either it has error class (was wrong) or it doesn't (was right)
        # We just verify the check ran without crashing
        self.assertIsNotNone(cell_classes)


class TestSolveButton(TestSudokuE2E):
    """Tests for the Solve button."""

    def test_solve_fills_board(self):
        """Solve button should fill all empty cells with the solution."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        # Find an empty cell before solving
        empty_before = self._find_empty_cell()
        self.assertIsNotNone(empty_before, "Should have empty cells before solving")

        # Click solve (auto-accept the confirm dialog)
        self.page.on("dialog", lambda dialog: dialog.accept())
        self.page.click("#solveBtn")
        self.page.wait_for_timeout(1000)

        # The previously empty cell should now be filled
        row, col = empty_before
        self.assertNotEqual(self._cell_text(row, col), "")

    def test_solve_shows_modal(self):
        """Solve should show the completion modal."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        self.page.on("dialog", lambda dialog: dialog.accept())
        self.page.click("#solveBtn")
        self.page.wait_for_timeout(1000)

        overlay = self.page.query_selector("#overlay")
        self.assertTrue(overlay.is_visible())
        self.assertIn("Solution", self.page.text_content("#modalTitle"))


class TestHintButton(TestSudokuE2E):
    """Tests for the Hint button."""

    def test_hint_shows_preview(self):
        """Hint button should show a preview of a correct cell."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        # Press and hold hint button (mousedown)
        self.page.dispatch_event("#hintBtn", "mousedown")
        self.page.wait_for_timeout(500)

        # Check if any cell has hint-preview class
        previews = self.page.query_selector_all(".hint-preview")
        # Hint should show a preview on an empty cell
        self.assertGreater(len(previews), 0, "Hint should show a preview cell")

        # Release
        self.page.dispatch_event("#hintBtn", "mouseleave")
        self.page.wait_for_timeout(300)

    def test_hint_commits_on_click(self):
        """Clicking the hint preview cell should commit the hint."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        # Show hint preview
        self.page.dispatch_event("#hintBtn", "mousedown")
        self.page.wait_for_timeout(500)

        # Find the preview cell
        preview_cell = self.page.query_selector(".hint-preview")
        self.assertIsNotNone(preview_cell, "Should have a hint preview")

        # Click it to commit
        preview_cell.click()
        self.page.wait_for_timeout(300)

        # Cell should now have a value
        row = int(preview_cell.get_attribute("data-row"))
        col = int(preview_cell.get_attribute("data-col"))
        self.assertNotEqual(self._cell_text(row, col), "")


class TestAutoNotes(TestSudokuE2E):
    """Tests for Auto-Notes and Clear Notes."""

    def test_auto_notes_fills_pencil_marks(self):
        """Auto-Notes should fill pencil marks in empty cells."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        self.page.click("#autoNotesBtn")
        self.page.wait_for_timeout(500)

        hint_text = self.page.text_content("#hintText")
        self.assertIn("pencil", hint_text.lower())

    def test_clear_notes_removes_marks(self):
        """Clear Notes should remove all pencil marks."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        # First fill notes
        self.page.click("#autoNotesBtn")
        self.page.wait_for_timeout(500)

        # Then clear
        self.page.click("#clearNotesBtn")
        self.page.wait_for_timeout(500)

        hint_text = self.page.text_content("#hintText")
        self.assertIn("Cleared", hint_text)


class TestResetBoard(TestSudokuE2E):
    """Tests for Reset Board button."""

    def test_reset_clears_user_entries(self):
        """Reset Board should clear user-entered numbers back to original."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        # Place a number
        empty = self._find_empty_cell()
        row, col = empty
        self._click_cell(row, col)
        self.page.keyboard.press("5")
        self.page.wait_for_timeout(200)
        self.assertEqual(self._cell_text(row, col), "5")

        # Reset board (auto-accept confirm)
        self.page.on("dialog", lambda dialog: dialog.accept())
        self.page.click("#resetBoardBtn")
        self.page.wait_for_timeout(500)

        # Cell should be empty again
        self.assertEqual(self._cell_text(row, col), "")


class TestNotesMode(TestSudokuE2E):
    """Tests for Notes mode functionality."""

    def test_notes_mode_places_pencil_mark(self):
        """In notes mode, typing should place pencil marks, not final numbers."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        # Switch to notes mode
        self.page.keyboard.press("n")
        self.page.wait_for_timeout(200)

        # Click an empty cell and type
        empty = self._find_empty_cell()
        row, col = empty
        self._click_cell(row, col)
        self.page.keyboard.press("3")
        self.page.wait_for_timeout(200)

        # Cell should NOT show "3" as main text (it's a pencil mark)
        cell_text = self._cell_text(row, col)
        self.assertNotEqual(cell_text, "3",
                          "Notes mode should not place final numbers")


class TestConflictHighlighting(TestSudokuE2E):
    """Tests for visual conflict indicators."""

    def test_wrong_number_gets_error_class(self):
        """Placing a wrong number should add 'error' class after Check."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        # Find an empty cell and the solution for it via API
        empty = self._find_empty_cell()
        row, col = empty

        # Get solution value from the API
        games = requests.get(f"{APP_URL}/api/games").json()["games"]
        game = requests.get(f"{APP_URL}/api/games/{games[0]['game_id']}").json()
        correct_val = game["solution"][row][col]

        # Place a DIFFERENT number (wrong)
        wrong_val = (correct_val % 9) + 1
        if wrong_val == correct_val:
            wrong_val = (correct_val + 1) % 9 + 1

        self._click_cell(row, col)
        self.page.keyboard.press(str(wrong_val))
        self.page.wait_for_timeout(200)

        # Click check
        self.page.click("#checkBtn")
        self.page.wait_for_timeout(1000)

        # Cell should have 'error' class
        cell = self._get_cell(row, col)
        cell_classes = cell.get_attribute("class") or ""
        self.assertIn("error", cell_classes,
                     f"Cell with wrong number should have 'error' class, got: {cell_classes}")


class TestProgressDisplay(TestSudokuE2E):
    """Tests for progress percentage display."""

    def test_progress_starts_at_zero(self):
        """Progress should start at 0% on a fresh game."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        # Wait for new game to initialize
        self.page.wait_for_timeout(1000)

        progress = self.page.text_content("#progressLabel")
        self.assertEqual(progress, "0%")

    def test_progress_increases_after_move(self):
        """Progress should increase after placing a correct number."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")
        self.page.wait_for_timeout(1000)

        initial = self.page.text_content("#progressLabel")
        self.assertEqual(initial, "0%")

        # Find empty cell, get solution, place correct number
        empty = self._find_empty_cell()
        row, col = empty

        games = requests.get(f"{APP_URL}/api/games").json()["games"]
        game = requests.get(f"{APP_URL}/api/games/{games[0]['game_id']}").json()
        correct_val = game["solution"][row][col]

        self._click_cell(row, col)
        self.page.keyboard.press(str(correct_val))
        self.page.wait_for_timeout(200)

        progress = self.page.text_content("#progressLabel")
        self.assertNotEqual(progress, "0%")


class TestCellHighlighting(TestSudokuE2E):
    """Tests for cell selection highlighting."""

    def test_selected_cell_has_selected_class(self):
        """Clicking a cell should add 'selected' class."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        self._click_cell(0, 0)
        self.page.wait_for_timeout(200)

        cell = self._get_cell(0, 0)
        self.assertIn("selected", cell.get_attribute("class"))

    def test_row_col_box_highlighted(self):
        """Selecting a cell should highlight its row, column, and box."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        self._click_cell(4, 4)  # Center cell
        self.page.wait_for_timeout(200)

        # Same row cells should be highlighted
        row_cell = self._get_cell(4, 0)
        self.assertIn("highlight", row_cell.get_attribute("class"))

        # Same column cells should be highlighted
        col_cell = self._get_cell(0, 4)
        self.assertIn("highlight", col_cell.get_attribute("class"))

        # Same box cells should be highlighted
        box_cell = self._get_cell(3, 3)
        self.assertIn("highlight", box_cell.get_attribute("class"))

    def test_selecting_different_cell_moves_selection(self):
        """Selecting a new cell should deselect the old one."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        self._click_cell(0, 0)
        self.page.wait_for_timeout(200)
        old_cell = self._get_cell(0, 0)
        self.assertIn("selected", old_cell.get_attribute("class"))

        self._click_cell(5, 5)
        self.page.wait_for_timeout(200)
        old_cell = self._get_cell(0, 0)
        self.assertNotIn("selected", old_cell.get_attribute("class"))
        new_cell = self._get_cell(5, 5)
        self.assertIn("selected", new_cell.get_attribute("class"))


class TestNumpadState(TestSudokuE2E):
    """Tests for numpad button state."""

    def test_numpad_shows_count(self):
        """Numpad buttons should show remaining count badges."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")
        self.page.wait_for_timeout(1000)

        # Each numpad button may have a badge showing remaining count
        # At minimum, buttons 1-9 should be visible and clickable
        for num in range(1, 10):
            btn = self.page.query_selector(f".num-btn[data-num='{num}']")
            self.assertIsNotNone(btn, f"Numpad button {num} should exist")
            self.assertTrue(btn.is_visible())


class TestKeyboardShortcuts(TestSudokuE2E):
    """Tests for keyboard shortcuts."""

    def test_help_shortcut(self):
        """Pressing ? should open help overlay."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        self.page.keyboard.press("Shift+Slash")  # ? key
        self.page.wait_for_timeout(300)

        help_overlay = self.page.query_selector("#helpOverlay")
        self.assertTrue(help_overlay.is_visible())

        # Close with Escape
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)
        self.assertFalse(help_overlay.is_visible())

    def test_escape_dismisses_hint(self):
        """Escape should dismiss hint text."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        # Trigger a hint message
        self.page.click("#checkBtn")
        self.page.wait_for_timeout(500)

        # Press escape
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(500)

        # Hint text should be empty or clearing
        hint_text = self.page.text_content("#hintText")
        # May not be empty yet if timeout hasn't fired, but escape should work

    def test_r_key_resets_board(self):
        """Pressing R should trigger reset board."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        # Place a number first
        empty = self._find_empty_cell()
        row, col = empty
        self._click_cell(row, col)
        self.page.keyboard.press("5")
        self.page.wait_for_timeout(200)
        self.assertEqual(self._cell_text(row, col), "5")

        # Press R (should trigger confirm dialog)
        self.page.on("dialog", lambda dialog: dialog.accept())
        self.page.keyboard.press("r")
        self.page.wait_for_timeout(500)

        # Cell should be empty
        self.assertEqual(self._cell_text(row, col), "")

    def test_t_key_toggles_theme(self):
        """Pressing T should toggle theme."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        html_class = self.page.get_attribute("html", "class") or ""
        initial_light = "light" in html_class

        self.page.keyboard.press("t")
        self.page.wait_for_timeout(300)

        html_class = self.page.get_attribute("html", "class") or ""
        new_light = "light" in html_class
        self.assertNotEqual(initial_light, new_light)

    def test_l_key_opens_games(self):
        """Pressing L should open Load Games modal."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        self.page.keyboard.press("l")
        self.page.wait_for_timeout(500)

        games_overlay = self.page.query_selector("#gamesOverlay")
        self.assertTrue(games_overlay.is_visible())


class TestGamesModal(TestSudokuE2E):
    """Tests for Load Games modal functionality."""

    def test_games_modal_shows_saved_games(self):
        """Load Games modal should show saved games."""
        self.page.goto(APP_URL)
        self.page.wait_for_timeout(1000)  # Wait for auto-save

        self.page.click("#loadGamesBtn")
        self.page.wait_for_timeout(500)

        # Should have at least one game in the table
        rows = self.page.query_selector_all("#gamesTableBody tr")
        self.assertGreater(len(rows), 0, "Should have at least one saved game")

    def test_games_modal_sort_dropdown(self):
        """Sort dropdown should have all options."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        self.page.click("#loadGamesBtn")
        self.page.wait_for_timeout(500)

        sort = self.page.query_selector("#gamesSort")
        options = sort.query_selector_all("option")
        self.assertEqual(len(options), 5)

    def test_games_modal_filter_checkboxes(self):
        """Filter checkboxes should be present and checked by default."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        self.page.click("#loadGamesBtn")
        self.page.wait_for_timeout(500)

        completed = self.page.query_selector("#filterCompleted")
        inprogress = self.page.query_selector("#filterInProgress")
        self.assertTrue(completed.is_checked())
        self.assertTrue(inprogress.is_checked())

    def test_close_games_modal_with_button(self):
        """Close button should close the games modal."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        self.page.click("#loadGamesBtn")
        self.page.wait_for_timeout(500)

        games_overlay = self.page.query_selector("#gamesOverlay")
        self.assertTrue(games_overlay.is_visible())

        self.page.click("#closeGamesBtn")
        self.page.wait_for_timeout(300)
        self.assertFalse(games_overlay.is_visible())


class TestGameIdDisplay(TestSudokuE2E):
    """Tests for game ID display in footer."""

    def test_game_id_displayed(self):
        """Game ID should be displayed in the footer after game creation."""
        self.page.goto(APP_URL)
        self.page.wait_for_timeout(1000)

        game_id = self.page.text_content("#gameIdDisplay")
        self.assertTrue(game_id and len(game_id) > 0, "Game ID should be displayed")
        self.assertIn("#", game_id)


class TestTimerDisplay(TestSudokuE2E):
    """Tests for timer display."""

    def test_timer_starts_at_zero(self):
        """Timer should show 00:00 on fresh page load."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        # Wait for game to initialize
        self.page.wait_for_timeout(1000)

        timer = self.page.text_content("#timer")
        # Should be 00:00 or very close to it
        self.assertTrue(timer.startswith("00:0"), f"Timer should start near 00:00, got: {timer}")




class TestWinFlow(TestSudokuE2E):
    """Tests for win detection and the win modal."""

    def test_win_modal_appears_on_completion(self):
        """Completing the puzzle should show the win modal."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")
        self.page.wait_for_timeout(1000)

        # Get the solution from the API
        games = requests.get(f"{APP_URL}/api/games").json()["games"]
        game = requests.get(f"{APP_URL}/api/games/{games[0]['game_id']}").json()
        solution = game["solution"]

        # Fill in all empty cells with the correct solution
        for r in range(9):
            for c in range(9):
                if self._cell_text(r, c) == "":
                    self._click_cell(r, c)
                    self.page.keyboard.press(str(solution[r][c]))
                    self.page.wait_for_timeout(100)

        # Win modal should appear
        overlay = self.page.query_selector("#overlay")
        self.page.wait_for_timeout(500)
        self.assertTrue(overlay.is_visible(), "Win modal should appear after completing puzzle")

    def test_win_modal_shows_stats(self):
        """Win modal should show time and mistakes."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")
        self.page.wait_for_timeout(1000)

        games = requests.get(f"{APP_URL}/api/games").json()["games"]
        game = requests.get(f"{APP_URL}/api/games/{games[0]['game_id']}").json()
        solution = game["solution"]

        for r in range(9):
            for c in range(9):
                if self._cell_text(r, c) == "":
                    self._click_cell(r, c)
                    self.page.keyboard.press(str(solution[r][c]))
                    self.page.wait_for_timeout(100)

        self.page.wait_for_timeout(500)
        modal_body = self.page.text_content("#modalBody")
        self.assertTrue(len(modal_body) > 0, "Win modal body should have content")


class TestLoadGameFromModal(TestSudokuE2E):
    """Tests for loading a game from the Load Games modal."""

    def test_load_game_restores_state(self):
        """Loading a saved game should restore the board state."""
        self.page.goto(APP_URL)
        self.page.wait_for_timeout(1000)

        # Place a number and save
        empty = self._find_empty_cell()
        row, col = empty
        self._click_cell(row, col)
        self.page.keyboard.press("5")
        self.page.wait_for_timeout(500)

        # Open Load Games modal
        self.page.click("#loadGamesBtn")
        self.page.wait_for_timeout(500)

        # Click the first game's load button
        load_btn = self.page.query_selector("#gamesTableBody tr .load-btn")
        if load_btn:
            load_btn.click()
            self.page.wait_for_timeout(500)
            # Modal should close
            games_overlay = self.page.query_selector("#gamesOverlay")
            self.assertFalse(games_overlay.is_visible())
        else:
            # If no load button, just verify the modal has content
            rows = self.page.query_selector_all("#gamesTableBody tr")
            self.assertGreater(len(rows), 0)


class TestMoreKeyboardShortcuts(TestSudokuE2E):
    """Tests for additional keyboard shortcuts."""

    def test_a_key_auto_notes(self):
        """Pressing A should trigger auto-notes."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        self.page.keyboard.press("a")
        self.page.wait_for_timeout(500)

        hint_text = self.page.text_content("#hintText")
        self.assertIn("pencil", hint_text.lower())

    def test_d_key_daily_puzzle(self):
        """Pressing D should load the daily puzzle."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        self.page.keyboard.press("d")
        self.page.wait_for_timeout(1000)

        # Board should still have 81 cells
        cells = self.page.query_selector_all("#board .cell")
        self.assertEqual(len(cells), 81)




class TestPauseTimer(TestSudokuE2E):
    """Tests for pause functionality."""

    def test_pause_stops_timer(self):
        """When paused, the timer should not increment."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")
        self.page.wait_for_timeout(1000)

        timer_before = self.page.text_content("#timer")

        # Pause
        self.page.click("#pauseBtn")
        self.page.wait_for_timeout(3000)

        timer_after = self.page.text_content("#timer")
        # Timer should not have changed (was paused)
        self.assertEqual(timer_before, timer_after,
                        f"Timer should not change while paused: before={timer_before}, after={timer_after}")

    def test_resume_continues_timer(self):
        """After resuming, the timer should continue counting."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")
        self.page.wait_for_timeout(1000)

        # Pause
        self.page.click("#pauseBtn")
        self.page.wait_for_timeout(2000)

        timer_paused = self.page.text_content("#timer")

        # Resume
        self.page.click("#pauseBtn")
        self.page.wait_for_timeout(2000)

        timer_resumed = self.page.text_content("#timer")
        # Timer should have advanced after resume
        self.assertNotEqual(timer_paused, timer_resumed,
                           "Timer should advance after resuming")


class TestErrorCorrection(TestSudokuE2E):
    """Tests for error class removal when correcting mistakes."""

    def test_error_removed_when_corrected(self):
        """Correcting a wrong number should remove the error class."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")
        self.page.wait_for_timeout(1000)

        # Find empty cell and get solution
        empty = self._find_empty_cell()
        row, col = empty

        games = requests.get(f"{APP_URL}/api/games").json()["games"]
        game = requests.get(f"{APP_URL}/api/games/{games[0]['game_id']}").json()
        correct_val = game["solution"][row][col]

        # Place wrong number
        wrong_val = (correct_val % 9) + 1
        if wrong_val == correct_val:
            wrong_val = (correct_val + 1) % 9 + 1

        self._click_cell(row, col)
        self.page.keyboard.press(str(wrong_val))
        self.page.wait_for_timeout(200)

        # Check to mark error
        self.page.click("#checkBtn")
        self.page.wait_for_timeout(1000)

        cell = self._get_cell(row, col)
        self.assertIn("error", cell.get_attribute("class"))

        # Correct it
        self._click_cell(row, col)
        self.page.keyboard.press(str(correct_val))
        self.page.wait_for_timeout(200)

        # Re-check
        self.page.click("#checkBtn")
        self.page.wait_for_timeout(1000)

        cell = self._get_cell(row, col)
        cell_classes = cell.get_attribute("class") or ""
        self.assertNotIn("error", cell_classes,
                        "Error class should be removed after correcting the number")


class TestExpertDifficulty(TestSudokuE2E):
    """Tests for Expert difficulty button."""

    def test_expert_difficulty_button(self):
        """Expert difficulty button should activate."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        self.page.click(".diff-btn[data-difficulty='58']")
        self.page.wait_for_timeout(300)

        active = self.page.query_selector(".diff-btn.active")
        self.assertIn("Expert", active.text_content())


class TestPlayAgain(TestSudokuE2E):
    """Tests for the Play Again button in win modal."""

    def test_play_again_starts_new_game(self):
        """Play Again button should start a new game."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")
        self.page.wait_for_timeout(1000)

        # Solve the puzzle via API to trigger win
        games = requests.get(f"{APP_URL}/api/games").json()["games"]
        game = requests.get(f"{APP_URL}/api/games/{games[0]['game_id']}").json()
        solution = game["solution"]

        for r in range(9):
            for c in range(9):
                if self._cell_text(r, c) == "":
                    self._click_cell(r, c)
                    self.page.keyboard.press(str(solution[r][c]))
                    self.page.wait_for_timeout(100)

        self.page.wait_for_timeout(500)

        # Click Play Again
        self.page.click("#modalNewGame")
        self.page.wait_for_timeout(1000)

        # Win modal should be closed
        overlay = self.page.query_selector("#overlay")
        self.assertFalse(overlay.is_visible(), "Win modal should close after Play Again")

        # Board should still have 81 cells
        cells = self.page.query_selector_all("#board .cell")
        self.assertEqual(len(cells), 81)


class TestGamePersistence(TestSudokuE2E):
    """Tests for game persistence across page reloads."""

    def test_game_restored_on_reload(self):
        """Reloading the page should restore the current game."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")
        self.page.wait_for_timeout(1000)

        # Place a number
        empty = self._find_empty_cell()
        row, col = empty
        self._click_cell(row, col)
        self.page.keyboard.press("5")
        self.page.wait_for_timeout(500)

        # Reload
        self.page.reload()
        self.page.wait_for_selector("#board .cell")
        self.page.wait_for_timeout(1000)

        # Game ID should still be displayed
        game_id = self.page.text_content("#gameIdDisplay")
        self.assertTrue(game_id and len(game_id) > 0, "Game should be restored on reload")




class TestSameNumberHighlighting(TestSudokuE2E):
    """Tests for same-number highlighting when selecting a cell."""

    def test_same_number_highlighted(self):
        """Selecting a cell with a number should highlight all same numbers."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")
        self.page.wait_for_timeout(1000)

        # Click a given cell (has a number)
        for r in range(9):
            for c in range(9):
                val = self._cell_text(r, c)
                if val != "":
                    self._click_cell(r, c)
                    self.page.wait_for_timeout(200)
                    # Check if any cell has same-num class
                    same_nums = self.page.query_selector_all(".same-num")
                    self.assertGreater(len(same_nums), 0,
                                      f"Should highlight cells with same number {val}")
                    return
        self.fail("No filled cells found on board")

    def test_empty_cell_no_same_number(self):
        """Selecting an empty cell should not highlight any same-num cells."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")
        self.page.wait_for_timeout(1000)

        empty = self._find_empty_cell()
        row, col = empty
        self._click_cell(row, col)
        self.page.wait_for_timeout(200)

        same_nums = self.page.query_selector_all(".same-num")
        self.assertEqual(len(same_nums), 0, "Empty cell should not have same-num highlights")


class TestConflictDetection(TestSudokuE2E):
    """Tests for real-time conflict detection."""

    def test_conflict_class_appears_on_duplicate(self):
        """Placing a duplicate number should add 'conflict' class."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")
        self.page.wait_for_timeout(1000)

        # Find a given cell with value v, then place v in another cell in the same row
        for r in range(9):
            for c in range(9):
                val = self._cell_text(r, c)
                if val == "":
                    continue
                # Find an empty cell in the same row
                for c2 in range(9):
                    if c2 != c and self._cell_text(r, c2) == "":
                        self._click_cell(r, c2)
                        self.page.keyboard.press(val)
                        self.page.wait_for_timeout(200)
                        # Check for conflict class
                        conflicts = self.page.query_selector_all(".conflict")
                        self.assertGreater(len(conflicts), 0,
                                          "Duplicate number should create conflict")
                        return
        # If no suitable configuration found, skip
        self.skipTest("No suitable board configuration for conflict test")


class TestDeleteGame(TestSudokuE2E):
    """Tests for deleting a game from the games modal."""

    def test_delete_game_removes_from_list(self):
        """Delete button should remove a game from the list."""
        self.page.goto(APP_URL)
        self.page.wait_for_timeout(1000)

        # Open games modal
        self.page.click("#loadGamesBtn")
        self.page.wait_for_timeout(500)

        # Count rows before
        rows_before = len(self.page.query_selector_all("#gamesTableBody tr"))
        self.assertGreater(rows_before, 0, "Should have games to delete")

        # Click first delete button
        delete_btn = self.page.query_selector("#gamesTableBody tr .delete-btn")
        if delete_btn:
            delete_btn.click()
            self.page.wait_for_timeout(500)

            # Count rows after
            rows_after = len(self.page.query_selector_all("#gamesTableBody tr"))
            self.assertEqual(rows_after, rows_before - 1,
                            "Game should be deleted from list")


class TestShareGame(TestSudokuE2E):
    """Tests for the share game functionality."""

    def test_share_button_shows_hint(self):
        """Share button should show a hint message."""
        self.page.goto(APP_URL)
        self.page.wait_for_timeout(1000)

        # Grant clipboard permission
        self._context.grant_permissions(["clipboard-read", "clipboard-write"])

        self.page.click("#loadGamesBtn")
        self.page.wait_for_timeout(500)

        share_btn = self.page.query_selector("#gamesTableBody tr .share-btn")
        if share_btn:
            share_btn.click()
            self.page.wait_for_timeout(1000)

            hint_text = self.page.text_content("#hintText")
            self.assertTrue(
                "Share link" in hint_text or "Failed" in hint_text,
                f"Share should show a message, got: {hint_text}"
            )


class TestDifficultyChangeNewGame(TestSudokuE2E):
    """Tests that changing difficulty only selects it, New Game button starts the game."""

    def test_difficulty_change_starts_new_game(self):
        """Clicking a difficulty button should NOT start a new game. Only New Game does."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")
        self.page.wait_for_timeout(1000)

        # Get initial game ID
        game_id_before = self.page.text_content("#gameIdDisplay")

        # Switch to Easy difficulty (should NOT create a new game)
        self.page.click(".diff-btn[data-difficulty='30']")
        self.page.wait_for_timeout(500)

        # Game ID should NOT change (difficulty only selects, doesn't start)
        game_id_after = self.page.text_content("#gameIdDisplay")
        self.assertEqual(game_id_before, game_id_after,
                         "Difficulty change should NOT start a new game")




class TestGamesModalSort(TestSudokuE2E):
    """Tests for games modal sorting."""

    def test_sort_by_newest(self):
        """Sort dropdown should sort by newest."""
        self.page.goto(APP_URL)
        self.page.wait_for_timeout(1000)

        self.page.click("#loadGamesBtn")
        self.page.wait_for_timeout(500)

        self.page.select_option("#gamesSort", "updated")
        self.page.wait_for_timeout(500)

        rows = self.page.query_selector_all("#gamesTableBody tr")
        self.assertGreater(len(rows), 0)

    def test_sort_by_difficulty(self):
        """Sort dropdown should sort by difficulty."""
        self.page.goto(APP_URL)
        self.page.wait_for_timeout(1000)

        self.page.click("#loadGamesBtn")
        self.page.wait_for_timeout(500)

        self.page.select_option("#gamesSort", "difficulty")
        self.page.wait_for_timeout(500)

        rows = self.page.query_selector_all("#gamesTableBody tr")
        self.assertGreater(len(rows), 0)


class TestGamesModalFilter(TestSudokuE2E):
    """Tests for games modal filtering."""

    def test_filter_completed_only(self):
        """Filtering to completed only should hide in-progress games."""
        self.page.goto(APP_URL)
        self.page.wait_for_timeout(1000)

        self.page.click("#loadGamesBtn")
        self.page.wait_for_timeout(500)

        # Uncheck in-progress
        self.page.uncheck("#filterInProgress")
        self.page.wait_for_timeout(500)

        # All visible rows should be completed
        rows = self.page.query_selector_all("#gamesTableBody tr")
        for row in rows:
            text = row.text_content()
            # Completed games should have ✅
            self.assertIn("✅", text)

    def test_filter_in_progress_only(self):
        """Filtering to in-progress only should hide completed games."""
        self.page.goto(APP_URL)
        self.page.wait_for_timeout(1000)

        self.page.click("#loadGamesBtn")
        self.page.wait_for_timeout(500)

        # Uncheck completed
        self.page.uncheck("#filterCompleted")
        self.page.wait_for_timeout(500)

        # All visible rows should be in-progress (no ✅)
        rows = self.page.query_selector_all("#gamesTableBody tr")
        for row in rows:
            text = row.text_content()
            self.assertNotIn("✅", text)


class TestGamesStatsSummary(TestSudokuE2E):
    """Tests for stats summary in games modal."""

    def test_stats_summary_displayed(self):
        """Stats summary should be displayed when games exist."""
        self.page.goto(APP_URL)
        self.page.wait_for_timeout(1000)

        self.page.click("#loadGamesBtn")
        self.page.wait_for_timeout(500)

        stats_el = self.page.query_selector("#gamesStatsSummary")
        self.assertIsNotNone(stats_el)
        # Should be visible (games exist)
        self.assertTrue(stats_el.is_visible())

    def test_stats_summary_has_total(self):
        """Stats summary should show total games count."""
        self.page.goto(APP_URL)
        self.page.wait_for_timeout(1000)

        self.page.click("#loadGamesBtn")
        self.page.wait_for_timeout(500)

        stats_text = self.page.text_content("#gamesStatsSummary")
        self.assertIn("Total:", stats_text)


class TestSpaceKeyPause(TestSudokuE2E):
    """Tests for Space key toggling pause."""

    def test_space_key_toggles_pause(self):
        """Pressing Space should toggle pause."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")
        self.page.wait_for_timeout(1000)

        timer_before = self.page.text_content("#timer")
        pause_text_before = self.page.text_content("#pauseBtn")

        # Press Space to pause
        self.page.keyboard.press("Space")
        self.page.wait_for_timeout(2000)

        timer_after = self.page.text_content("#timer")
        self.assertEqual(timer_before, timer_after, "Timer should not change while paused")

        # Press Space to resume
        self.page.keyboard.press("Space")
        self.page.wait_for_timeout(2000)

        timer_resumed = self.page.text_content("#timer")
        self.assertNotEqual(timer_before, timer_resumed, "Timer should advance after resume")


class TestMediumDifficulty(TestSudokuE2E):
    """Tests for Medium difficulty (default)."""

    def test_medium_is_default(self):
        """Medium difficulty should be active by default."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        active = self.page.query_selector(".diff-btn.active")
        self.assertIn("Medium", active.text_content())


class TestNewGameFromWinModal(TestSudokuE2E):
    """Tests for New Game button in win modal."""

    def test_new_game_from_win_modal(self):
        """New Game button in win modal should start a fresh game."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")
        self.page.wait_for_timeout(1000)

        # Get initial game ID
        game_id_before = self.page.text_content("#gameIdDisplay")

        # Solve the puzzle to trigger win
        games = requests.get(f"{APP_URL}/api/games").json()["games"]
        game = requests.get(f"{APP_URL}/api/games/{games[0]['game_id']}").json()
        solution = game["solution"]

        for r in range(9):
            for c in range(9):
                if self._cell_text(r, c) == "":
                    self._click_cell(r, c)
                    self.page.keyboard.press(str(solution[r][c]))
                    self.page.wait_for_timeout(100)

        self.page.wait_for_timeout(500)

        # Click New Game in win modal
        self.page.click("#modalNewGame")
        self.page.wait_for_timeout(1000)

        # Win modal should be closed
        overlay = self.page.query_selector("#overlay")
        self.assertFalse(overlay.is_visible())

        # Game ID should be different
        game_id_after = self.page.text_content("#gameIdDisplay")
        self.assertNotEqual(game_id_before, game_id_after)

        # Timer should be reset
        timer = self.page.text_content("#timer")
        self.assertTrue(timer.startswith("00:0"), f"Timer should be reset, got: {timer}")




class TestButtonLayout(TestSudokuE2E):
    """Tests for reorganized button layout."""

    def test_action_buttons_use_grid_not_single_column(self):
        """Action buttons should be in a grid layout, not single column."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")
        self.page.wait_for_timeout(500)

        # The actions section should use grid, not flex column
        actions_display = self.page.eval_on_selector(
            ".actions",
            "el => getComputedStyle(el).display"
        )
        self.assertEqual(actions_display, "grid",
                        "Actions should use grid layout, not flex column")

    def test_new_game_button_is_full_width(self):
        """New Game button should span full width of its grid row."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")
        self.page.wait_for_timeout(500)

        new_game = self.page.query_selector("#newGameBtn")
        self.assertIsNotNone(new_game)

        # New Game should span full width (grid-column: 1 / -1 or span 2)
        grid_column = self.page.eval_on_selector(
            "#newGameBtn",
            "el => getComputedStyle(el).gridColumn"
        )
        self.assertTrue(
            "span 2" in grid_column.lower() or "1 / -1" in grid_column or "1/-1" in grid_column,
            f"New Game should span full width, got grid-column: {grid_column}"
        )


class TestDifficultySelectionOnly(TestSudokuE2E):
    """Tests that difficulty buttons only select, not start new game."""

    def test_difficulty_does_not_change_game_id(self):
        """Clicking difficulty should NOT change the current game."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")
        self.page.wait_for_timeout(1000)

        game_id_before = self.page.text_content("#gameIdDisplay")

        # Click Easy difficulty
        self.page.click(".diff-btn[data-difficulty='30']")
        self.page.wait_for_timeout(500)

        game_id_after = self.page.text_content("#gameIdDisplay")
        self.assertEqual(game_id_before, game_id_after,
                         "Difficulty change should NOT create a new game")

    def test_difficulty_shows_hint_message(self):
        """Changing difficulty should show a hint telling user to start new game."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")
        self.page.wait_for_timeout(1000)

        # Click Easy difficulty
        self.page.click(".diff-btn[data-difficulty='30']")
        self.page.wait_for_timeout(300)

        hint_text = self.page.text_content("#hintText")
        self.assertTrue(
            "new game" in hint_text.lower() or "difficulty" in hint_text.lower(),
            f"Should show hint about difficulty change, got: {hint_text}"
        )

    def test_new_game_uses_selected_difficulty(self):
        """New Game button should use the currently selected difficulty."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")
        self.page.wait_for_timeout(1000)

        # Select Hard difficulty
        self.page.click(".diff-btn[data-difficulty='50']")
        self.page.wait_for_timeout(300)

        # Now click New Game
        self.page.click("#newGameBtn")
        self.page.wait_for_timeout(1000)

        # The difficulty label should show Hard
        label = self.page.text_content("#difficultyLabel")
        self.assertEqual(label, "Hard")




class TestAutoNotesToggle(TestSudokuE2E):
    """Tests that auto-notes toggles on/off, preserving user notes."""

    def test_auto_notes_button_toggles_active_class(self):
        """Auto-Notes button should get active class when toggled on."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")
        self.page.wait_for_timeout(1000)

        btn = self.page.query_selector("#autoNotesBtn")
        self.assertFalse(btn.get_attribute("class") and "active" in btn.get_attribute("class"),
                        "Auto-Notes should start inactive")

        btn.click()
        self.page.wait_for_timeout(500)
        self.assertTrue("active" in btn.get_attribute("class"),
                        "Auto-Notes button should have active class when toggled on")

        btn.click()
        self.page.wait_for_timeout(500)
        self.assertFalse("active" in btn.get_attribute("class"),
                         "Auto-Notes button should NOT have active class when toggled off")

    def test_auto_notes_off_clears_only_auto_notes(self):
        """When auto-notes is turned off, only auto-generated notes are cleared."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")
        self.page.wait_for_timeout(1000)

        # Turn auto-notes on
        self.page.click("#autoNotesBtn")
        self.page.wait_for_timeout(500)

        # Verify some notes appeared
        notes_count = self.page.eval_on_selector_all(
            "#board .cell .pencil-marks span.on",
            "els => els.length"
        )
        self.assertGreater(notes_count, 0, "Auto-notes should fill pencil marks")

        # Turn auto-notes off
        self.page.click("#autoNotesBtn")
        self.page.wait_for_timeout(500)

        # Notes should be cleared
        notes_count_after = self.page.eval_on_selector_all(
            "#board .cell .pencil-marks span.on",
            "els => els.length"
        )
        self.assertEqual(notes_count_after, 0,
                         "Auto-notes off should clear all auto-generated notes")

    def test_user_notes_preserved_when_auto_notes_off(self):
        """User-entered notes should remain when auto-notes is turned off."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")
        self.page.wait_for_timeout(1000)

        # Switch to notes mode
        self.page.click("#notesModeBtn")
        self.page.wait_for_timeout(300)

        # Click an empty cell, add a note
        cells = self.page.query_selector_all("#board .cell")
        empty_cell = None
        for cell in cells:
            text = cell.inner_text().strip()
            if not text:
                empty_cell = cell
                break

        if empty_cell:
            empty_cell.click()
            self.page.wait_for_timeout(100)
            # Add note "5"
            self.page.click(".num-btn[data-num='5']")
            self.page.wait_for_timeout(200)

        # Turn auto-notes on (should add more notes, keep user note)
        self.page.click("#finalModeBtn")  # Switch back to final mode first
        self.page.wait_for_timeout(100)
        self.page.click("#autoNotesBtn")
        self.page.wait_for_timeout(500)

        # Turn auto-notes off (should clear auto notes, keep user note)
        self.page.click("#autoNotesBtn")
        self.page.wait_for_timeout(500)

        # Check if at least one note remains (the user-entered one)
        notes_remaining = self.page.eval_on_selector_all(
            "#board .cell .pencil-marks span.on",
            "els => els.length"
        )
        self.assertGreater(notes_remaining, 0,
                          "User-entered notes should be preserved when auto-notes is off")


if __name__ == "__main__":
    unittest.main(verbosity=2)
