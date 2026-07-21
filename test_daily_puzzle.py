"""
Tests for the daily puzzle feature.
"""
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestDailyPuzzle(unittest.TestCase):
    """Tests for /api/daily-puzzle endpoint."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_returns_valid_response(self):
        """Daily puzzle should return puzzle, solution, date, and seed."""
        res = self.client.get('/api/daily-puzzle')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('puzzle', data)
        self.assertIn('solution', data)
        self.assertIn('date', data)
        self.assertIn('seed', data)

    def test_puzzle_is_9x9(self):
        """Daily puzzle should be a 9x9 grid."""
        res = self.client.get('/api/daily-puzzle')
        puzzle = res.get_json()['puzzle']
        self.assertEqual(len(puzzle), 9)
        for row in puzzle:
            self.assertEqual(len(row), 9)

    def test_same_day_returns_same_puzzle(self):
        """Two calls on the same day should return the same puzzle."""
        res1 = self.client.get('/api/daily-puzzle')
        res2 = self.client.get('/api/daily-puzzle')
        self.assertEqual(res1.get_json()['puzzle'], res2.get_json()['puzzle'])

    def test_puzzle_is_valid(self):
        """Daily puzzle should have a unique solution."""
        from sudoku import _count_solutions, _has_conflicts
        res = self.client.get('/api/daily-puzzle')
        data = res.get_json()
        self.assertFalse(_has_conflicts(data['puzzle']))
        self.assertEqual(_count_solutions(data['puzzle'], limit=2), 1)

    def test_difficulty_is_medium(self):
        """Daily puzzle should be Medium difficulty (40 empty cells)."""
        res = self.client.get('/api/daily-puzzle')
        puzzle = res.get_json()['puzzle']
        empty = sum(1 for r in range(9) for c in range(9) if puzzle[r][c] == 0)
        self.assertEqual(empty, 40)

    def test_seed_contains_date(self):
        """The seed should contain today's date."""
        from datetime import date
        today = date.today().isoformat()
        res = self.client.get('/api/daily-puzzle')
        seed = res.get_json()['seed']
        self.assertIn(today, seed)
        self.assertIn('daily', seed)


if __name__ == '__main__':
    unittest.main(verbosity=2)
