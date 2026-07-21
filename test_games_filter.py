"""
Tests for the games list filter functionality.
Since filtering happens client-side, these tests verify the filter logic.
"""
import unittest


class TestGamesFilter(unittest.TestCase):
    """Tests for the games list filter logic."""

    def _filter_games(self, games, show_completed=True, show_in_progress=True):
        """Simulate the client-side filter logic."""
        return [g for g in games if
                (g.get('completed') and show_completed) or
                (not g.get('completed') and show_in_progress)]

    def test_show_all(self):
        """Both filters checked should show all games."""
        games = [
            {'game_id': '1', 'completed': True},
            {'game_id': '2', 'completed': False},
        ]
        result = self._filter_games(games, True, True)
        self.assertEqual(len(result), 2)

    def test_show_only_completed(self):
        """Only completed filter checked should show only completed games."""
        games = [
            {'game_id': '1', 'completed': True},
            {'game_id': '2', 'completed': False},
            {'game_id': '3', 'completed': True},
        ]
        result = self._filter_games(games, True, False)
        self.assertEqual(len(result), 2)
        self.assertTrue(all(g['completed'] for g in result))

    def test_show_only_in_progress(self):
        """Only in-progress filter checked should show only in-progress games."""
        games = [
            {'game_id': '1', 'completed': True},
            {'game_id': '2', 'completed': False},
            {'game_id': '3', 'completed': True},
        ]
        result = self._filter_games(games, False, True)
        self.assertEqual(len(result), 1)
        self.assertFalse(all(g['completed'] for g in result))

    def test_show_none(self):
        """Neither filter checked should show no games."""
        games = [
            {'game_id': '1', 'completed': True},
            {'game_id': '2', 'completed': False},
        ]
        result = self._filter_games(games, False, False)
        self.assertEqual(len(result), 0)

    def test_empty_games(self):
        """Filtering an empty list should return empty."""
        self.assertEqual(self._filter_games([]), [])

    def test_all_completed(self):
        """All games completed, show only in-progress should return empty."""
        games = [
            {'game_id': '1', 'completed': True},
            {'game_id': '2', 'completed': True},
        ]
        result = self._filter_games(games, False, True)
        self.assertEqual(len(result), 0)

    def test_all_in_progress(self):
        """All games in-progress, show only completed should return empty."""
        games = [
            {'game_id': '1', 'completed': False},
            {'game_id': '2', 'completed': False},
        ]
        result = self._filter_games(games, True, False)
        self.assertEqual(len(result), 0)

    def test_missing_completed_field(self):
        """Games without 'completed' field should be treated as in-progress."""
        games = [
            {'game_id': '1'},  # no 'completed' field
            {'game_id': '2', 'completed': True},
        ]
        result = self._filter_games(games, False, True)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['game_id'], '1')

    def test_preserves_game_data(self):
        """Filtering should not modify game data."""
        games = [
            {'game_id': '1', 'completed': True, 'elapsed': 100},
            {'game_id': '2', 'completed': False, 'elapsed': 50},
        ]
        result = self._filter_games(games, True, True)
        self.assertEqual(result[0]['elapsed'], 100)
        self.assertEqual(result[1]['elapsed'], 50)


if __name__ == '__main__':
    unittest.main(verbosity=2)
