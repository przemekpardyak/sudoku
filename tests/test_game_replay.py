"""
Tests for game replay functionality.
Tests reconstructing play history from undo/redo stacks.
"""
import json
import copy
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module
from sudoku import generate_puzzle


class TestGameReplay(unittest.TestCase):
    """Tests for game replay from undo/redo stacks."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_game_with_undo_stack(self, undo_stack):
        """Create a game with a given undo stack."""
        puzzle, solution = generate_puzzle(difficulty=30)
        board = copy.deepcopy(puzzle)
        state = {
            'puzzle': puzzle,
            'solution': solution,
            'board': board,
            'given': [[v != 0 for v in row] for row in puzzle],
            'difficulty': 30,
            'undoStack': undo_stack,
            'redoStack': [],
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        return res.get_json()['game_id']

    def test_undo_stack_preserved(self):
        """Undo stack should be preserved when saving/loading."""
        puzzle, solution = generate_puzzle(difficulty=30)
        board1 = copy.deepcopy(puzzle)
        board2 = copy.deepcopy(puzzle)
        board2[0][0] = solution[0][0]

        undo_stack = [board1]
        game_id = self._create_game_with_undo_stack(undo_stack)

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(len(game['undoStack']), 1)
        self.assertEqual(game['undoStack'][0], board1)

    def test_redo_stack_preserved(self):
        """Redo stack should be preserved when saving/loading."""
        puzzle, solution = generate_puzzle(difficulty=30)
        board1 = copy.deepcopy(puzzle)
        board2 = copy.deepcopy(puzzle)
        board2[0][0] = solution[0][0]
        board3 = copy.deepcopy(board2)
        board3[1][1] = solution[1][1]

        state = {
            'puzzle': puzzle,
            'solution': solution,
            'board': board3,
            'given': [[v != 0 for v in row] for row in puzzle],
            'difficulty': 30,
            'undoStack': [board1, board2],
            'redoStack': [board3],
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(len(game['undoStack']), 2)
        self.assertEqual(len(game['redoStack']), 1)

    def test_empty_stacks(self):
        """Empty undo/redo stacks should be handled."""
        game_id = self._create_game_with_undo_stack([])
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(len(game['undoStack']), 0)
        self.assertEqual(len(game['redoStack']), 0)

    def test_replay_progression(self):
        """Undo stack should show progression of moves."""
        puzzle, solution = generate_puzzle(difficulty=30)
        board1 = copy.deepcopy(puzzle)

        # Make 3 moves
        board2 = copy.deepcopy(board1)
        board2[0][0] = solution[0][0]
        board3 = copy.deepcopy(board2)
        board3[1][1] = solution[1][1]
        board4 = copy.deepcopy(board3)
        board4[2][2] = solution[2][2]

        undo_stack = [board1, board2, board3]
        state = {
            'puzzle': puzzle,
            'solution': solution,
            'board': board4,
            'given': [[v != 0 for v in row] for row in puzzle],
            'difficulty': 30,
            'undoStack': undo_stack,
            'redoStack': [],
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()

        # Current board is board4 (has 3 moves)
        self.assertEqual(game['board'], board4)
        # Undo stack has 3 snapshots (before each move)
        self.assertEqual(len(game['undoStack']), 3)
        # First snapshot is the original puzzle
        self.assertEqual(game['undoStack'][0], board1)
        # Last snapshot is after 2 moves
        self.assertEqual(game['undoStack'][2], board3)

    def test_stacks_survive_update(self):
        """Undo/redo stacks should survive a partial update."""
        puzzle, solution = generate_puzzle(difficulty=30)
        board1 = copy.deepcopy(puzzle)
        board2 = copy.deepcopy(puzzle)
        board2[0][0] = solution[0][0]

        state = {
            'puzzle': puzzle,
            'solution': solution,
            'board': board2,
            'given': [[v != 0 for v in row] for row in puzzle],
            'difficulty': 30,
            'undoStack': [board1],
            'redoStack': [],
            'elapsed': 50,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        # Update just elapsed
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'elapsed': 100}),
                       content_type='application/json')

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(len(game['undoStack']), 1)
        self.assertEqual(game['elapsed'], 100)

    def test_stacks_in_export_import(self):
        """Undo/redo stacks should survive export/import."""
        puzzle, solution = generate_puzzle(difficulty=30)
        board1 = copy.deepcopy(puzzle)
        board2 = copy.deepcopy(puzzle)
        board2[0][0] = solution[0][0]

        state = {
            'puzzle': puzzle,
            'solution': solution,
            'board': board2,
            'given': [[v != 0 for v in row] for row in puzzle],
            'difficulty': 30,
            'undoStack': [board1],
            'redoStack': [],
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        # Export
        res = self.client.get(f'/api/games/{game_id}/export')
        share_code = res.get_json()['share_code']

        # Import
        res = self.client.post('/api/games/import', data=json.dumps({
            'share_code': share_code,
        }), content_type='application/json')
        imported_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{imported_id}')
        imported = res.get_json()
        self.assertEqual(len(imported['undoStack']), 1)
        self.assertEqual(len(imported['redoStack']), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
