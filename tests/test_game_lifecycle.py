"""
Comprehensive integration tests for the full game lifecycle.
Tests the complete flow: create → play → save → complete → stats → export → import.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module
from sudoku import generate_puzzle


class TestGameLifecycle(unittest.TestCase):
    """End-to-end integration tests for the full game lifecycle."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_full_game_lifecycle(self):
        """Test the complete lifecycle: new game → save → update → complete → stats."""
        # 1. Generate a new puzzle
        res = self.client.get('/api/new-game?difficulty=30')
        self.assertEqual(res.status_code, 200)
        puzzle_data = res.get_json()
        puzzle = puzzle_data['puzzle']
        solution = puzzle_data['solution']

        # 2. Create a game with this puzzle
        state = {
            'puzzle': puzzle,
            'solution': solution,
            'board': [row[:] for row in puzzle],
            'given': [[puzzle[r][c] != 0 for c in range(9)] for r in range(9)],
            'difficulty': 30,
            'elapsed': 0,
            'mistakes': 0,
            'completed': False,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        self.assertEqual(res.status_code, 201)
        game_id = res.get_json()['game_id']

        # 3. Simulate playing — fill in some cells
        board = [row[:] for row in puzzle]
        filled = 0
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0 and filled < 5:
                    board[r][c] = solution[r][c]
                    filled += 1

        self.client.put(f'/api/games/{game_id}', data=json.dumps({
            'board': board, 'elapsed': 30, 'mistakes': 1
        }), content_type='application/json')

        # 4. Verify game was saved
        res = self.client.get(f'/api/games/{game_id}')
        saved = res.get_json()
        self.assertEqual(saved['elapsed'], 30)
        self.assertEqual(saved['mistakes'], 1)

        # 5. Complete the game
        self.client.put(f'/api/games/{game_id}', data=json.dumps({
            'board': solution, 'elapsed': 120, 'mistakes': 1, 'completed': True
        }), content_type='application/json')

        # 6. Check stats reflect the completed game
        res = self.client.get('/api/stats')
        stats = res.get_json()
        self.assertEqual(stats['total_games'], 1)
        self.assertEqual(stats['completed_games'], 1)
        self.assertEqual(stats['total_mistakes'], 1)

        # 7. Check best times
        res = self.client.get('/api/best-times')
        best_times = res.get_json()
        self.assertIn('30', best_times)
        self.assertEqual(best_times['30'], 120)

    def test_export_import_roundtrip(self):
        """Export a game and import it — should have the same state."""
        state = {
            'puzzle': [[5] * 9] * 9,
            'board': [[5, 0, 0, 0, 0, 0, 0, 0, 0]] * 9,
            'difficulty': 30,
            'elapsed': 50,
            'mistakes': 2,
            'completed': False,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        # Export
        res = self.client.get(f'/api/games/{game_id}/export')
        share_code = res.get_json()['share_code']

        # Import
        res = self.client.post('/api/games/import',
                              data=json.dumps({'share_code': share_code}),
                              content_type='application/json')
        new_id = res.get_json()['game_id']
        self.assertNotEqual(game_id, new_id)

        # Verify imported state
        res = self.client.get(f'/api/games/{new_id}')
        imported = res.get_json()
        self.assertEqual(imported['elapsed'], 50)
        self.assertEqual(imported['mistakes'], 2)

    def test_validate_during_gameplay(self):
        """Validate board state during gameplay."""
        puzzle, solution = generate_puzzle(difficulty=30)

        # Validate the initial puzzle (should be valid, not complete)
        res = self.client.post('/api/validate',
                              data=json.dumps({'board': puzzle}),
                              content_type='application/json')
        data = res.get_json()
        self.assertTrue(data['valid'])
        self.assertFalse(data['complete'])

        # Validate the solution (should be valid and complete)
        res = self.client.post('/api/validate',
                              data=json.dumps({'board': solution}),
                              content_type='application/json')
        data = res.get_json()
        self.assertTrue(data['valid'])
        self.assertTrue(data['complete'])

    def test_multiple_games_stats(self):
        """Stats should aggregate across multiple games."""
        # Create 3 games, complete 2
        for i in range(3):
            state = {
                'puzzle': [[5] * 9] * 9,
                'board': [[5] * 9] * 9,
                'difficulty': 40,
                'elapsed': 100 + i * 50,
                'mistakes': i,
                'completed': i < 2,
            }
            self.client.post('/api/games', data=json.dumps(state),
                            content_type='application/json')

        res = self.client.get('/api/stats')
        stats = res.get_json()
        self.assertEqual(stats['total_games'], 3)
        self.assertEqual(stats['completed_games'], 2)
        self.assertEqual(stats['total_mistakes'], 3)  # 0 + 1 + 2
        self.assertEqual(stats['best_time'], 100)  # fastest completed

    def test_delete_and_recreate(self):
        """Delete a game and verify it's gone, then create a new one."""
        state = {'difficulty': 40, 'elapsed': 50}
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        # Delete
        res = self.client.delete(f'/api/games/{game_id}')
        self.assertEqual(res.status_code, 200)

        # Verify deleted
        res = self.client.get(f'/api/games/{game_id}')
        self.assertEqual(res.status_code, 404)

        # Create new game
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        new_id = res.get_json()['game_id']
        self.assertNotEqual(game_id, new_id)


if __name__ == '__main__':
    unittest.main(verbosity=2)
