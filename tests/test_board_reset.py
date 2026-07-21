"""
Tests for the board reset functionality via the API.
These verify that a game can be reset to its original puzzle state.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestBoardReset(unittest.TestCase):
    """Tests for board reset functionality."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_reset_via_update(self):
        """Updating a game with the original puzzle should reset the board."""
        puzzle = [[5, 0, 1, 0, 0, 0, 0, 0, 0],
                  [0, 3, 0, 0, 0, 0, 0, 0, 0],
                  [0, 0, 9, 0, 0, 0, 0, 0, 0]] + [[0] * 9] * 6
        solution = [[5, 7, 1, 2, 4, 3, 6, 8, 9],
                    [8, 3, 2, 5, 7, 9, 1, 4, 6],
                    [4, 6, 9, 1, 2, 8, 3, 5, 7]] + [[1] * 9] * 6

        # Create game with partially filled board
        board = [row[:] for row in puzzle]
        board[0][1] = 7  # User fills one cell
        state = {
            'puzzle': puzzle, 'board': board, 'solution': solution,
            'difficulty': 40, 'elapsed': 50, 'completed': False,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        # "Reset" by updating board back to puzzle
        reset_state = {
            'puzzle': puzzle, 'board': puzzle, 'solution': solution,
            'difficulty': 40, 'elapsed': 50, 'completed': False,
        }
        self.client.put(f'/api/games/{game_id}', data=json.dumps(reset_state),
                       content_type='application/json')

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        # Board should match puzzle (reset)
        for r in range(9):
            for c in range(9):
                self.assertEqual(game['board'][r][c], puzzle[r][c])

    def test_reset_preserves_given(self):
        """After reset, given numbers should still be present."""
        puzzle = [[5, 0, 1] + [0] * 6] * 9
        state = {'puzzle': puzzle, 'board': [[5, 7, 1] + [0] * 6] * 9,
                 'difficulty': 40, 'elapsed': 30}
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        # Reset
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'puzzle': puzzle, 'board': puzzle}),
                       content_type='application/json')

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        # Given cells should still have values
        self.assertEqual(game['board'][0][0], 5)
        self.assertEqual(game['board'][0][2], 1)
        # User-filled cell should be empty
        self.assertEqual(game['board'][0][1], 0)

    def test_reset_clears_user_progress(self):
        """Reset should clear the progress counter back to 0."""
        puzzle = [[5, 0, 1] + [0] * 6] * 9
        state = {'puzzle': puzzle, 'board': [[5, 7, 1] + [0] * 6] * 9,
                 'difficulty': 40, 'elapsed': 30}
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        # Check progress before reset
        res = self.client.get('/api/games')
        game_before = res.get_json()['games'][0]
        self.assertNotEqual(game_before['progress'], '0/0')

        # Reset
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'puzzle': puzzle, 'board': puzzle}),
                       content_type='application/json')

        # Check progress after reset
        res = self.client.get('/api/games')
        game_after = res.get_json()['games'][0]
        # Progress should be 0/N (no user-filled cells)
        parts = game_after['progress'].split('/')
        self.assertEqual(parts[0], '0')


if __name__ == '__main__':
    unittest.main(verbosity=2)
