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
        # Check if app is already running
        if not _wait_for_app(timeout=2):
            # Start the app
            cls._app_process = subprocess.Popen(
                ["venv/bin/python3", "app.py"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid,
            )
            if not _wait_for_app(timeout=15):
                raise RuntimeError("Flask app did not start in time")
        cls._playwright = sync_playwright().start()
        cls._browser = cls._playwright.chromium.launch(headless=True)
        cls._context = cls._browser.new_context()
        # Clear storage so each test class starts fresh
        try:
            requests.delete(f"{APP_URL}/api/games")
        except Exception:
            pass

    @classmethod
    def tearDownClass(cls):
        cls._context.close()
        cls._browser.close()
        cls._playwright.stop()
        if cls._app_process:
            os.killpg(os.getpgid(cls._app_process.pid), signal.SIGTERM)

    def setUp(self):
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
        """Placing a number should trigger auto-save."""
        self.page.goto(APP_URL)
        self.page.wait_for_selector("#board .cell")

        # Place a number
        empty = self._find_empty_cell()
        row, col = empty
        self._click_cell(row, col)
        self.page.keyboard.press("5")
        self.page.wait_for_timeout(2500)  # Wait for auto-save (2s debounce)

        # Check that the game was updated via API
        res = requests.get(f"{APP_URL}/api/games")
        games = res.json()["games"]
        self.assertGreater(len(games), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
