"""
Tests for data integrity across operations.
Tests that game data stays consistent through various operations.
"""
import json
import copy
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module
from sudoku import generate_puzzle, _has_conflicts


class TestDataIntegrity(unittest.TestCase):
    """Tests for data integrity across operations."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_puzzle_solution_consistency(self):
        """Puzzle and solution should be consistent after save/load."""
        puzzle, solution = generate_puzzle(difficulty=30)
        state = {
            'puzzle': puzzle,
            'solution': solution,
            'board': puzzle,
            'difficulty': 30,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['puzzle'], puzzle)
        self.assertEqual(game['solution'], solution)

    def test_board_does_not_mutate_puzzle(self):
        """Updating board should not modify the puzzle."""
        puzzle, solution = generate_puzzle(difficulty=30)
        state = {
            'puzzle': puzzle,
            'solution': solution,
            'board': copy.deepcopy(puzzle),
            'difficulty': 30,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        # Modify the board — find an empty cell
        board = copy.deepcopy(puzzle)
        # Find first empty cell
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    board[r][c] = solution[r][c]
                    break
            else:
                continue
            break
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'board': board}),
                       content_type='application/json')

        # Puzzle should be unchanged
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['puzzle'], puzzle)
        self.assertNotEqual(game['board'], game['puzzle'])

    def test_given_mask_consistency(self):
        """Given mask should match puzzle clues."""
        puzzle, solution = generate_puzzle(difficulty=30)
        given = [[puzzle[r][c] != 0 for c in range(9)] for r in range(9)]
        state = {
            'puzzle': puzzle,
            'solution': solution,
            'board': copy.deepcopy(puzzle),
            'given': given,
            'difficulty': 30,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['given'], given)

    def test_notes_structure_integrity(self):
        """Notes should maintain 9x9x9 structure."""
        notes = [[[False]*9 for _ in range(9)] for _ in range(9)]
        notes[0][0][3] = True  # Cell (0,0) has note 4
        notes[4][4][7] = True  # Cell (4,4) has note 8

        state = {
            'notes': notes,
            'difficulty': 30,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(len(game['notes']), 9)
        self.assertEqual(len(game['notes'][0]), 9)
        self.assertEqual(len(game['notes'][0][0]), 9)
        self.assertTrue(game['notes'][0][0][3])
        self.assertTrue(game['notes'][4][4][7])
        self.assertFalse(game['notes'][0][0][0])

    def test_difficulty_persistence(self):
        """Difficulty should persist across saves."""
        for diff in [20, 30, 40, 50, 58]:
            state = {'difficulty': diff}
            res = self.client.post('/api/games', data=json.dumps(state),
                                   content_type='application/json')
            game_id = res.get_json()['game_id']
            res = self.client.get(f'/api/games/{game_id}')
            self.assertEqual(res.get_json()['difficulty'], diff)

    def test_elapsed_persistence(self):
        """Elapsed time should persist across saves."""
        for elapsed in [0, 30, 100, 500, 3600]:
            state = {'difficulty': 30, 'elapsed': elapsed}
            res = self.client.post('/api/games', data=json.dumps(state),
                                   content_type='application/json')
            game_id = res.get_json()['game_id']
            res = self.client.get(f'/api/games/{game_id}')
            self.assertEqual(res.get_json()['elapsed'], elapsed)

    def test_mistakes_persistence(self):
        """Mistakes counter should persist."""
        for mistakes in [0, 1, 5, 10, 50]:
            state = {'difficulty': 30, 'mistakes': mistakes}
            res = self.client.post('/api/games', data=json.dumps(state),
                                   content_type='application/json')
            game_id = res.get_json()['game_id']
            res = self.client.get(f'/api/games/{game_id}')
            self.assertEqual(res.get_json()['mistakes'], mistakes)

    def test_hints_used_persistence(self):
        """Hints used counter should persist."""
        for hints in [0, 1, 3, 5, 10]:
            state = {'difficulty': 30, 'hintsUsed': hints}
            res = self.client.post('/api/games', data=json.dumps(state),
                                   content_type='application/json')
            game_id = res.get_json()['game_id']
            res = self.client.get(f'/api/games/{game_id}')
            self.assertEqual(res.get_json()['hintsUsed'], hints)

    def test_completed_flag_persistence(self):
        """Completed flag should persist."""
        state = {'difficulty': 30, 'completed': True}
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']
        res = self.client.get(f'/api/games/{game_id}')
        self.assertTrue(res.get_json()['completed'])

    def test_multiple_fields_update(self):
        """Updating multiple fields at once should preserve all."""
        puzzle, solution = generate_puzzle(difficulty=30)
        state = {
            'puzzle': puzzle,
            'solution': solution,
            'board': copy.deepcopy(puzzle),
            'difficulty': 30,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        self.client.put(f'/api/games/{game_id}', data=json.dumps({
            'elapsed': 250,
            'mistakes': 3,
            'hintsUsed': 2,
            'completed': True,
            'tags': ['test'],
            'notes': 'Done!',
            'rating': 4,
            'favorite': True,
        }), content_type='application/json')

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['elapsed'], 250)
        self.assertEqual(game['mistakes'], 3)
        self.assertEqual(game['hintsUsed'], 2)
        self.assertTrue(game['completed'])
        self.assertIn('test', game['tags'])
        self.assertEqual(game['notes'], 'Done!')
        self.assertEqual(game['rating'], 4)
        self.assertTrue(game['favorite'])
        # Original fields still intact
        self.assertEqual(game['puzzle'], puzzle)
        self.assertEqual(game['solution'], solution)
        self.assertEqual(game['difficulty'], 30)

    def test_solution_validity_after_operations(self):
        """Solution should remain valid after multiple operations."""
        puzzle, solution = generate_puzzle(difficulty=30)
        state = {
            'puzzle': puzzle,
            'solution': solution,
            'board': copy.deepcopy(puzzle),
            'difficulty': 30,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        # Multiple updates
        for i in range(5):
            self.client.put(f'/api/games/{game_id}', data=json.dumps({
                'elapsed': (i + 1) * 50,
                'mistakes': i,
            }), content_type='application/json')

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertFalse(_has_conflicts(game['solution']))
        self.assertEqual(game['solution'], solution)


if __name__ == '__main__':
    unittest.main(verbosity=2)
