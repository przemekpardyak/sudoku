"""
Tests for undo/redo functionality in the game logic.
These test the snapshot/restore logic via the API's save/load flow.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestUndoRedoStatePreservation(unittest.TestCase):
    """Test that undo/redo stacks are properly saved and restored."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_game_with_state(self, board, undo_stack=None, redo_stack=None):
        state = {
            'puzzle': [[0]*9]*9,
            'solution': [[1]*9]*9,
            'board': board,
            'given': [[False]*9]*9,
            'notes': [[[False]*9]*9]*9,
            'undoStack': undo_stack or [],
            'redoStack': redo_stack or [],
            'mistakes': 0,
            'elapsed': 0,
            'difficulty': 40,
            'completed': False,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        return res.get_json()['game_id']

    def test_undo_stack_saved(self):
        """Undo stack should be saved and restored."""
        undo = [
            {'board': [[0]*9]*9, 'notes': [[[False]*9]*9]*9,
             'given': [[False]*9]*9, 'mistakes': 0}
        ]
        board = [[5 if r == 0 and c == 0 else 0 for c in range(9)] for r in range(9)]
        game_id = self._create_game_with_state(board, undo_stack=undo)

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(len(game['undoStack']), 1)
        self.assertEqual(game['undoStack'][0]['mistakes'], 0)

    def test_redo_stack_saved(self):
        """Redo stack should be saved and restored."""
        redo = [
            {'board': [[7 if r == 0 and c == 0 else 0 for c in range(9)] for r in range(9)],
             'notes': [[[False]*9]*9]*9,
             'given': [[False]*9]*9, 'mistakes': 1}
        ]
        board = [[0]*9]*9
        game_id = self._create_game_with_state(board, redo_stack=redo)

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(len(game['redoStack']), 1)

    def test_empty_stacks_saved(self):
        """Empty undo/redo stacks should be saved correctly."""
        game_id = self._create_game_with_state([[0]*9]*9)

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['undoStack'], [])
        self.assertEqual(game['redoStack'], [])

    def test_multiple_undo_entries_saved(self):
        """Multiple undo entries should all be preserved."""
        undo = [
            {'board': [[0]*9]*9, 'notes': [[[False]*9]*9]*9,
             'given': [[False]*9]*9, 'mistakes': i}
            for i in range(5)
        ]
        board = [[9]*9]*9
        game_id = self._create_game_with_state(board, undo_stack=undo)

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(len(game['undoStack']), 5)
        self.assertEqual(game['undoStack'][0]['mistakes'], 0)
        self.assertEqual(game['undoStack'][4]['mistakes'], 4)

    def test_update_preserves_stacks(self):
        """PUT update should preserve the undo/redo stacks."""
        board = [[5 if r == 0 and c == 0 else 0 for c in range(9)] for r in range(9)]
        game_id = self._create_game_with_state(board)

        # Add undo stack via update
        state = {
            'board': board,
            'undoStack': [{'board': [[0]*9]*9, 'notes': [[[False]*9]*9]*9,
                          'given': [[False]*9]*9, 'mistakes': 0}],
            'redoStack': [],
            'mistakes': 1,
        }
        self.client.put(f'/api/games/{game_id}', data=json.dumps(state),
                        content_type='application/json')

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(len(game['undoStack']), 1)
        self.assertEqual(game['mistakes'], 1)

    def test_notes_saved_with_correct_structure(self):
        """Notes (3D array) should be preserved with correct structure."""
        notes = [[[False]*9 for _ in range(9)] for _ in range(9)]
        notes[0][0][3] = True  # pencil mark for number 4 at (0,0)
        notes[4][4][7] = True  # pencil mark for number 8 at (4,4)

        state = {
            'puzzle': [[0]*9]*9,
            'solution': [[1]*9]*9,
            'board': [[0]*9]*9,
            'given': [[False]*9]*9,
            'notes': notes,
            'undoStack': [],
            'redoStack': [],
            'mistakes': 0,
            'elapsed': 0,
            'difficulty': 40,
            'completed': False,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertTrue(game['notes'][0][0][3])
        self.assertTrue(game['notes'][4][4][7])
        self.assertFalse(game['notes'][1][1][3])


class TestGameCompletionState(unittest.TestCase):
    """Test game completion detection and persistence."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_completed_flag_saved(self):
        """When a game is completed, completed=True should be saved."""
        state = {'difficulty': 40, 'completed': True, 'elapsed': 300, 'mistakes': 2}
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        self.assertTrue(res.get_json()['completed'])

    def test_completed_flag_shown_in_list(self):
        """Completed games should show completed=true in the list."""
        # Create an incomplete game
        self.client.post('/api/games',
                        data=json.dumps({'difficulty': 40, 'completed': False}),
                        content_type='application/json')
        # Create a completed game
        self.client.post('/api/games',
                        data=json.dumps({'difficulty': 40, 'completed': True}),
                        content_type='application/json')

        res = self.client.get('/api/games')
        games = res.get_json()['games']
        completed = [g for g in games if g['completed']]
        incomplete = [g for g in games if not g['completed']]
        self.assertEqual(len(completed), 1)
        self.assertEqual(len(incomplete), 1)

    def test_update_to_completed(self):
        """Updating a game to completed should persist."""
        state = {'difficulty': 40, 'completed': False}
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        # Complete the game
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'completed': True, 'elapsed': 200}),
                       content_type='application/json')

        res = self.client.get(f'/api/games/{game_id}')
        self.assertTrue(res.get_json()['completed'])
        self.assertEqual(res.get_json()['elapsed'], 200)


if __name__ == '__main__':
    unittest.main(verbosity=2)
