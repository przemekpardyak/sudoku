"""
Tests for game lifecycle with all new features.
Comprehensive end-to-end tests covering the full game flow with
tags, ratings, notes, achievements, and session tracking.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module
from sudoku import generate_puzzle


class TestFullLifecycle(unittest.TestCase):
    """End-to-end tests covering the full game lifecycle with all features."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_full_game_lifecycle_with_all_features(self):
        """Test the complete lifecycle: create → play → rate → archive."""
        puzzle, solution = generate_puzzle(difficulty=30)

        # 1. Create game
        res = self.client.post('/api/games', data=json.dumps({
            'puzzle': puzzle,
            'solution': solution,
            'board': puzzle,
            'difficulty': 30,
            'session_start': '2026-07-21T10:00:00Z',
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        # 2. Play — fill in some cells
        board = [row[:] for row in puzzle]
        filled = 0
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0 and filled < 5:
                    board[r][c] = solution[r][c]
                    filled += 1
        self.client.put(f'/api/games/{game_id}', data=json.dumps({
            'board': board,
            'elapsed': 45,
            'mistakes': 1,
            'hintsUsed': 1,
        }), content_type='application/json')

        # 3. Complete the game
        self.client.put(f'/api/games/{game_id}', data=json.dumps({
            'board': solution,
            'completed': True,
            'elapsed': 120,
            'session_end': '2026-07-21T10:02:00Z',
        }), content_type='application/json')

        # 4. Rate it
        self.client.put(f'/api/games/{game_id}/rate', data=json.dumps({
            'rating': 4,
        }), content_type='application/json')

        # 5. Add notes and tags
        self.client.put(f'/api/games/{game_id}', data=json.dumps({
            'notes': 'Good game!',
            'tags': ['favorite', 'easy'],
        }), content_type='application/json')

        # 6. Archive it
        self.client.put(f'/api/games/{game_id}/archive', data=json.dumps({
            'archived': True,
        }), content_type='application/json')

        # 7. Verify game state
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertTrue(game['completed'])
        self.assertEqual(game['elapsed'], 120)
        self.assertEqual(game['rating'], 4)
        self.assertEqual(game['notes'], 'Good game!')
        self.assertIn('favorite', game['tags'])
        self.assertTrue(game['archived'])
        self.assertEqual(game['session_start'], '2026-07-21T10:00:00Z')
        self.assertEqual(game['session_end'], '2026-07-21T10:02:00Z')

        # 8. Verify in list
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        game_in_list = [g for g in games if g['game_id'] == game_id][0]
        self.assertTrue(game_in_list['completed'])
        self.assertEqual(game_in_list['rating'], 4)
        self.assertTrue(game_in_list['archived'])

        # 9. Verify stats include achievements
        res = self.client.get('/api/stats')
        stats = res.get_json()
        self.assertIn('first_win', stats['achievements'])
        self.assertIn('avg_rating', stats)
        self.assertEqual(stats['avg_rating'], 4.0)

    def test_clone_then_complete_then_rate(self):
        """Clone a game, complete the clone, then rate it."""
        puzzle, solution = generate_puzzle(difficulty=40)

        # Create original game
        res = self.client.post('/api/games', data=json.dumps({
            'puzzle': puzzle,
            'solution': solution,
            'board': solution,  # Already solved
            'difficulty': 40,
            'completed': True,
            'elapsed': 300,
        }), content_type='application/json')
        original_id = res.get_json()['game_id']

        # Clone it
        res = self.client.post(f'/api/games/{original_id}/clone')
        clone_id = res.get_json()['game_id']

        # Clone should be fresh
        res = self.client.get(f'/api/games/{clone_id}')
        clone = res.get_json()
        self.assertFalse(clone['completed'])
        self.assertEqual(clone['elapsed'], 0)
        self.assertIn('cloned', clone['tags'])

        # Complete the clone
        self.client.put(f'/api/games/{clone_id}', data=json.dumps({
            'board': solution,
            'completed': True,
            'elapsed': 150,
            'mistakes': 2,
        }), content_type='application/json')

        # Rate the clone
        res = self.client.put(f'/api/games/{clone_id}/rate', data=json.dumps({
            'rating': 5,
        }), content_type='application/json')
        self.assertEqual(res.status_code, 200)

    def test_export_import_with_all_fields(self):
        """Export a game with all fields, import it, verify data preserved."""
        puzzle, solution = generate_puzzle(difficulty=30)

        # Create game with all fields
        res = self.client.post('/api/games', data=json.dumps({
            'puzzle': puzzle,
            'solution': solution,
            'board': solution,
            'difficulty': 30,
            'completed': True,
            'elapsed': 100,
            'mistakes': 1,
            'hintsUsed': 2,
            'tags': ['test', 'export'],
            'notes': 'Export test',
            'rating': 4,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        # Export
        res = self.client.get(f'/api/games/{game_id}/export')
        share_code = res.get_json()['share_code']

        # Import
        res = self.client.post('/api/games/import', data=json.dumps({
            'share_code': share_code,
        }), content_type='application/json')
        imported_id = res.get_json()['game_id']

        # Verify
        res = self.client.get(f'/api/games/{imported_id}')
        imported = res.get_json()
        self.assertTrue(imported['completed'])
        self.assertEqual(imported['elapsed'], 100)
        self.assertEqual(imported['mistakes'], 1)
        self.assertEqual(imported['hintsUsed'], 2)
        self.assertIn('test', imported['tags'])
        self.assertEqual(imported['notes'], 'Export test')
        self.assertEqual(imported['rating'], 4)

    def test_multiple_games_achievements_progression(self):
        """Play multiple games and watch achievements unlock."""
        for i in range(3):
            self.client.post('/api/games', data=json.dumps({
                'difficulty': 30,
                'completed': True,
                'elapsed': 50 + i * 10,
                'mistakes': 0,
                'hintsUsed': 0,
            }), content_type='application/json')

        res = self.client.get('/api/stats')
        stats = res.get_json()
        self.assertIn('first_win', stats['achievements'])
        self.assertIn('perfect_game', stats['achievements'])
        self.assertIn('speed_run', stats['achievements'])
        self.assertIn('no_hints', stats['achievements'])
        self.assertEqual(stats['completed_games'], 3)

    def test_validate_solve_hint_chain(self):
        """Validate → hint → solve chain on the same board."""
        puzzle, solution = generate_puzzle(difficulty=30)

        # Validate the puzzle
        res = self.client.post('/api/validate', data=json.dumps({
            'board': puzzle,
        }), content_type='application/json')
        self.assertTrue(res.get_json()['valid'])

        # Get a hint
        res = self.client.post('/api/hint', data=json.dumps({
            'board': puzzle,
        }), content_type='application/json')
        hint = res.get_json()
        self.assertEqual(hint['value'], solution[hint['row']][hint['col']])

        # Apply the hint
        board = [row[:] for row in puzzle]
        board[hint['row']][hint['col']] = hint['value']

        # Solve the board
        res = self.client.post('/api/solve', data=json.dumps({
            'board': board,
        }), content_type='application/json')
        solved = res.get_json()['solved']

        # Solved board should match solution
        self.assertEqual(solved, solution)


if __name__ == '__main__':
    unittest.main(verbosity=2)
