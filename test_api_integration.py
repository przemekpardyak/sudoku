"""
Tests for the /api/solve and /api/hint endpoint integration.
Tests that solving and hinting work together correctly.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module
from sudoku import generate_puzzle


class TestSolveHintIntegration(unittest.TestCase):
    """Integration tests for solve + hint endpoints."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_solve_then_hint_complete(self):
        """After solving, hint should say board is complete."""
        puzzle, solution = generate_puzzle(difficulty=30)
        # Solve
        self.client.post('/api/solve',
                        data=json.dumps({'board': puzzle}),
                        content_type='application/json')
        # Hint on solved board
        res = self.client.post('/api/hint',
                             data=json.dumps({'board': solution}),
                             content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('message', data)

    def test_validate_then_solve(self):
        """Validate a partial board, then solve it."""
        puzzle, solution = generate_puzzle(difficulty=30)
        # Validate
        res = self.client.post('/api/validate',
                             data=json.dumps({'board': puzzle}),
                             content_type='application/json')
        self.assertTrue(res.get_json()['valid'])
        self.assertFalse(res.get_json()['complete'])

        # Solve
        res = self.client.post('/api/solve',
                             data=json.dumps({'board': puzzle}),
                             content_type='application/json')
        solved = res.get_json()['solved']

        # Validate solved board
        res = self.client.post('/api/validate',
                             data=json.dumps({'board': solved}),
                             content_type='application/json')
        self.assertTrue(res.get_json()['valid'])
        self.assertTrue(res.get_json()['complete'])

    def test_hint_progression(self):
        """Successive hints should fill the board."""
        puzzle, solution = generate_puzzle(difficulty=30)
        board = [row[:] for row in puzzle]

        for _ in range(5):
            # Find empty cell
            empty = False
            for r in range(9):
                for c in range(9):
                    if board[r][c] == 0:
                        empty = True
                        break
                if empty:
                    break
            if not empty:
                break

            res = self.client.post('/api/hint',
                                 data=json.dumps({'board': board}),
                                 content_type='application/json')
            data = res.get_json()
            if 'message' in data:
                break
            r, c, v = data['row'], data['col'], data['value']
            self.assertEqual(v, solution[r][c])
            board[r][c] = v

    def test_solve_matches_hint_value(self):
        """The solve endpoint should produce values consistent with hints."""
        puzzle, solution = generate_puzzle(difficulty=30)
        # Get hint
        res = self.client.post('/api/hint',
                             data=json.dumps({'board': puzzle}),
                             content_type='application/json')
        hint_data = res.get_json()
        r, c, v = hint_data['row'], hint_data['col'], hint_data['value']

        # Get solved board
        res = self.client.post('/api/solve',
                             data=json.dumps({'board': puzzle}),
                             content_type='application/json')
        solved = res.get_json()['solved']

        # Hint value should match solved board
        self.assertEqual(solved[r][c], v)

    def test_archive_then_validate(self):
        """Archive a game and validate a board with conflicts."""
        state = {
            'puzzle': [[5]*9]*9,
            'board': [[5]*9]*9,
            'difficulty': 40,
            'elapsed': 100,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                             content_type='application/json')
        game_id = res.get_json()['game_id']

        # Archive
        self.client.put(f'/api/games/{game_id}/archive',
                       data=json.dumps({'archived': True}),
                       content_type='application/json')

        # Validate a board with a clear row conflict
        conflict_board = [
            [5, 3, 0, 0, 7, 0, 0, 0, 0],
            [6, 0, 0, 1, 9, 5, 0, 0, 0],  # 5 in col 4 conflicts with row 0
            [0, 9, 8, 0, 0, 0, 0, 6, 0],
            [8, 0, 0, 0, 6, 0, 0, 0, 3],
            [4, 0, 0, 8, 0, 3, 0, 0, 1],
            [7, 0, 0, 0, 2, 0, 0, 0, 6],
            [0, 6, 0, 0, 0, 0, 2, 8, 0],
            [0, 0, 0, 4, 1, 9, 0, 0, 5],
            [0, 0, 0, 0, 8, 0, 0, 7, 9],
        ]
        # Add a duplicate 5 in row 0
        conflict_board[0][2] = 7  # 7 already in row 0 at col 4
        res = self.client.post('/api/validate',
                             data=json.dumps({'board': conflict_board}),
                             content_type='application/json')
        data = res.get_json()
        self.assertFalse(data['valid'])
        self.assertGreater(len(data['conflicts']), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
