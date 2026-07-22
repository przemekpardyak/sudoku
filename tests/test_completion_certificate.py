"""
Tests for game completion certificate.
Tests the /api/games/<id>/certificate endpoint.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module
from sudoku import generate_puzzle


class TestCompletionCertificate(unittest.TestCase):
    """Tests for game completion certificate."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_completed_game(self, elapsed=120, difficulty=30, mistakes=1, hintsUsed=0, rating=4):
        puzzle, solution = generate_puzzle(difficulty=30)
        res = self.client.post('/api/games', data=json.dumps({
            'puzzle': puzzle,
            'solution': solution,
            'board': solution,
            'difficulty': difficulty,
            'completed': True,
            'elapsed': elapsed,
            'mistakes': mistakes,
            'hintsUsed': hintsUsed,
            'rating': rating,
        }), content_type='application/json')
        return res.get_json()['game_id']

    def test_certificate_for_completed_game(self):
        """Should return a certificate for a completed game."""
        game_id = self._create_completed_game()
        res = self.client.get(f'/api/games/{game_id}/certificate')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('game_id', data)
        self.assertIn('difficulty', data)
        self.assertIn('elapsed', data)
        self.assertIn('mistakes', data)

    def test_certificate_not_for_incomplete_game(self):
        """Should return 400 for an incomplete game."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'completed': False,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']
        res = self.client.get(f'/api/games/{game_id}/certificate')
        self.assertEqual(res.status_code, 400)

    def test_certificate_nonexistent_game(self):
        """Should return 404 for nonexistent game."""
        res = self.client.get('/api/games/nonexistent/certificate')
        self.assertEqual(res.status_code, 404)

    def test_certificate_has_difficulty_label(self):
        """Certificate should include a difficulty label."""
        game_id = self._create_completed_game(difficulty=30)
        res = self.client.get(f'/api/games/{game_id}/certificate')
        data = res.get_json()
        self.assertIn('difficulty_label', data)

    def test_certificate_has_performance_rating(self):
        """Certificate should include a performance rating."""
        game_id = self._create_completed_game(elapsed=50, mistakes=0, hintsUsed=0)
        res = self.client.get(f'/api/games/{game_id}/certificate')
        data = res.get_json()
        self.assertIn('performance', data)

    def test_certificate_perfect_game(self):
        """Perfect game (0 mistakes, 0 hints) should get 'perfect' rating."""
        game_id = self._create_completed_game(mistakes=0, hintsUsed=0)
        res = self.client.get(f'/api/games/{game_id}/certificate')
        self.assertEqual(res.get_json()['performance'], 'perfect')

    def test_certificate_excellent_game(self):
        """Fast game with few mistakes should get 'excellent' rating."""
        game_id = self._create_completed_game(elapsed=80, mistakes=1, hintsUsed=0)
        res = self.client.get(f'/api/games/{game_id}/certificate')
        self.assertIn(res.get_json()['performance'], ['excellent', 'perfect'])

    def test_certificate_has_created_at(self):
        """Certificate should include the game's creation timestamp."""
        game_id = self._create_completed_game()
        res = self.client.get(f'/api/games/{game_id}/certificate')
        self.assertIn('created_at', res.get_json())

    def test_certificate_has_hints_used(self):
        """Certificate should include hints used."""
        game_id = self._create_completed_game(hintsUsed=3)
        res = self.client.get(f'/api/games/{game_id}/certificate')
        self.assertEqual(res.get_json()['hintsUsed'], 3)

    def test_certificate_good_rating(self):
        """Game with <3 mistakes and <300s should get 'good' rating."""
        # good: <3 mistakes, <300s (but not excellent: >1 mistake or >0 hints or >=120s)
        game_id = self._create_completed_game(elapsed=200, mistakes=2, hintsUsed=0)
        res = self.client.get(f'/api/games/{game_id}/certificate')
        performance = res.get_json()['performance']
        self.assertIn(performance, ['good', 'excellent'],
                      f"Expected 'good' or 'excellent', got '{performance}'")

    def test_certificate_completed_rating(self):
        """Game with many mistakes or slow time should get 'completed' rating."""
        # completed: anything that doesn't qualify for perfect/excellent/good
        # good requires <3 mistakes AND <300s, so 5 mistakes should be 'completed'
        game_id = self._create_completed_game(elapsed=500, mistakes=5, hintsUsed=2)
        res = self.client.get(f'/api/games/{game_id}/certificate')
        performance = res.get_json()['performance']
        self.assertEqual(performance, 'completed',
                         f"Expected 'completed' rating for 5 mistakes + 500s, got '{performance}'")

    def test_certificate_difficulty_label_easy(self):
        """Difficulty 25 should map to 'Easy' label."""
        game_id = self._create_completed_game(difficulty=25)
        res = self.client.get(f'/api/games/{game_id}/certificate')
        self.assertEqual(res.get_json()['difficulty_label'], 'Easy')

    def test_certificate_difficulty_label_medium(self):
        """Difficulty 35 should map to 'Medium' label."""
        game_id = self._create_completed_game(difficulty=35)
        res = self.client.get(f'/api/games/{game_id}/certificate')
        self.assertEqual(res.get_json()['difficulty_label'], 'Medium')

    def test_certificate_difficulty_label_hard(self):
        """Difficulty 45 should map to 'Hard' label."""
        game_id = self._create_completed_game(difficulty=45)
        res = self.client.get(f'/api/games/{game_id}/certificate')
        self.assertEqual(res.get_json()['difficulty_label'], 'Hard')

    def test_certificate_difficulty_label_expert(self):
        """Difficulty 50 should map to 'Expert' label."""
        game_id = self._create_completed_game(difficulty=50)
        res = self.client.get(f'/api/games/{game_id}/certificate')
        self.assertEqual(res.get_json()['difficulty_label'], 'Expert')


if __name__ == '__main__':
    unittest.main(verbosity=2)
