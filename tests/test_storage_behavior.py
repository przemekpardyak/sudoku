"""
Tests for the storage layer — InMemoryStorage behavior with various game states.
"""
import unittest
import time
from storage import InMemoryStorage
from sudoku import generate_puzzle


class TestStorageBehavior(unittest.TestCase):
    """Tests for InMemoryStorage behavior with real game data."""

    def setUp(self):
        self.storage = InMemoryStorage()

    def test_create_and_get_game(self):
        """Create a game and retrieve it."""
        state = {'difficulty': 40, 'elapsed': 50, 'board': [[1]*9]*9}
        game_id = self.storage.create_game(state)
        game = self.storage.get_game(game_id)
        self.assertIsNotNone(game)
        self.assertEqual(game['difficulty'], 40)
        self.assertEqual(game['elapsed'], 50)

    def test_list_games_empty(self):
        """List games on empty storage should return empty list."""
        self.assertEqual(self.storage.list_games(), [])

    def test_list_games_limit(self):
        """List games should respect the limit parameter."""
        for i in range(10):
            self.storage.create_game({'difficulty': 40, 'elapsed': i})
        games = self.storage.list_games(limit=5)
        self.assertEqual(len(games), 5)

    def test_list_games_sorted_by_updated(self):
        """Games should be sorted by updated_at in descending order."""
        id1 = self.storage.create_game({'difficulty': 40, 'elapsed': 10})
        time.sleep(0.01)
        id2 = self.storage.create_game({'difficulty': 40, 'elapsed': 20})
        games = self.storage.list_games()
        self.assertEqual(games[0]['game_id'], id2)
        self.assertEqual(games[1]['game_id'], id1)

    def test_save_game_merges_state(self):
        """save_game should merge the new state with existing."""
        game_id = self.storage.create_game({'difficulty': 40, 'elapsed': 10, 'mistakes': 0})
        self.storage.save_game(game_id, {'elapsed': 20, 'mistakes': 3})
        game = self.storage.get_game(game_id)
        self.assertEqual(game['elapsed'], 20)
        self.assertEqual(game['mistakes'], 3)
        self.assertEqual(game['difficulty'], 40)  # preserved from original

    def test_delete_game(self):
        """Delete should remove the game."""
        game_id = self.storage.create_game({'difficulty': 40})
        self.assertTrue(self.storage.delete_game(game_id))
        self.assertIsNone(self.storage.get_game(game_id))

    def test_delete_nonexistent(self):
        """Delete non-existent game should return False."""
        self.assertFalse(self.storage.delete_game('nonexistent'))

    def test_get_nonexistent(self):
        """Get non-existent game should return None."""
        self.assertIsNone(self.storage.get_game('nonexistent'))

    def test_save_nonexistent_raises(self):
        """Saving a non-existent game should raise KeyError."""
        with self.assertRaises(KeyError):
            self.storage.save_game('nonexistent', {'elapsed': 10})

    def test_create_multiple_games(self):
        """Creating multiple games should give each a unique ID."""
        ids = set()
        for _ in range(5):
            gid = self.storage.create_game({'difficulty': 40})
            ids.add(gid)
        self.assertEqual(len(ids), 5)

    def test_game_has_timestamps(self):
        """Created games should have created_at and updated_at timestamps."""
        game_id = self.storage.create_game({'difficulty': 40})
        game = self.storage.get_game(game_id)
        self.assertIn('created_at', game)
        self.assertIn('updated_at', game)

    def test_save_updates_timestamp(self):
        """Saving a game should update the updated_at timestamp."""
        game_id = self.storage.create_game({'difficulty': 40, 'elapsed': 0})
        original = self.storage.get_game(game_id)
        time.sleep(0.01)
        self.storage.save_game(game_id, {'elapsed': 10})
        updated = self.storage.get_game(game_id)
        self.assertNotEqual(original['updated_at'], updated['updated_at'])

    def test_summary_has_progress(self):
        """Game summary should include progress field."""
        puzzle, solution = generate_puzzle(difficulty=30)
        game_id = self.storage.create_game({
            'puzzle': puzzle, 'board': puzzle, 'difficulty': 30
        })
        games = self.storage.list_games()
        self.assertIn('progress', games[0])

    def test_summary_has_hints_used(self):
        """Game summary should include hintsUsed field."""
        game_id = self.storage.create_game({
            'difficulty': 40, 'hintsUsed': 5
        })
        games = self.storage.list_games()
        self.assertIn('hintsUsed', games[0])
        self.assertEqual(games[0]['hintsUsed'], 5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
