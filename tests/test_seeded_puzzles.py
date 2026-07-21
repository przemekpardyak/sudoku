"""
Tests for seeded puzzle generation — reproducible puzzles from a seed.
"""
import unittest
import json
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestSeededPuzzles(unittest.TestCase):
    """Tests for reproducible puzzle generation via seed parameter."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_same_seed_produces_same_puzzle(self):
        """Two calls with the same seed should produce identical puzzles."""
        res1 = self.client.get('/api/new-game?difficulty=30&seed=test123')
        res2 = self.client.get('/api/new-game?difficulty=30&seed=test123')
        p1 = res1.get_json()['puzzle']
        p2 = res2.get_json()['puzzle']
        self.assertEqual(p1, p2)

    def test_different_seeds_produce_different_puzzles(self):
        """Different seeds should (almost certainly) produce different puzzles."""
        res1 = self.client.get('/api/new-game?difficulty=30&seed=seedA')
        res2 = self.client.get('/api/new-game?difficulty=30&seed=seedB')
        p1 = res1.get_json()['puzzle']
        p2 = res2.get_json()['puzzle']
        self.assertNotEqual(p1, p2)

    def test_seed_returned_in_response(self):
        """The seed should be returned in the response."""
        res = self.client.get('/api/new-game?difficulty=40&seed=myseed')
        data = res.get_json()
        self.assertEqual(data['seed'], 'myseed')

    def test_no_seed_returns_null_seed(self):
        """Without a seed, the response seed should be None."""
        res = self.client.get('/api/new-game?difficulty=40')
        data = res.get_json()
        self.assertIsNone(data['seed'])

    def test_seeded_puzzle_is_valid(self):
        """A seeded puzzle should still be valid (unique solution, correct structure)."""
        from sudoku import _count_solutions, _has_conflicts
        res = self.client.get('/api/new-game?difficulty=30&seed=valid42')
        data = res.get_json()
        puzzle = data['puzzle']
        solution = data['solution']
        # No conflicts
        self.assertFalse(_has_conflicts(puzzle))
        # Unique solution
        self.assertEqual(_count_solutions(puzzle, limit=2), 1)
        # Puzzle is subset of solution
        for r in range(9):
            for c in range(9):
                if puzzle[r][c] != 0:
                    self.assertEqual(puzzle[r][c], solution[r][c])

    def test_seeded_puzzle_correct_difficulty(self):
        """A seeded puzzle should have the correct number of empty cells."""
        res = self.client.get('/api/new-game?difficulty=50&seed=hardseed')
        puzzle = res.get_json()['puzzle']
        empty = sum(1 for r in range(9) for c in range(9) if puzzle[r][c] == 0)
        self.assertEqual(empty, 50)

    def test_seed_with_different_difficulties(self):
        """Same seed with different difficulties should produce valid puzzles."""
        for diff in [30, 40, 50]:
            res = self.client.get(f'/api/new-game?difficulty={diff}&seed=samediff')
            data = res.get_json()
            empty = sum(1 for r in range(9) for c in range(9) if data['puzzle'][r][c] == 0)
            self.assertEqual(empty, diff)


if __name__ == '__main__':
    unittest.main(verbosity=2)
