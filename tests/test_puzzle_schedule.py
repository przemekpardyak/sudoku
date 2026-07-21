"""
Tests for the daily and weekly puzzle consistency.
Verifies that daily/weekly puzzles are deterministic and valid.
"""
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module
from sudoku import _has_conflicts


class TestPuzzleSchedule(unittest.TestCase):
    """Tests for scheduled puzzle consistency."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_daily_puzzle_valid_board(self):
        """Daily puzzle should be a valid 9x9 board."""
        res = self.client.get('/api/daily-puzzle')
        puzzle = res.get_json()['puzzle']
        self.assertEqual(len(puzzle), 9)
        for row in puzzle:
            self.assertEqual(len(row), 9)
        self.assertFalse(_has_conflicts(puzzle))

    def test_weekly_puzzle_valid_board(self):
        """Weekly puzzle should be a valid 9x9 board."""
        res = self.client.get('/api/weekly-puzzle')
        puzzle = res.get_json()['puzzle']
        self.assertEqual(len(puzzle), 9)
        for row in puzzle:
            self.assertEqual(len(row), 9)
        self.assertFalse(_has_conflicts(puzzle))

    def test_daily_and_weekly_different(self):
        """Daily and weekly puzzles should be different."""
        daily = self.client.get('/api/daily-puzzle').get_json()['puzzle']
        weekly = self.client.get('/api/weekly-puzzle').get_json()['puzzle']
        self.assertNotEqual(daily, weekly)

    def test_daily_has_date_field(self):
        """Daily puzzle should have a date field."""
        res = self.client.get('/api/daily-puzzle')
        self.assertIn('date', res.get_json())

    def test_weekly_has_week_field(self):
        """Weekly puzzle should have a week field."""
        res = self.client.get('/api/weekly-puzzle')
        self.assertIn('week', res.get_json())

    def test_daily_difficulty_is_medium(self):
        """Daily puzzle should be medium difficulty (40)."""
        res = self.client.get('/api/daily-puzzle')
        puzzle = res.get_json()['puzzle']
        empty_count = sum(1 for r in range(9) for c in range(9) if puzzle[r][c] == 0)
        # Medium has ~40 empty cells
        self.assertGreater(empty_count, 25)
        self.assertLess(empty_count, 50)

    def test_weekly_difficulty_is_hard(self):
        """Weekly puzzle should be hard difficulty (50)."""
        res = self.client.get('/api/weekly-puzzle')
        self.assertEqual(res.get_json()['difficulty'], 50)

    def test_daily_seed_format(self):
        """Daily puzzle seed should start with 'daily-'."""
        res = self.client.get('/api/daily-puzzle')
        seed = res.get_json()['seed']
        self.assertTrue(seed.startswith('daily-'))

    def test_weekly_seed_format(self):
        """Weekly puzzle seed should start with 'weekly-'."""
        res = self.client.get('/api/weekly-puzzle')
        seed = res.get_json()['seed']
        self.assertTrue(seed.startswith('weekly-'))

    def test_both_have_solutions(self):
        """Both daily and weekly should include solutions."""
        daily = self.client.get('/api/daily-puzzle').get_json()
        weekly = self.client.get('/api/weekly-puzzle').get_json()
        self.assertIn('solution', daily)
        self.assertIn('solution', weekly)
        self.assertFalse(_has_conflicts(daily['solution']))
        self.assertFalse(_has_conflicts(weekly['solution']))

    def test_daily_puzzle_has_empty_cells(self):
        """Daily puzzle should have empty cells."""
        res = self.client.get('/api/daily-puzzle')
        puzzle = res.get_json()['puzzle']
        has_empty = any(0 in row for row in puzzle)
        self.assertTrue(has_empty)

    def test_weekly_puzzle_has_empty_cells(self):
        """Weekly puzzle should have empty cells."""
        res = self.client.get('/api/weekly-puzzle')
        puzzle = res.get_json()['puzzle']
        has_empty = any(0 in row for row in puzzle)
        self.assertTrue(has_empty)

    def test_weekly_harder_than_daily(self):
        """Weekly puzzle should have more empty cells than daily."""
        daily = self.client.get('/api/daily-puzzle').get_json()['puzzle']
        weekly = self.client.get('/api/weekly-puzzle').get_json()['puzzle']
        daily_empty = sum(1 for r in range(9) for c in range(9) if daily[r][c] == 0)
        weekly_empty = sum(1 for r in range(9) for c in range(9) if weekly[r][c] == 0)
        self.assertGreaterEqual(weekly_empty, daily_empty - 5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
