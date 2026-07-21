"""
Tests for the /api/validate endpoint.
Tests board validation, conflict detection, and completion checking.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestValidateEndpoint(unittest.TestCase):
    """Tests for the board validation API endpoint."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _valid_solved_board(self):
        """Return a valid solved Sudoku board."""
        return [
            [5, 3, 4, 6, 7, 8, 9, 1, 2],
            [6, 7, 2, 1, 9, 5, 3, 4, 8],
            [1, 9, 8, 3, 4, 2, 5, 6, 7],
            [8, 5, 9, 7, 6, 1, 4, 2, 3],
            [4, 2, 6, 8, 5, 3, 7, 9, 1],
            [7, 1, 3, 9, 2, 4, 8, 5, 6],
            [9, 6, 1, 5, 3, 7, 2, 8, 4],
            [2, 8, 7, 4, 1, 9, 6, 3, 5],
            [3, 4, 5, 2, 8, 6, 1, 7, 9],
        ]

    def test_valid_complete_board(self):
        """A valid, fully solved board should be valid and complete."""
        board = self._valid_solved_board()
        res = self.client.post('/api/validate',
                              data=json.dumps({'board': board}),
                              content_type='application/json')
        data = res.get_json()
        self.assertTrue(data['valid'])
        self.assertTrue(data['complete'])
        self.assertEqual(data['filled'], 81)
        self.assertEqual(data['empty'], 0)
        self.assertEqual(data['conflicts'], [])

    def test_valid_partial_board(self):
        """A valid partial board should be valid but not complete."""
        board = self._valid_solved_board()
        board[0][0] = 0  # Remove one cell
        res = self.client.post('/api/validate',
                              data=json.dumps({'board': board}),
                              content_type='application/json')
        data = res.get_json()
        self.assertTrue(data['valid'])
        self.assertFalse(data['complete'])
        self.assertEqual(data['filled'], 80)
        self.assertEqual(data['empty'], 1)

    def test_board_with_row_conflict(self):
        """Board with duplicate in a row should have conflicts."""
        board = self._valid_solved_board()
        board[0][1] = board[0][0]  # Duplicate in row
        res = self.client.post('/api/validate',
                              data=json.dumps({'board': board}),
                              content_type='application/json')
        data = res.get_json()
        self.assertFalse(data['valid'])
        self.assertGreater(len(data['conflicts']), 0)
        self.assertIn([0, 0], data['conflicts'])
        self.assertIn([0, 1], data['conflicts'])

    def test_board_with_column_conflict(self):
        """Board with duplicate in a column should have conflicts."""
        board = self._valid_solved_board()
        board[1][0] = board[0][0]  # Duplicate in column
        res = self.client.post('/api/validate',
                              data=json.dumps({'board': board}),
                              content_type='application/json')
        data = res.get_json()
        self.assertFalse(data['valid'])
        self.assertIn([0, 0], data['conflicts'])
        self.assertIn([1, 0], data['conflicts'])

    def test_board_with_box_conflict(self):
        """Board with duplicate in a 3x3 box should have conflicts."""
        board = self._valid_solved_board()
        board[1][1] = board[0][0]  # Duplicate in box (0,0)-(2,2)
        res = self.client.post('/api/validate',
                              data=json.dumps({'board': board}),
                              content_type='application/json')
        data = res.get_json()
        self.assertFalse(data['valid'])
        self.assertIn([0, 0], data['conflicts'])
        self.assertIn([1, 1], data['conflicts'])

    def test_empty_board(self):
        """An all-zero board should be valid but not complete."""
        board = [[0] * 9 for _ in range(9)]
        res = self.client.post('/api/validate',
                              data=json.dumps({'board': board}),
                              content_type='application/json')
        data = res.get_json()
        self.assertTrue(data['valid'])
        self.assertFalse(data['complete'])
        self.assertEqual(data['filled'], 0)
        self.assertEqual(data['empty'], 81)

    def test_invalid_board_format(self):
        """A non-9x9 board should return 400."""
        res = self.client.post('/api/validate',
                              data=json.dumps({'board': [[1, 2], [3, 4]]}),
                              content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_missing_board_field(self):
        """Missing board field should return 400."""
        res = self.client.post('/api/validate',
                              data=json.dumps({}),
                              content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_unique_solution_check(self):
        """A partially filled valid board should report unique_solution."""
        board = self._valid_solved_board()
        # Remove several cells
        for i in range(9):
            board[i][i] = 0
        res = self.client.post('/api/validate',
                              data=json.dumps({'board': board}),
                              content_type='application/json')
        data = res.get_json()
        self.assertTrue(data['valid'])
        self.assertIsNotNone(data['unique_solution'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
