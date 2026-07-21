"""
Tests for the games list sorting functionality.
Since sorting happens client-side, these tests verify the sort logic
by simulating the same comparisons the frontend does.
"""
import unittest


class TestGamesListSort(unittest.TestCase):
    """Tests for the sort logic used by the games list."""

    def _sort_games(self, games, sort_by='updated'):
        """Simulate the client-side sort logic."""
        if sort_by == 'updated':
            return sorted(games, key=lambda g: g.get('updated_at', ''),
                          reverse=True)
        elif sort_by == 'progress':
            def progress_ratio(g):
                p = g.get('progress', '0/0').split('/')
                if len(p) == 2 and int(p[1]) > 0:
                    return int(p[0]) / int(p[1])
                return 0
            return sorted(games, key=progress_ratio, reverse=True)
        else:
            return sorted(games, key=lambda g: g.get(sort_by, 0), reverse=True)

    def test_sort_by_updated_desc(self):
        """Games should be sorted by updated_at descending."""
        games = [
            {'game_id': '1', 'updated_at': '2026-01-01T10:00:00Z'},
            {'game_id': '2', 'updated_at': '2026-01-03T10:00:00Z'},
            {'game_id': '3', 'updated_at': '2026-01-02T10:00:00Z'},
        ]
        sorted_games = self._sort_games(games, 'updated')
        self.assertEqual(sorted_games[0]['game_id'], '2')
        self.assertEqual(sorted_games[1]['game_id'], '3')
        self.assertEqual(sorted_games[2]['game_id'], '1')

    def test_sort_by_elapsed(self):
        """Games should be sorted by elapsed time descending."""
        games = [
            {'game_id': 'a', 'elapsed': 100},
            {'game_id': 'b', 'elapsed': 300},
            {'game_id': 'c', 'elapsed': 50},
        ]
        sorted_games = self._sort_games(games, 'elapsed')
        self.assertEqual(sorted_games[0]['game_id'], 'b')
        self.assertEqual(sorted_games[1]['game_id'], 'a')
        self.assertEqual(sorted_games[2]['game_id'], 'c')

    def test_sort_by_difficulty(self):
        """Games should be sorted by difficulty descending."""
        games = [
            {'game_id': 'a', 'difficulty': 30},
            {'game_id': 'b', 'difficulty': 58},
            {'game_id': 'c', 'difficulty': 40},
        ]
        sorted_games = self._sort_games(games, 'difficulty')
        self.assertEqual(sorted_games[0]['game_id'], 'b')
        self.assertEqual(sorted_games[1]['game_id'], 'c')
        self.assertEqual(sorted_games[2]['game_id'], 'a')

    def test_sort_by_mistakes(self):
        """Games should be sorted by mistakes descending."""
        games = [
            {'game_id': 'a', 'mistakes': 5},
            {'game_id': 'b', 'mistakes': 10},
            {'game_id': 'c', 'mistakes': 0},
        ]
        sorted_games = self._sort_games(games, 'mistakes')
        self.assertEqual(sorted_games[0]['game_id'], 'b')
        self.assertEqual(sorted_games[1]['game_id'], 'a')
        self.assertEqual(sorted_games[2]['game_id'], 'c')

    def test_sort_by_progress(self):
        """Games should be sorted by progress ratio descending."""
        games = [
            {'game_id': 'a', 'progress': '5/40'},
            {'game_id': 'b', 'progress': '40/40'},
            {'game_id': 'c', 'progress': '20/40'},
        ]
        sorted_games = self._sort_games(games, 'progress')
        self.assertEqual(sorted_games[0]['game_id'], 'b')
        self.assertEqual(sorted_games[1]['game_id'], 'c')
        self.assertEqual(sorted_games[2]['game_id'], 'a')

    def test_sort_empty_list(self):
        """Sorting an empty list should return empty."""
        self.assertEqual(self._sort_games([], 'elapsed'), [])

    def test_sort_single_game(self):
        """Sorting a single game should return it."""
        games = [{'game_id': 'a', 'elapsed': 100}]
        result = self._sort_games(games, 'elapsed')
        self.assertEqual(len(result), 1)

    def test_sort_with_missing_fields(self):
        """Sorting should handle missing fields gracefully."""
        games = [
            {'game_id': 'a'},
            {'game_id': 'b', 'elapsed': 100},
        ]
        result = self._sort_games(games, 'elapsed')
        self.assertEqual(result[0]['game_id'], 'b')
        self.assertEqual(result[1]['game_id'], 'a')

    def test_sort_preserves_all_games(self):
        """Sorting should not lose any games."""
        games = [{'game_id': str(i), 'elapsed': i} for i in range(10)]
        result = self._sort_games(games, 'elapsed')
        self.assertEqual(len(result), 10)

    def test_sort_default_is_updated(self):
        """Default sort should be by updated_at."""
        games = [
            {'game_id': '1', 'updated_at': '2026-01-01', 'elapsed': 100},
            {'game_id': '2', 'updated_at': '2026-01-02', 'elapsed': 50},
        ]
        result = self._sort_games(games)  # no sort_by = default 'updated'
        self.assertEqual(result[0]['game_id'], '2')


if __name__ == '__main__':
    unittest.main(verbosity=2)
