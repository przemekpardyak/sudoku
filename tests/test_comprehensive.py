"""
Comprehensive integration test exercising all endpoints in sequence.
This is the ultimate end-to-end test that covers the entire API surface.
"""
import json
import copy
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module
from sudoku import generate_puzzle, _has_conflicts


class TestComprehensiveIntegration(unittest.TestCase):
    """Comprehensive integration test covering all endpoints."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_full_player_journey(self):
        """Complete player journey from first game to expert."""
        # 1. Check empty profile
        res = self.client.get('/api/profile')
        self.assertEqual(res.get_json()['total_games'], 0)

        # 2. Get a new game
        res = self.client.get('/api/new-game?difficulty=20')
        puzzle_data = res.get_json()
        puzzle = puzzle_data['puzzle']
        solution = puzzle_data['solution']

        # 3. Analyze the puzzle
        res = self.client.post('/api/analyze', data=json.dumps({
            'puzzle': puzzle,
        }), content_type='application/json')
        analysis = res.get_json()
        self.assertFalse(analysis['has_conflicts'])
        self.assertTrue(analysis['unique_solution'])

        # 4. Create the game
        res = self.client.post('/api/games', data=json.dumps({
            'puzzle': puzzle,
            'solution': solution,
            'board': copy.deepcopy(puzzle),
            'difficulty': 20,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']
        self.assertEqual(res.status_code, 201)

        # 5. Check progress (should be 0%)
        res = self.client.get(f'/api/games/{game_id}/progress')
        self.assertEqual(res.get_json()['progress_pct'], 0)

        # 6. Get a hint
        res = self.client.post('/api/hint', data=json.dumps({
            'board': puzzle,
        }), content_type='application/json')
        hint = res.get_json()
        self.assertEqual(hint['value'], solution[hint['row']][hint['col']])

        # 7. Apply the hint and fill more cells
        board = copy.deepcopy(puzzle)
        board[hint['row']][hint['col']] = hint['value']
        # Fill 5 more cells
        count = 0
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0 and count < 5:
                    board[r][c] = solution[r][c]
                    count += 1

        # 8. Save progress
        self.client.put(f'/api/games/{game_id}', data=json.dumps({
            'board': board,
            'elapsed': 45,
            'hintsUsed': 1,
            'mistakes': 0,
        }), content_type='application/json')

        # 9. Check progress again
        res = self.client.get(f'/api/games/{game_id}/progress')
        self.assertGreater(res.get_json()['progress_pct'], 0)

        # 10. Validate the board
        res = self.client.post('/api/validate', data=json.dumps({
            'board': board,
        }), content_type='application/json')
        self.assertTrue(res.get_json()['valid'])

        # 11. Complete the game
        self.client.put(f'/api/games/{game_id}', data=json.dumps({
            'board': solution,
            'completed': True,
            'elapsed': 90,
            'session_end': '2026-07-21T10:02:00Z',
        }), content_type='application/json')

        # 12. Check progress is 100%
        res = self.client.get(f'/api/games/{game_id}/progress')
        self.assertEqual(res.get_json()['progress_pct'], 100)

        # 13. Rate the game
        self.client.put(f'/api/games/{game_id}/rate', data=json.dumps({
            'rating': 5,
        }), content_type='application/json')

        # 14. Add tags and notes
        self.client.put(f'/api/games/{game_id}', data=json.dumps({
            'tags': ['first-game', 'great'],
            'notes': 'My first completed game!',
            'favorite': True,
        }), content_type='application/json')

        # 15. Get certificate
        res = self.client.get(f'/api/games/{game_id}/certificate')
        cert = res.get_json()
        self.assertTrue(cert['completed'])
        self.assertIn(cert['performance'], ['perfect', 'excellent', 'good', 'completed'])

        # 16. Export the game
        res = self.client.get(f'/api/games/{game_id}/export')
        share_code = res.get_json()['share_code']

        # 17. Import as a new game
        res = self.client.post('/api/games/import', data=json.dumps({
            'share_code': share_code,
        }), content_type='application/json')
        imported_id = res.get_json()['game_id']
        self.assertNotEqual(imported_id, game_id)

        # 18. Clone the original game
        res = self.client.post(f'/api/games/{game_id}/clone')
        clone_id = res.get_json()['game_id']
        self.assertNotEqual(clone_id, game_id)

        # 19. Archive the clone
        self.client.put(f'/api/games/{clone_id}/archive', data=json.dumps({
            'archived': True,
        }), content_type='application/json')

        # 20. Check stats
        res = self.client.get('/api/stats')
        stats = res.get_json()
        self.assertEqual(stats['total_games'], 3)  # original + imported + clone
        self.assertEqual(stats['completed_games'], 2)  # original + imported

        # 21. Check achievements
        self.assertIn('first_win', stats['achievements'])

        # 22. Check leaderboard
        res = self.client.get('/api/leaderboard')
        self.assertGreater(res.get_json()['count'], 0)

        # 23. Check streaks
        res = self.client.get('/api/streaks')
        self.assertGreater(res.get_json()['best_streak'], 0)

        # 24. Check history
        res = self.client.get('/api/history')
        self.assertEqual(res.get_json()['count'], 3)

        # 25. Check profile
        res = self.client.get('/api/profile')
        profile = res.get_json()
        self.assertEqual(profile['total_games'], 3)
        self.assertGreater(profile['level'], 0)
        self.assertIn('recommended_difficulty', profile)

        # 26. Check recommendation
        res = self.client.get('/api/recommend-difficulty')
        self.assertIn('recommended_difficulty', res.get_json())

        # 27. Get daily puzzle
        res = self.client.get('/api/daily-puzzle')
        self.assertIn('puzzle', res.get_json())

        # 28. Get weekly puzzle
        res = self.client.get('/api/weekly-puzzle')
        self.assertIn('puzzle', res.get_json())

        # 29. Compare two games
        res = self.client.get(f'/api/games/compare?a={game_id}&b={imported_id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn('differences', res.get_json())

        # 30. Export stats
        res = self.client.get('/api/stats/export')
        self.assertIn('summary', res.get_json())

        # 31. Delete one game
        self.client.delete(f'/api/games/{clone_id}')
        res = self.client.get('/api/games')
        self.assertEqual(len(res.get_json()['games']), 2)

        # 32. Delete all
        self.client.delete('/api/games')
        res = self.client.get('/api/games')
        self.assertEqual(len(res.get_json()['games']), 0)

        # 33. Verify everything reset
        res = self.client.get('/api/profile')
        self.assertEqual(res.get_json()['total_games'], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
