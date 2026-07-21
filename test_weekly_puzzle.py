"""
Tests for the weekly puzzle endpoint.
"""
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module
from sudoku import _has_conflicts


class TestWeeklyPuzzle(unittest.TestCase):
    """Tests for the weekly puzzle API endpoint."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_weekly_puzzle_returns_valid_board(self):
        """Weekly puzzle should return a valid 9x9 board."""
        res = self.client.get('/api/weekly-puzzle')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        puzzle = data['puzzle']
        self.assertEqual(len(puzzle), 9)
        for row in puzzle:
            self.assertEqual(len(row), 9)

    def test_weekly_puzzle_has_solution(self):
        """Weekly puzzle should include a solution."""
        res = self.client.get('/api/weekly-puzzle')
        data = res.get_json()
        solution = data['solution']
        self.assertFalse(_has_conflicts(solution))

    def test_weekly_puzzle_has_seed(self):
        """Weekly puzzle should have a reproducible seed."""
        res = self.client.get('/api/weekly-puzzle')
        data = res.get_json()
        self.assertIn('seed', data)
        self.assertTrue(data['seed'].startswith('weekly-'))

    def test_weekly_puzzle_has_week(self):
        """Weekly puzzle should include the week date."""
        res = self.client.get('/api/weekly-puzzle')
        data = res.get_json()
        self.assertIn('week', data)

    def test_weekly_puzzle_has_difficulty(self):
        """Weekly puzzle should be hard difficulty (50)."""
        res = self.client.get('/api/weekly-puzzle')
        data = res.get_json()
        self.assertEqual(data['difficulty'], 50)

    def test_weekly_puzzle_consistent_within_week(self):
        """Two calls should return the same puzzle (same week)."""
        res1 = self.client.get('/api/weekly-puzzle')
        res2 = self.client.get('/api/weekly-puzzle')
        self.assertEqual(res1.get_json()['puzzle'], res2.get_json()['puzzle'])

    def test_weekly_puzzle_has_empty_cells(self):
        """Weekly puzzle should have empty cells (not solved)."""
        res = self.client.get('/api/weekly-puzzle')
        data = res.get_json()
        puzzle = data['puzzle']
        has_empty = any(0 in row for row in puzzle)
        self.assertTrue(has_empty)


if __name__ == '__main__':
    unittest.main(verbosity=2)
