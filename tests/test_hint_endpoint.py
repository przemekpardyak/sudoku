"""
Tests for the /api/hint endpoint.
Tests logical hint finding with naked singles, hidden singles, and backtracking.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module
from sudoku import generate_puzzle


class TestHintEndpoint(unittest.TestCase):
    """Tests for the hint API endpoint."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_hint_returns_row_col_value(self):
        """Hint should return row, col, value, and technique."""
        puzzle, _ = generate_puzzle(difficulty=30)
        res = self.client.post('/api/hint',
                              data=json.dumps({'board': puzzle}),
                              content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('row', data)
        self.assertIn('col', data)
        self.assertIn('value', data)
        self.assertIn('technique', data)
        self.assertIsInstance(data['row'], int)
        self.assertIsInstance(data['col'], int)
        self.assertGreaterEqual(data['value'], 1)
        self.assertLessEqual(data['value'], 9)

    def test_hint_value_is_correct(self):
        """The hint value should match the solution."""
        puzzle, solution = generate_puzzle(difficulty=30)
        res = self.client.post('/api/hint',
                              data=json.dumps({'board': puzzle}),
                              content_type='application/json')
        data = res.get_json()
        r, c = data['row'], data['col']
        self.assertEqual(data['value'], solution[r][c])

    def test_hint_points_to_empty_cell(self):
        """Hint should point to a cell that's currently empty."""
        puzzle, _ = generate_puzzle(difficulty=30)
        res = self.client.post('/api/hint',
                              data=json.dumps({'board': puzzle}),
                              content_type='application/json')
        data = res.get_json()
        r, c = data['row'], data['col']
        self.assertEqual(puzzle[r][c], 0)

    def test_hint_on_empty_board(self):
        """Hint on an empty board should return a valid move."""
        board = [[0] * 9 for _ in range(9)]
        res = self.client.post('/api/hint',
                              data=json.dumps({'board': board}),
                              content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('technique', data)

    def test_hint_on_complete_board(self):
        """Hint on a complete board should say it's complete."""
        puzzle, solution = generate_puzzle(difficulty=0)
        res = self.client.post('/api/hint',
                              data=json.dumps({'board': solution}),
                              content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('message', data)

    def test_hint_on_board_with_conflicts(self):
        """Hint on a board with conflicts should return 400."""
        board = [[5, 5] + [0] * 7] + [[0] * 9] * 8
        res = self.client.post('/api/hint',
                              data=json.dumps({'board': board}),
                              content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_hint_invalid_format(self):
        """Non-9x9 board should return 400."""
        res = self.client.post('/api/hint',
                              data=json.dumps({'board': [[1, 2]]}),
                              content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_hint_missing_board(self):
        """Missing board field should return 400."""
        res = self.client.post('/api/hint',
                              data=json.dumps({}),
                              content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_hint_technique_is_valid(self):
        """Technique should be one of the known values."""
        puzzle, _ = generate_puzzle(difficulty=30)
        res = self.client.post('/api/hint',
                              data=json.dumps({'board': puzzle}),
                              content_type='application/json')
        data = res.get_json()
        valid_techniques = {
            'naked_single',
            'hidden_single_row',
            'hidden_single_column',
            'hidden_single_box',
            'backtracking',
        }
        self.assertIn(data['technique'], valid_techniques)

    def test_hint_value_valid_for_board(self):
        """The hint value should not conflict with existing numbers."""
        puzzle, _ = generate_puzzle(difficulty=30)
        res = self.client.post('/api/hint',
                              data=json.dumps({'board': puzzle}),
                              content_type='application/json')
        data = res.get_json()
        r, c, v = data['row'], data['col'], data['value']
        # Value should not be in the same row
        self.assertNotIn(v, [puzzle[r][c2] for c2 in range(9) if c2 != c])
        # Value should not be in the same column
        self.assertNotIn(v, [puzzle[r2][c] for r2 in range(9) if r2 != r])


if __name__ == '__main__':
    unittest.main(verbosity=2)
