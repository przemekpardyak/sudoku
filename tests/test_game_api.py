"""
Tests for the /api/new-game endpoint and puzzle generation via the API.
"""
import unittest
import json
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestNewGameAPI(unittest.TestCase):
    """Tests for /api/new-game endpoint."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_default_difficulty(self):
        """Default difficulty should be 40 (Medium)."""
        res = self.client.get('/api/new-game')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        empty = sum(1 for r in range(9) for c in range(9) if data['puzzle'][r][c] == 0)
        self.assertEqual(empty, 40)

    def test_easy_difficulty(self):
        """Easy difficulty should have 30 empty cells."""
        res = self.client.get('/api/new-game?difficulty=30')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        empty = sum(1 for r in range(9) for c in range(9) if data['puzzle'][r][c] == 0)
        self.assertEqual(empty, 30)

    def test_hard_difficulty(self):
        """Hard difficulty should have 50 empty cells."""
        res = self.client.get('/api/new-game?difficulty=50')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        empty = sum(1 for r in range(9) for c in range(9) if data['puzzle'][r][c] == 0)
        self.assertEqual(empty, 50)

    def test_puzzle_is_9x9(self):
        """Puzzle and solution should be 9x9 arrays."""
        res = self.client.get('/api/new-game')
        data = res.get_json()
        self.assertEqual(len(data['puzzle']), 9)
        self.assertEqual(len(data['solution']), 9)
        for row in data['puzzle']:
            self.assertEqual(len(row), 9)
        for row in data['solution']:
            self.assertEqual(len(row), 9)

    def test_solution_is_valid(self):
        """Solution should be a valid solved Sudoku board."""
        res = self.client.get('/api/new-game')
        solution = res.get_json()['solution']
        # Check rows
        for row in solution:
            self.assertEqual(sorted(row), list(range(1, 10)))
        # Check columns
        for c in range(9):
            col = [solution[r][c] for r in range(9)]
            self.assertEqual(sorted(col), list(range(1, 10)))
        # Check boxes
        for br in range(0, 9, 3):
            for bc in range(0, 9, 3):
                box = [solution[br + dr][bc + dc] for dr in range(3) for dc in range(3)]
                self.assertEqual(sorted(box), list(range(1, 10)))

    def test_puzzle_is_subset_of_solution(self):
        """Every non-zero puzzle cell should match the solution."""
        res = self.client.get('/api/new-game')
        data = res.get_json()
        for r in range(9):
            for c in range(9):
                if data['puzzle'][r][c] != 0:
                    self.assertEqual(data['puzzle'][r][c], data['solution'][r][c])

    def test_puzzle_has_unique_solution(self):
        """Generated puzzle should have exactly one solution."""
        from sudoku import _count_solutions
        res = self.client.get('/api/new-game?difficulty=30')
        puzzle = res.get_json()['puzzle']
        self.assertEqual(_count_solutions(puzzle, limit=2), 1)

    def test_no_duplicates_in_puzzle(self):
        """Puzzle should have no duplicate values in any row, column, or box."""
        res = self.client.get('/api/new-game')
        puzzle = res.get_json()['puzzle']
        # Rows
        for row in puzzle:
            vals = [v for v in row if v != 0]
            self.assertEqual(len(vals), len(set(vals)))
        # Columns
        for c in range(9):
            vals = [puzzle[r][c] for r in range(9) if puzzle[r][c] != 0]
            self.assertEqual(len(vals), len(set(vals)))
        # Boxes
        for br in range(0, 9, 3):
            for bc in range(0, 9, 3):
                box = [puzzle[br + dr][bc + dc] for dr in range(3) for dc in range(3) if puzzle[br + dr][bc + dc] != 0]
                self.assertEqual(len(box), len(set(box)))

    def test_different_calls_produce_different_puzzles(self):
        """Two calls should (almost certainly) produce different puzzles."""
        import random
        random.seed(42)
        p1 = self.client.get('/api/new-game').get_json()['puzzle']
        random.seed(99)
        p2 = self.client.get('/api/new-game').get_json()['puzzle']
        self.assertNotEqual(p1, p2)

    def test_invalid_difficulty_returns_error(self):
        """Negative or invalid difficulty should still return a valid puzzle."""
        res = self.client.get('/api/new-game?difficulty=0')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        # With difficulty 0, puzzle should equal solution (no cells removed)
        self.assertEqual(data['puzzle'], data['solution'])


class TestGameAPIErrorHandling(unittest.TestCase):
    """Tests for error handling in the game API."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_get_game_with_invalid_id(self):
        """GET /api/games/<invalid> should return 404."""
        res = self.client.get('/api/games/not-a-real-id')
        self.assertEqual(res.status_code, 404)

    def test_put_with_invalid_id(self):
        """PUT /api/games/<invalid> should return 404."""
        res = self.client.put('/api/games/nonexistent',
                              data=json.dumps({'mistakes': 1}),
                              content_type='application/json')
        self.assertEqual(res.status_code, 404)

    def test_delete_with_invalid_id(self):
        """DELETE /api/games/<invalid> should return 404."""
        res = self.client.delete('/api/games/does-not-exist')
        self.assertEqual(res.status_code, 404)

    def test_post_without_body(self):
        """POST /api/games without a body should handle gracefully."""
        res = self.client.post('/api/games', content_type='application/json')
        # Should either create with empty state or return 400
        self.assertIn(res.status_code, [201, 400])

    def test_post_with_invalid_json(self):
        """POST /api/games with invalid JSON should return 400."""
        res = self.client.post('/api/games',
                              data='not json',
                              content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_list_with_limit_param(self):
        """GET /api/games?limit=5 should respect the limit."""
        for _ in range(10):
            self.client.post('/api/games',
                            data=json.dumps({'difficulty': 40}),
                            content_type='application/json')
        res = self.client.get('/api/games?limit=5')
        games = res.get_json()['games']
        self.assertLessEqual(len(games), 5)

    def test_list_with_no_games(self):
        """GET /api/games with no saved games should return empty list."""
        res = self.client.get('/api/games')
        data = res.get_json()
        self.assertEqual(data['games'], [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
