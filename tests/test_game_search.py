"""
Tests for game search/filtering functionality.
Tests filtering games by multiple criteria.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestGameSearch(unittest.TestCase):
    """Tests for game search and filtering."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_game(self, difficulty=40, completed=False, tags=None, elapsed=100):
        state = {
            'difficulty': difficulty,
            'elapsed': elapsed,
            'completed': completed,
            'mistakes': 0,
        }
        if tags:
            state['tags'] = tags
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        return res.get_json()['game_id']

    def test_filter_by_difficulty(self):
        """Can filter games by difficulty level via list endpoint."""
        self._create_game(difficulty=30)
        self._create_game(difficulty=40)
        self._create_game(difficulty=50)
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        easy = [g for g in games if g['difficulty'] == 30]
        medium = [g for g in games if g['difficulty'] == 40]
        hard = [g for g in games if g['difficulty'] == 50]
        self.assertEqual(len(easy), 1)
        self.assertEqual(len(medium), 1)
        self.assertEqual(len(hard), 1)

    def test_filter_completed(self):
        """Can separate completed from in-progress games."""
        self._create_game(completed=True)
        self._create_game(completed=False)
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        completed = [g for g in games if g.get('completed')]
        in_progress = [g for g in games if not g.get('completed')]
        self.assertEqual(len(completed), 1)
        self.assertEqual(len(in_progress), 1)

    def test_filter_by_tag(self):
        """Can filter games by tag."""
        self._create_game(tags=['favorite', 'easy-win'])
        self._create_game(tags=['hard-fail'])
        self._create_game(tags=['favorite'])
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        favorites = [g for g in games if 'favorite' in g.get('tags', [])]
        self.assertEqual(len(favorites), 2)

    def test_filter_by_elapsed_range(self):
        """Can filter games by elapsed time range."""
        self._create_game(elapsed=50)
        self._create_game(elapsed=200)
        self._create_game(elapsed=500)
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        fast = [g for g in games if g.get('elapsed', 0) < 100]
        medium = [g for g in games if 100 <= g.get('elapsed', 0) <= 300]
        slow = [g for g in games if g.get('elapsed', 0) > 300]
        self.assertEqual(len(fast), 1)
        self.assertEqual(len(medium), 1)
        self.assertEqual(len(slow), 1)

    def test_filter_archived(self):
        """Can separate archived from non-archived games."""
        gid1 = self._create_game()
        gid2 = self._create_game()
        self.client.put(f'/api/games/{gid1}/archive',
                       data=json.dumps({'archived': True}),
                       content_type='application/json')
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        archived = [g for g in games if g.get('archived')]
        active = [g for g in games if not g.get('archived')]
        self.assertEqual(len(archived), 1)
        self.assertEqual(len(active), 1)

    def test_filter_by_rating(self):
        """Can filter games by rating."""
        gid = self._create_game(completed=True)
        self.client.put(f'/api/games/{gid}/rate',
                       data=json.dumps({'rating': 5}),
                       content_type='application/json')
        self._create_game(completed=True)
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        rated = [g for g in games if g.get('rating', 0) > 0]
        unrated = [g for g in games if g.get('rating', 0) == 0]
        self.assertEqual(len(rated), 1)
        self.assertEqual(len(unrated), 1)

    def test_filter_by_notes(self):
        """Can filter games that have notes."""
        self._create_game()
        self._create_game()
        # Add notes to one game
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        gid = games[0]['game_id']
        self.client.put(f'/api/games/{gid}',
                       data=json.dumps({'notes': 'has a note'}),
                       content_type='application/json')
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        with_notes = [g for g in games if g.get('notes')]
        without_notes = [g for g in games if not g.get('notes')]
        self.assertEqual(len(with_notes), 1)
        self.assertEqual(len(without_notes), 1)

    def test_combined_filter(self):
        """Can combine multiple filters."""
        self._create_game(difficulty=30, completed=True, tags=['favorite'])
        self._create_game(difficulty=30, completed=False, tags=['favorite'])
        self._create_game(difficulty=50, completed=True, tags=['favorite'])
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        # Easy + completed + favorite
        result = [g for g in games
                  if g['difficulty'] == 30
                  and g.get('completed')
                  and 'favorite' in g.get('tags', [])]
        self.assertEqual(len(result), 1)

    def test_search_returns_all_when_no_filter(self):
        """Without filters, all games should be returned."""
        for _ in range(5):
            self._create_game()
        res = self.client.get('/api/games')
        self.assertEqual(len(res.get_json()['games']), 5)

    def test_games_have_all_filterable_fields(self):
        """Each game in list should have all filterable fields."""
        self._create_game(completed=True, tags=['test'])
        res = self.client.get('/api/games')
        game = res.get_json()['games'][0]
        for field in ['difficulty', 'completed', 'tags', 'archived', 'rating', 'notes', 'elapsed']:
            self.assertIn(field, game, f"Missing filterable field: {field}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
