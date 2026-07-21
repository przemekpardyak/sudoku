"""
Tests for the /api/solve endpoint.
Tests board solving, error handling, and solution uniqueness.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module
from sudoku import generate_puzzle, _has_conflicts


class TestSolveEndpoint(unittest.TestCase):
    """Tests for the board solver API endpoint."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_solve_empty_board(self):
        """An empty board should be solvable with a unique solution."""
        board = [[0] * 9 for _ in range(9)]
        res = self.client.post('/api/solve',
                              data=json.dumps({'board': board}),
                              content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('solved', data)
        solved = data['solved']
        self.assertFalse(_has_conflicts(solved))
        # All cells should be filled
        for r in range(9):
            for c in range(9):
                self.assertNotEqual(solved[r][c], 0)

    def test_solve_partial_board(self):
        """A partial board from generate_puzzle should be solvable."""
        puzzle, solution = generate_puzzle(difficulty=30)
        res = self.client.post('/api/solve',
                              data=json.dumps({'board': puzzle}),
                              content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        solved = data['solved']
        # Solved board should match the known solution
        for r in range(9):
            for c in range(9):
                self.assertEqual(solved[r][c], solution[r][c])
        self.assertTrue(data['unique'])

    def test_solve_complete_board(self):
        """A fully solved board should return itself as the solution."""
        puzzle, solution = generate_puzzle(difficulty=0)
        res = self.client.post('/api/solve',
                              data=json.dumps({'board': solution}),
                              content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['solved'], solution)

    def test_solve_board_with_conflicts(self):
        """A board with conflicts should return 400."""
        board = [
            [5, 5, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
        ]
        res = self.client.post('/api/solve',
                              data=json.dumps({'board': board}),
                              content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_solve_invalid_board_format(self):
        """A non-9x9 board should return 400."""
        res = self.client.post('/api/solve',
                              data=json.dumps({'board': [[1, 2], [3, 4]]}),
                              content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_solve_missing_board_field(self):
        """Missing board field should return 400."""
        res = self.client.post('/api/solve',
                              data=json.dumps({}),
                              content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_solve_returns_unique_flag(self):
        """The response should include a unique flag."""
        puzzle, _ = generate_puzzle(difficulty=30)
        res = self.client.post('/api/solve',
                              data=json.dumps({'board': puzzle}),
                              content_type='application/json')
        data = res.get_json()
        self.assertIn('unique', data)
        self.assertTrue(data['unique'])

    def test_solve_preserves_input_board(self):
        """The input board should not be modified (deep copy)."""
        puzzle, solution = generate_puzzle(difficulty=30)
        original = [row[:] for row in puzzle]
        self.client.post('/api/solve',
                        data=json.dumps({'board': puzzle}),
                        content_type='application/json')
        # Input board should be unchanged
        for r in range(9):
            for c in range(9):
                self.assertEqual(puzzle[r][c], original[r][c])


if __name__ == '__main__':
    unittest.main(verbosity=2)
