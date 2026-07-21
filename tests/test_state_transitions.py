"""
Tests for game state transitions.
Tests the lifecycle of game state as it moves through different stages.
"""
import json
import copy
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module
from sudoku import generate_puzzle


class TestStateTransitions(unittest.TestCase):
    """Tests for game state transitions through the lifecycle."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_transition_new_to_in_progress(self):
        """Game should transition from new to in-progress correctly."""
        puzzle, solution = generate_puzzle(difficulty=30)
        # Create new game
        res = self.client.post('/api/games', data=json.dumps({
            'puzzle': puzzle, 'solution': solution,
            'board': copy.deepcopy(puzzle), 'difficulty': 30,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        # Check progress is 0%
        res = self.client.get(f'/api/games/{game_id}/progress')
        self.assertEqual(res.get_json()['progress_pct'], 0)

        # Fill one cell
        board = copy.deepcopy(puzzle)
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    board[r][c] = solution[r][c]
                    break
            else:
                continue
            break

        self.client.put(f'/api/games/{game_id}', data=json.dumps({
            'board': board, 'elapsed': 30,
        }), content_type='application/json')

        # Check progress > 0%
        res = self.client.get(f'/api/games/{game_id}/progress')
        self.assertGreater(res.get_json()['progress_pct'], 0)

    def test_transition_in_progress_to_completed(self):
        """Game should transition from in-progress to completed."""
        puzzle, solution = generate_puzzle(difficulty=30)
        res = self.client.post('/api/games', data=json.dumps({
            'puzzle': puzzle, 'solution': solution,
            'board': copy.deepcopy(puzzle), 'difficulty': 30,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        # Complete the game
        self.client.put(f'/api/games/{game_id}', data=json.dumps({
            'board': solution, 'completed': True, 'elapsed': 120,
        }), content_type='application/json')

        res = self.client.get(f'/api/games/{game_id}')
        self.assertTrue(res.get_json()['completed'])

    def test_transition_completed_to_archived(self):
        """Completed game should be archivable."""
        puzzle, solution = generate_puzzle(difficulty=30)
        res = self.client.post('/api/games', data=json.dumps({
            'puzzle': puzzle, 'solution': solution,
            'board': solution, 'difficulty': 30,
            'completed': True, 'elapsed': 100,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        # Archive
        self.client.put(f'/api/games/{game_id}/archive', data=json.dumps({
            'archived': True,
        }), content_type='application/json')

        res = self.client.get(f'/api/games/{game_id}')
        self.assertTrue(res.get_json().get('archived', False))

    def test_transition_archived_to_unarchived(self):
        """Archived game should be unarchivable."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'archived': True,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        # Unarchive
        self.client.put(f'/api/games/{game_id}/archive', data=json.dumps({
            'archived': False,
        }), content_type='application/json')

        games = self.client.get('/api/games').get_json()['games']
        game = [g for g in games if g['game_id'] == game_id][0]
        self.assertFalse(game['archived'])

    def test_transition_clone_resets_state(self):
        """Cloning should reset board but keep puzzle."""
        puzzle, solution = generate_puzzle(difficulty=30)
        res = self.client.post('/api/games', data=json.dumps({
            'puzzle': puzzle, 'solution': solution,
            'board': solution, 'difficulty': 30,
            'completed': True, 'elapsed': 100,
        }), content_type='application/json')
        original_id = res.get_json()['game_id']

        # Clone
        res = self.client.post(f'/api/games/{original_id}/clone')
        clone_id = res.get_json()['game_id']

        # Clone should not be completed
        clone = self.client.get(f'/api/games/{clone_id}').get_json()
        self.assertFalse(clone.get('completed', False))
        self.assertEqual(clone['elapsed'], 0)

    def test_transition_import_preserves_state(self):
        """Importing should preserve the game state."""
        puzzle, solution = generate_puzzle(difficulty=30)
        res = self.client.post('/api/games', data=json.dumps({
            'puzzle': puzzle, 'solution': solution,
            'board': solution, 'difficulty': 30,
            'completed': True, 'elapsed': 100, 'mistakes': 2,
        }), content_type='application/json')
        original_id = res.get_json()['game_id']

        # Export and import
        export_res = self.client.get(f'/api/games/{original_id}/export')
        share_code = export_res.get_json()['share_code']
        import_res = self.client.post('/api/games/import', data=json.dumps({
            'share_code': share_code,
        }), content_type='application/json')
        imported_id = import_res.get_json()['game_id']

        imported = self.client.get(f'/api/games/{imported_id}').get_json()
        self.assertTrue(imported.get('completed', False))
        self.assertEqual(imported['elapsed'], 100)
        self.assertEqual(imported['mistakes'], 2)

    def test_transition_rate_updates_rating(self):
        """Rating should update on completed game."""
        puzzle, solution = generate_puzzle(difficulty=30)
        res = self.client.post('/api/games', data=json.dumps({
            'puzzle': puzzle, 'solution': solution,
            'board': solution, 'difficulty': 30,
            'completed': True, 'elapsed': 100,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        # Rate 3 stars, then change to 5
        self.client.put(f'/api/games/{game_id}/rate', data=json.dumps({
            'rating': 3,
        }), content_type='application/json')
        self.assertEqual(
            self.client.get(f'/api/games/{game_id}').get_json()['rating'], 3)

        self.client.put(f'/api/games/{game_id}/rate', data=json.dumps({
            'rating': 5,
        }), content_type='application/json')
        self.assertEqual(
            self.client.get(f'/api/games/{game_id}').get_json()['rating'], 5)

    def test_transition_add_remove_tags(self):
        """Tags should be addable and removable."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'tags': ['fun', 'easy'],
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        # Add more tags
        self.client.put(f'/api/games/{game_id}', data=json.dumps({
            'tags': ['fun', 'easy', 'quick'],
        }), content_type='application/json')
        game = self.client.get(f'/api/games/{game_id}').get_json()
        self.assertIn('quick', game['tags'])

        # Remove tags
        self.client.put(f'/api/games/{game_id}', data=json.dumps({
            'tags': [],
        }), content_type='application/json')
        game = self.client.get(f'/api/games/{game_id}').get_json()
        self.assertEqual(game['tags'], [])

    def test_transition_favorite_toggle(self):
        """Favorite should toggle correctly."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        # Favorite
        self.client.put(f'/api/games/{game_id}', data=json.dumps({
            'favorite': True,
        }), content_type='application/json')
        game = self.client.get(f'/api/games/{game_id}').get_json()
        self.assertTrue(game.get('favorite', False))

        # Unfavorite
        self.client.put(f'/api/games/{game_id}', data=json.dumps({
            'favorite': False,
        }), content_type='application/json')
        game = self.client.get(f'/api/games/{game_id}').get_json()
        self.assertFalse(game.get('favorite', False))

    def test_transition_update_preserves_completed(self):
        """Updating a completed game should keep it completed."""
        puzzle, solution = generate_puzzle(difficulty=30)
        res = self.client.post('/api/games', data=json.dumps({
            'puzzle': puzzle, 'solution': solution,
            'board': solution, 'difficulty': 30,
            'completed': True, 'elapsed': 100,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        # Update notes
        self.client.put(f'/api/games/{game_id}', data=json.dumps({
            'notes': 'Great game!',
        }), content_type='application/json')

        game = self.client.get(f'/api/games/{game_id}').get_json()
        self.assertTrue(game['completed'])  # Still completed
        self.assertEqual(game['notes'], 'Great game!')


if __name__ == '__main__':
    unittest.main(verbosity=2)
