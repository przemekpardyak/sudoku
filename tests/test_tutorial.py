"""
Tests for the tutorial system.
Batch 1: Tutorial framework + first beginner lesson.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestTutorialContent(unittest.TestCase):
    """Tests for tutorial content structure and API."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_get_tutorial_lessons(self):
        """GET /api/tutorials/lessons should return list of lessons."""
        res = self.client.get('/api/tutorials/lessons')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIsInstance(data['lessons'], list)
        self.assertGreater(len(data['lessons']), 0)

    def test_lessons_have_required_fields(self):
        """Each lesson should have id, title, level, description, order."""
        res = self.client.get('/api/tutorials/lessons')
        lessons = res.get_json()['lessons']
        for lesson in lessons:
            self.assertIn('id', lesson)
            self.assertIn('title', lesson)
            self.assertIn('level', lesson)
            self.assertIn('description', lesson)
            self.assertIn('order', lesson)

    def test_lessons_ordered_by_order_field(self):
        """Lessons should be returned in order."""
        res = self.client.get('/api/tutorials/lessons')
        lessons = res.get_json()['lessons']
        orders = [l['order'] for l in lessons]
        self.assertEqual(orders, sorted(orders))

    def test_lessons_have_levels(self):
        """Lessons should have valid skill levels."""
        res = self.client.get('/api/tutorials/lessons')
        lessons = res.get_json()['lessons']
        valid_levels = {'beginner', 'intermediate', 'advanced', 'expert'}
        for lesson in lessons:
            self.assertIn(lesson['level'], valid_levels)

    def test_get_single_lesson(self):
        """GET /api/tutorials/lessons/<id> should return lesson detail."""
        res = self.client.get('/api/tutorials/lessons')
        first_lesson_id = res.get_json()['lessons'][0]['id']
        res = self.client.get(f'/api/tutorials/lessons/{first_lesson_id}')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('id', data)
        self.assertIn('title', data)
        self.assertIn('steps', data)
        self.assertIsInstance(data['steps'], list)
        self.assertGreater(len(data['steps']), 0)

    def test_lesson_steps_have_required_fields(self):
        """Each step should have title, description, and type."""
        res = self.client.get('/api/tutorials/lessons')
        first_lesson_id = res.get_json()['lessons'][0]['id']
        res = self.client.get(f'/api/tutorials/lessons/{first_lesson_id}')
        steps = res.get_json()['steps']
        for step in steps:
            self.assertIn('title', step)
            self.assertIn('description', step)
            self.assertIn('type', step)

    def test_nonexistent_lesson_returns_404(self):
        """GET /api/tutorials/lessons/nonexistent should return 404."""
        res = self.client.get('/api/tutorials/lessons/nonexistent')
        self.assertEqual(res.status_code, 404)


class TestTutorialProgress(unittest.TestCase):
    """Tests for tutorial progress tracking."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()
        # Login as testuser
        self.client.post('/api/login', data=json.dumps({
            'username': 'testuser', 'password': 'password'
        }), content_type='application/json')

    def test_get_progress_empty(self):
        """GET /api/tutorials/progress should return empty for new user."""
        res = self.client.get('/api/tutorials/progress')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['completed_lessons'], [])
        self.assertEqual(data['completed_steps'], [])

    def test_mark_lesson_complete(self):
        """POST /api/tutorials/progress should mark lesson as complete."""
        res = self.client.post('/api/tutorials/progress', data=json.dumps({
            'lesson_id': 'rules-of-sudoku',
            'status': 'completed'
        }), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        # Verify it persists
        res = self.client.get('/api/tutorials/progress')
        self.assertIn('rules-of-sudoku', res.get_json()['completed_lessons'])

    def test_mark_step_complete(self):
        """POST /api/tutorials/progress should mark individual steps."""
        res = self.client.post('/api/tutorials/progress', data=json.dumps({
            'lesson_id': 'rules-of-sudoku',
            'step_index': 0,
            'status': 'completed'
        }), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        res = self.client.get('/api/tutorials/progress')
        self.assertIn('rules-of-sudoku:0', res.get_json()['completed_steps'])

    def test_progress_requires_auth(self):
        """Progress endpoint should require login."""
        self.client.post('/api/logout')
        res = self.client.get('/api/tutorials/progress')
        self.assertEqual(res.status_code, 401)


if __name__ == '__main__':
    unittest.main(verbosity=2)
