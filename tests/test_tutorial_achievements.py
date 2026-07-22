"""
Tests for tutorial achievements system.
Batch 7: Achievements + badges.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestTutorialAchievements(unittest.TestCase):
    """Tests for tutorial achievements endpoint."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()
        self.client.post('/api/login', data=json.dumps({
            'username': 'testuser', 'password': 'password'
        }), content_type='application/json')

    def test_get_achievements(self):
        """GET /api/tutorials/achievements should return achievement list."""
        res = self.client.get('/api/tutorials/achievements')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIsInstance(data['achievements'], list)
        self.assertGreater(len(data['achievements']), 0)

    def test_achievements_have_required_fields(self):
        """Each achievement should have id, title, description, icon, unlocked."""
        res = self.client.get('/api/tutorials/achievements')
        achievements = res.get_json()['achievements']
        for ach in achievements:
            self.assertIn('id', ach)
            self.assertIn('title', ach)
            self.assertIn('description', ach)
            self.assertIn('icon', ach)
            self.assertIn('unlocked', ach)

    def test_new_user_has_no_unlocked_achievements(self):
        """New user should have all achievements locked."""
        res = self.client.get('/api/tutorials/achievements')
        achievements = res.get_json()['achievements']
        unlocked = [a for a in achievements if a['unlocked']]
        self.assertEqual(len(unlocked), 0)

    def test_complete_first_lesson_unlocks_achievement(self):
        """Completing first lesson should unlock 'first_lesson' achievement."""
        self.client.post('/api/tutorials/progress', data=json.dumps({
            'lesson_id': 'rules-of-sudoku',
            'status': 'completed'
        }), content_type='application/json')
        res = self.client.get('/api/tutorials/achievements')
        achievements = res.get_json()['achievements']
        first_lesson = [a for a in achievements if a['id'] == 'first_lesson']
        self.assertEqual(len(first_lesson), 1)
        self.assertTrue(first_lesson[0]['unlocked'])

    def test_complete_all_beginner_unlocks_achievement(self):
        """Completing all beginner lessons should unlock 'beginner_master' achievement."""
        for lesson_id in ['rules-of-sudoku', 'scanning', 'naked-singles', 'hidden-singles']:
            self.client.post('/api/tutorials/progress', data=json.dumps({
                'lesson_id': lesson_id,
                'status': 'completed'
            }), content_type='application/json')
        res = self.client.get('/api/tutorials/achievements')
        achievements = res.get_json()['achievements']
        beginner_master = [a for a in achievements if a['id'] == 'beginner_master']
        self.assertEqual(len(beginner_master), 1)
        self.assertTrue(beginner_master[0]['unlocked'])

    def test_achievements_require_auth(self):
        """Achievements endpoint should require login."""
        self.client.post('/api/logout')
        res = self.client.get('/api/tutorials/achievements')
        self.assertEqual(res.status_code, 401)


if __name__ == '__main__':
    unittest.main(verbosity=2)
