"""
Final regression tests covering all major features.
These serve as a safety net to catch any regressions in the future.
"""
import json
import copy
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module
from sudoku import generate_puzzle, _has_conflicts, _is_valid


class TestRegressionSuite(unittest.TestCase):
    """Final regression tests for all major features."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    # === Core Game Flow ===
    def test_new_game_returns_valid_puzzle(self):
        """New game should return a valid puzzle."""
        res = self.client.get('/api/new-game?difficulty=30')
        data = res.get_json()
        self.assertFalse(_has_conflicts(data['puzzle']))
        self.assertFalse(_has_conflicts(data['solution']))

    def test_create_get_update_delete(self):
        """CRUD operations should work."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30,
        }), content_type='application/json')
        gid = res.get_json()['game_id']
        self.assertEqual(res.status_code, 201)

        # GET
        res = self.client.get(f'/api/games/{gid}')
        self.assertEqual(res.status_code, 200)

        # UPDATE
        res = self.client.put(f'/api/games/{gid}', data=json.dumps({
            'elapsed': 100,
        }), content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # DELETE
        res = self.client.delete(f'/api/games/{gid}')
        self.assertEqual(res.status_code, 200)

        # GET should 404
        res = self.client.get(f'/api/games/{gid}')
        self.assertEqual(res.status_code, 404)

    # === Solver ===
    def test_solve_returns_valid_solution(self):
        """Solver should return a valid solution."""
        puzzle, _ = generate_puzzle(difficulty=30)
        res = self.client.post('/api/solve', data=json.dumps({
            'board': puzzle,
        }), content_type='application/json')
        solved = res.get_json()['solved']
        self.assertFalse(_has_conflicts(solved))

    def test_hint_returns_valid_move(self):
        """Hint should return a valid move."""
        puzzle, solution = generate_puzzle(difficulty=30)
        res = self.client.post('/api/hint', data=json.dumps({
            'board': puzzle,
        }), content_type='application/json')
        hint = res.get_json()
        self.assertEqual(hint['value'], solution[hint['row']][hint['col']])

    def test_validate_detects_conflicts(self):
        """Validate should detect conflicts."""
        puzzle, solution = generate_puzzle(difficulty=30)
        # Insert a conflict
        board = copy.deepcopy(puzzle)
        for r in range(9):
            for c in range(9):
                if board[r][c] != 0:
                    # Find same number in same row
                    for c2 in range(9):
                        if c2 != c and board[r][c2] == 0:
                            board[r][c2] = board[r][c]
                            res = self.client.post('/api/validate', data=json.dumps({
                                'board': board,
                            }), content_type='application/json')
                            self.assertFalse(res.get_json()['valid'])
                            return

    # === Storage ===
    def test_storage_persists_across_requests(self):
        """Storage should persist data across multiple requests."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'elapsed': 100,
        }), content_type='application/json')
        gid = res.get_json()['game_id']

        # Multiple reads should return same data
        for _ in range(5):
            game = self.client.get(f'/api/games/{gid}').get_json()
            self.assertEqual(game['elapsed'], 100)

    def test_delete_all_clears_everything(self):
        """Delete all should clear all games and reset stats."""
        for _ in range(5):
            self.client.post('/api/games', data=json.dumps({
                'difficulty': 30, 'completed': True, 'elapsed': 100,
            }), content_type='application/json')
        self.client.delete('/api/games')
        self.assertEqual(len(self.client.get('/api/games').get_json()['games']), 0)
        self.assertEqual(self.client.get('/api/stats').get_json()['total_games'], 0)

    # === Stats & Analytics ===
    def test_stats_reflect_games(self):
        """Stats should reflect the actual games."""
        self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'completed': True, 'elapsed': 100,
            'mistakes': 2, 'hintsUsed': 1,
        }), content_type='application/json')
        stats = self.client.get('/api/stats').get_json()
        self.assertEqual(stats['total_games'], 1)
        self.assertEqual(stats['completed_games'], 1)
        self.assertEqual(stats['total_mistakes'], 2)
        self.assertEqual(stats['total_hints'], 1)

    def test_profile_aggregates_correctly(self):
        """Profile should aggregate data correctly."""
        for i in range(5):
            self.client.post('/api/games', data=json.dumps({
                'difficulty': 30, 'completed': True, 'elapsed': 100 + i * 10,
                'rating': 3 + i % 3,
            }), content_type='application/json')
        profile = self.client.get('/api/profile').get_json()
        self.assertEqual(profile['total_games'], 5)
        self.assertEqual(profile['completed_games'], 5)
        self.assertEqual(profile['level'], 5)
        self.assertIn('first_win', profile['achievements'])

    # === Game Features ===
    def test_archive_unarchive(self):
        """Archive and unarchive should work."""
        res = self.client.post('/api/games', data=json.dumps({'difficulty': 30}),
                               content_type='application/json')
        gid = res.get_json()['game_id']
        self.client.put(f'/api/games/{gid}/archive', data=json.dumps({'archived': True}),
                        content_type='application/json')
        self.assertTrue(self.client.get(f'/api/games/{gid}').get_json().get('archived'))
        self.client.put(f'/api/games/{gid}/archive', data=json.dumps({'archived': False}),
                        content_type='application/json')
        self.assertFalse(self.client.get(f'/api/games/{gid}').get_json().get('archived'))

    def test_clone_creates_copy(self):
        """Clone should create a copy with reset state."""
        puzzle, solution = generate_puzzle(difficulty=30)
        res = self.client.post('/api/games', data=json.dumps({
            'puzzle': puzzle, 'solution': solution,
            'board': solution, 'difficulty': 30,
            'completed': True, 'elapsed': 100,
        }), content_type='application/json')
        gid = res.get_json()['game_id']
        clone_res = self.client.post(f'/api/games/{gid}/clone')
        clone_id = clone_res.get_json()['game_id']
        clone = self.client.get(f'/api/games/{clone_id}').get_json()
        self.assertFalse(clone.get('completed', False))
        self.assertEqual(clone.get('elapsed', 0), 0)

    def test_export_import_roundtrip(self):
        """Export then import should preserve data."""
        puzzle, solution = generate_puzzle(difficulty=30)
        res = self.client.post('/api/games', data=json.dumps({
            'puzzle': puzzle, 'solution': solution,
            'board': solution, 'difficulty': 30,
            'completed': True, 'elapsed': 100,
        }), content_type='application/json')
        gid = res.get_json()['game_id']
        export = self.client.get(f'/api/games/{gid}/export')
        import_res = self.client.post('/api/games/import', data=json.dumps({
            'share_code': export.get_json()['share_code'],
        }), content_type='application/json')
        imported = self.client.get(f'/api/games/{import_res.get_json()["game_id"]}').get_json()
        self.assertEqual(imported['difficulty'], 30)
        self.assertTrue(imported['completed'])

    def test_certificate_for_completed_game(self):
        """Certificate should work for completed games."""
        puzzle, solution = generate_puzzle(difficulty=30)
        res = self.client.post('/api/games', data=json.dumps({
            'puzzle': puzzle, 'solution': solution,
            'board': solution, 'difficulty': 30,
            'completed': True, 'elapsed': 100,
        }), content_type='application/json')
        cert = self.client.get(f'/api/games/{res.get_json()["game_id"]}/certificate').get_json()
        self.assertTrue(cert['completed'])
        self.assertIn(cert['performance'], ['perfect', 'excellent', 'good', 'completed'])

    # === Error Handling ===
    def test_404_returns_json_error(self):
        """404 should return JSON with error field."""
        res = self.client.get('/api/games/nonexistent')
        self.assertEqual(res.status_code, 404)
        self.assertIn('error', res.get_json())

    def test_invalid_json_returns_400(self):
        """Invalid JSON should return 400."""
        res = self.client.post('/api/games', data='invalid',
                               content_type='application/json')
        self.assertEqual(res.status_code, 400)


if __name__ == '__main__':
    unittest.main(verbosity=2)
