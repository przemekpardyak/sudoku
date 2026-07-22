"""
Tests for tutorial technique tips API.
Batch 4: In-game contextual help.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestTechniqueTips(unittest.TestCase):
    """Tests for the technique tips endpoint."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_get_technique_tips(self):
        """GET /api/tutorials/tips should return technique tips."""
        res = self.client.get('/api/tutorials/tips')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIsInstance(data['tips'], list)
        self.assertGreater(len(data['tips']), 0)

    def test_tips_have_required_fields(self):
        """Each tip should have technique, title, description, level."""
        res = self.client.get('/api/tutorials/tips')
        tips = res.get_json()['tips']
        for tip in tips:
            self.assertIn('technique', tip)
            self.assertIn('title', tip)
            self.assertIn('description', tip)
            self.assertIn('level', tip)

    def test_tips_cover_all_levels(self):
        """Tips should cover all skill levels."""
        res = self.client.get('/api/tutorials/tips')
        tips = res.get_json()['tips']
        levels = {tip['level'] for tip in tips}
        self.assertIn('beginner', levels)
        self.assertIn('intermediate', levels)
        self.assertIn('advanced', levels)

    def test_get_tips_by_level(self):
        """GET /api/tutorials/tips?level=beginner should filter tips."""
        res = self.client.get('/api/tutorials/tips?level=beginner')
        self.assertEqual(res.status_code, 200)
        tips = res.get_json()['tips']
        for tip in tips:
            self.assertEqual(tip['level'], 'beginner')

    def test_get_technique_detail(self):
        """GET /api/tutorials/techniques/<id> should return technique detail."""
        res = self.client.get('/api/tutorials/techniques/naked-singles')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('technique', data)
        self.assertIn('title', data)
        self.assertIn('description', data)
        self.assertIn('how_to_find', data)

    def test_nonexistent_technique_returns_404(self):
        """GET /api/tutorials/techniques/nonexistent should return 404."""
        res = self.client.get('/api/tutorials/techniques/nonexistent')
        self.assertEqual(res.status_code, 404)


class TestTutorialStats(unittest.TestCase):
    """Tests for tutorial statistics endpoint."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()
        self.client.post('/api/login', data=json.dumps({
            'username': 'testuser', 'password': 'password'
        }), content_type='application/json')

    def test_get_tutorial_stats(self):
        """GET /api/tutorials/stats should return tutorial statistics."""
        res = self.client.get('/api/tutorials/stats')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('total_lessons', data)
        self.assertIn('completed_lessons', data)
        self.assertIn('completion_rate', data)
        self.assertIn('level_progress', data)

    def test_stats_reflect_progress(self):
        """Stats should reflect completed lessons."""
        # Complete a lesson
        self.client.post('/api/tutorials/progress', data=json.dumps({
            'lesson_id': 'rules-of-sudoku',
            'status': 'completed'
        }), content_type='application/json')
        res = self.client.get('/api/tutorials/stats')
        data = res.get_json()
        self.assertGreaterEqual(data['completed_lessons'], 1)

    def test_stats_require_auth(self):
        """Stats endpoint should require login."""
        self.client.post('/api/logout')
        res = self.client.get('/api/tutorials/stats')
        self.assertEqual(res.status_code, 401)


if __name__ == '__main__':
    unittest.main(verbosity=2)
