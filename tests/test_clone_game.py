"""
Tests for the game clone endpoint.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module
from sudoku import generate_puzzle


class TestCloneGame(unittest.TestCase):
    """Tests for the game clone API endpoint."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_game_with_state(self, board=None, completed=False):
        puzzle, solution = generate_puzzle(difficulty=30)
        state = {
            'puzzle': puzzle,
            'solution': solution,
            'board': board or puzzle,
            'difficulty': 30,
            'elapsed': 150,
            'mistakes': 3,
            'completed': completed,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        return res.get_json()['game_id'], puzzle, solution

    def test_clone_creates_new_game(self):
        """Cloning should create a new game with a different ID."""
        game_id, _, _ = self._create_game_with_state()
        res = self.client.post(f'/api/games/{game_id}/clone')
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertNotEqual(data['game_id'], game_id)
        self.assertEqual(data['source_game_id'], game_id)

    def test_clone_resets_board_to_puzzle(self):
        """Cloned game should have board reset to original puzzle state."""
        game_id, puzzle, solution = self._create_game_with_state()
        # Modify the board by filling in a cell
        modified_board = [row[:] for row in puzzle]
        for r in range(9):
            for c in range(9):
                if modified_board[r][c] == 0:
                    modified_board[r][c] = solution[r][c]
                    break
            else:
                continue
            break
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'board': modified_board}),
                       content_type='application/json')

        # Clone
        res = self.client.post(f'/api/games/{game_id}/clone')
        clone_id = res.get_json()['game_id']

        # Get cloned game
        res = self.client.get(f'/api/games/{clone_id}')
        cloned = res.get_json()
        # Board should match puzzle, not modified board
        self.assertEqual(cloned['board'], puzzle)

    def test_clone_preserves_puzzle_and_solution(self):
        """Cloned game should have the same puzzle and solution."""
        game_id, puzzle, solution = self._create_game_with_state()
        res = self.client.post(f'/api/games/{game_id}/clone')
        clone_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{clone_id}')
        cloned = res.get_json()
        self.assertEqual(cloned['puzzle'], puzzle)
        self.assertEqual(cloned['solution'], solution)

    def test_clone_resets_progress(self):
        """Cloned game should have zero elapsed time and mistakes."""
        game_id, _, _ = self._create_game_with_state()
        res = self.client.post(f'/api/games/{game_id}/clone')
        clone_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{clone_id}')
        cloned = res.get_json()
        self.assertEqual(cloned['elapsed'], 0)
        self.assertEqual(cloned['mistakes'], 0)
        self.assertFalse(cloned['completed'])

    def test_clone_nonexistent_game(self):
        """Cloning a nonexistent game should return 404."""
        res = self.client.post('/api/games/nonexistent-id/clone')
        self.assertEqual(res.status_code, 404)

    def test_clone_preserves_difficulty(self):
        """Cloned game should have the same difficulty as the source."""
        game_id, _, _ = self._create_game_with_state()
        res = self.client.post(f'/api/games/{game_id}/clone')
        clone_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{clone_id}')
        cloned = res.get_json()
        self.assertEqual(cloned['difficulty'], 30)

    def test_clone_has_cloned_tag(self):
        """Cloned game should have 'cloned' tag."""
        game_id, _, _ = self._create_game_with_state()
        res = self.client.post(f'/api/games/{game_id}/clone')
        clone_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{clone_id}')
        cloned = res.get_json()
        self.assertIn('cloned', cloned.get('tags', []))


if __name__ == '__main__':
    unittest.main(verbosity=2)
