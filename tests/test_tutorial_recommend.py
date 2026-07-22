"""
Tests for tutorial recommendation endpoint.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestTutorialRecommendation(unittest.TestCase):
    """Tests for the tutorial recommendation endpoint."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()
        self.client.post('/api/login', data=json.dumps({
            'username': 'testuser', 'password': 'password'
        }), content_type='application/json')

    def test_get_recommendation_new_user(self):
        """New user should be recommended the first lesson."""
        res = self.client.get('/api/tutorials/recommend')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('lesson_id', data)
        self.assertIn('reason', data)
        self.assertEqual(data['lesson_id'], 'rules-of-sudoku')

    def test_get_recommendation_after_first_lesson(self):
        """After completing first lesson, recommend the second."""
        self.client.post('/api/tutorials/progress', data=json.dumps({
            'lesson_id': 'rules-of-sudoku',
            'status': 'completed'
        }), content_type='application/json')
        res = self.client.get('/api/tutorials/recommend')
        data = res.get_json()
        self.assertEqual(data['lesson_id'], 'scanning')

    def test_recommendation_requires_auth(self):
        """Recommendation endpoint should require login."""
        self.client.post('/api/logout')
        res = self.client.get('/api/tutorials/recommend')
        self.assertEqual(res.status_code, 401)

    def test_recommendation_all_beginner_done(self):
        """After all beginner lessons, recommend first intermediate."""
        for lesson_id in ['rules-of-sudoku', 'scanning', 'naked-singles', 'hidden-singles']:
            self.client.post('/api/tutorials/progress', data=json.dumps({
                'lesson_id': lesson_id,
                'status': 'completed'
            }), content_type='application/json')
        res = self.client.get('/api/tutorials/recommend')
        data = res.get_json()
        self.assertEqual(data['lesson_id'], 'naked-pairs')

    def test_recommendation_all_done(self):
        """When all lessons complete, return completion message."""
        # Complete ALL lessons
        all_ids = [
            'rules-of-sudoku', 'scanning', 'naked-singles', 'hidden-singles',
            'naked-pairs', 'hidden-pairs', 'pointing-pairs',
            'x-wing', 'swordfish', 'xy-wing',
            'unique-rectangle', 'coloring', 'als'
        ]
        for lesson_id in all_ids:
            self.client.post('/api/tutorials/progress', data=json.dumps({
                'lesson_id': lesson_id,
                'status': 'completed'
            }), content_type='application/json')
        res = self.client.get('/api/tutorials/recommend')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('lesson_id', data)
        self.assertIsNone(data['lesson_id'])
        self.assertIn('reason', data)


if __name__ == '__main__':
    unittest.main(verbosity=2)
