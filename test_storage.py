"""Unit tests for storage.py — game persistence layer."""
import unittest
from unittest.mock import MagicMock, patch
from storage import GameStorage, InMemoryStorage, FirestoreStorage, get_storage, _FIRESTORE_AVAILABLE


class TestInMemoryStorage(unittest.TestCase):
    """Tests for the InMemoryStorage backend."""

    def setUp(self):
        self.storage = InMemoryStorage()
        self.sample_state = {
            "puzzle": [[5, 0, 1], [0, 3, 0], [0, 0, 9]],
            "solution": [[5, 7, 1], [8, 3, 2], [4, 6, 9]],
            "board": [[5, 0, 1], [0, 3, 0], [0, 0, 9]],
            "given": [[True, False, True], [False, True, False], [False, False, True]],
            "notes": [[[False] * 9 for _ in range(3)] for _ in range(3)],
            "undoStack": [],
            "redoStack": [],
            "mistakes": 0,
            "elapsed": 120,
            "difficulty": 40,
            "completed": False,
        }

    def test_create_game_returns_id(self):
        game_id = self.storage.create_game(self.sample_state)
        self.assertIsInstance(game_id, str)
        self.assertTrue(len(game_id) > 0)

    def test_create_game_assigns_timestamps(self):
        game_id = self.storage.create_game(self.sample_state)
        game = self.storage.get_game(game_id)
        self.assertIsNotNone(game)
        self.assertIn("created_at", game)
        self.assertIn("updated_at", game)
        self.assertEqual(game["created_at"], game["updated_at"])

    def test_get_game_returns_data(self):
        game_id = self.storage.create_game(self.sample_state)
        game = self.storage.get_game(game_id)
        self.assertEqual(game["puzzle"], self.sample_state["puzzle"])
        self.assertEqual(game["difficulty"], 40)

    def test_get_nonexistent_game_returns_none(self):
        self.assertIsNone(self.storage.get_game("nonexistent-id"))

    def test_save_game_updates_state(self):
        game_id = self.storage.create_game(self.sample_state)
        updated = dict(self.sample_state)
        updated["mistakes"] = 5
        updated["elapsed"] = 300
        self.storage.save_game(game_id, updated)
        game = self.storage.get_game(game_id)
        self.assertEqual(game["mistakes"], 5)
        self.assertEqual(game["elapsed"], 300)

    def test_save_game_updates_timestamp(self):
        game_id = self.storage.create_game(self.sample_state)
        original = self.storage.get_game(game_id)
        self.storage.save_game(game_id, {"mistakes": 1})
        updated = self.storage.get_game(game_id)
        self.assertGreaterEqual(updated["updated_at"], original["updated_at"])

    def test_save_nonexistent_game_raises(self):
        with self.assertRaises(KeyError):
            self.storage.save_game("nonexistent", {"mistakes": 1})

    def test_list_games_returns_metadata(self):
        for i in range(3):
            state = dict(self.sample_state)
            state["mistakes"] = i
            self.storage.create_game(state)
        games = self.storage.list_games()
        self.assertEqual(len(games), 3)
        # Should not contain full board/solution data
        for game in games:
            self.assertNotIn("board", game)
            self.assertNotIn("solution", game)
            self.assertIn("game_id", game)
            self.assertIn("difficulty", game)
            self.assertIn("mistakes", game)
            self.assertIn("elapsed", game)

    def test_list_games_ordered_by_updated_at(self):
        id1 = self.storage.create_game(self.sample_state)
        id2 = self.storage.create_game(self.sample_state)
        self.storage.save_game(id1, {"mistakes": 1})
        games = self.storage.list_games()
        self.assertEqual(games[0]["game_id"], id1)

    def test_list_games_respects_limit(self):
        for _ in range(10):
            self.storage.create_game(self.sample_state)
        games = self.storage.list_games(limit=3)
        self.assertEqual(len(games), 3)

    def test_delete_game_returns_true(self):
        game_id = self.storage.create_game(self.sample_state)
        self.assertTrue(self.storage.delete_game(game_id))
        self.assertIsNone(self.storage.get_game(game_id))

    def test_delete_nonexistent_returns_false(self):
        self.assertFalse(self.storage.delete_game("nonexistent"))

    def test_full_state_roundtrip(self):
        """Create, save, retrieve — verify full game state integrity."""
        game_id = self.storage.create_game(self.sample_state)
        # Modify state
        modified = dict(self.sample_state)
        modified["board"] = [[5, 7, 1], [8, 3, 2], [4, 6, 9]]
        modified["mistakes"] = 3
        modified["undoStack"] = [{"board": [[5, 7, 1]], "notes": [[[False]*9]], "given": [[True, True, True]], "mistakes": 2}]
        self.storage.save_game(game_id, modified)
        # Retrieve
        game = self.storage.get_game(game_id)
        self.assertEqual(game["board"], [[5, 7, 1], [8, 3, 2], [4, 6, 9]])
        self.assertEqual(game["mistakes"], 3)
        self.assertEqual(len(game["undoStack"]), 1)
        self.assertEqual(game["undoStack"][0]["mistakes"], 2)


class TestGetStorageFactory(unittest.TestCase):
    """Tests for the get_storage() factory function."""

    def setUp(self):
        # Reset the singleton
        import storage as storage_module
        storage_module._storage = None

    def test_returns_in_memory_when_no_env(self):
        import storage as storage_module
        storage_module._storage = None
        with patch.dict("os.environ", {}, clear=False):
            if "FIRESTORE_PROJECT" in __import__("os").environ:
                del __import__("os").environ["FIRESTORE_PROJECT"]
            s = get_storage()
            self.assertIsInstance(s, InMemoryStorage)

    def test_returns_same_instance(self):
        s1 = get_storage()
        s2 = get_storage()
        self.assertIs(s1, s2)


class TestFirestoreStorage(unittest.TestCase):
    """Tests for the FirestoreStorage backend (mocked, no real GCP calls)."""

    @unittest.skipIf(
        not _FIRESTORE_AVAILABLE,
        "google-cloud-firestore not installed (tests use mocks but need the module importable)",
    )
    def setUp(self):
        self.sample_state = {
            "puzzle": [[0] * 9 for _ in range(9)],
            "solution": [[1] * 9 for _ in range(9)],
            "board": [[0] * 9 for _ in range(9)],
            "given": [[False] * 9 for _ in range(9)],
            "notes": [[[False] * 9 for _ in range(9)] for _ in range(9)],
            "undoStack": [],
            "redoStack": [],
            "mistakes": 0,
            "elapsed": 0,
            "difficulty": 40,
            "completed": False,
        }

    @patch("storage.firestore_module")
    def test_create_game_calls_firestore(self, mock_fs):
        mock_client = MagicMock()
        mock_fs.Client.return_value = mock_client
        mock_doc = MagicMock()
        mock_client.collection.return_value.document.return_value = mock_doc

        storage = FirestoreStorage("test-project", "games")
        game_id = storage.create_game(self.sample_state)

        self.assertTrue(len(game_id) > 0)
        mock_doc.set.assert_called_once()
        call_args = mock_doc.set.call_args[0][0]
        self.assertEqual(call_args["game_id"], game_id)
        self.assertIn("created_at", call_args)

    @patch("storage.firestore_module")
    def test_get_game_returns_none_when_not_found(self, mock_fs):
        mock_client = MagicMock()
        mock_fs.Client.return_value = mock_client
        mock_doc_ref = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_doc_ref.get.return_value = mock_doc
        mock_client.collection.return_value.document.return_value = mock_doc_ref

        storage = FirestoreStorage("test-project", "games")
        result = storage.get_game("nonexistent")
        self.assertIsNone(result)

    @patch("storage.firestore_module")
    def test_get_game_returns_data(self, mock_fs):
        mock_client = MagicMock()
        mock_fs.Client.return_value = mock_client
        mock_doc_ref = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"difficulty": 40, "mistakes": 2}
        mock_doc_ref.get.return_value = mock_doc
        mock_client.collection.return_value.document.return_value = mock_doc_ref

        storage = FirestoreStorage("test-project", "games")
        result = storage.get_game("abc123")
        self.assertIsNotNone(result)
        self.assertEqual(result["difficulty"], 40)
        self.assertEqual(result["game_id"], "abc123")

    @patch("storage.firestore_module")
    def test_save_game_merges_data(self, mock_fs):
        mock_client = MagicMock()
        mock_fs.Client.return_value = mock_client
        mock_doc_ref = MagicMock()
        mock_client.collection.return_value.document.return_value = mock_doc_ref

        storage = FirestoreStorage("test-project", "games")
        storage.save_game("abc123", {"mistakes": 5})

        mock_doc_ref.set.assert_called_once()
        call_args = mock_doc_ref.set.call_args
        self.assertTrue(call_args.kwargs.get("merge", False))
        self.assertIn("updated_at", call_args[0][0])

    @patch("storage.firestore_module")
    def test_delete_game_existing(self, mock_fs):
        mock_client = MagicMock()
        mock_fs.Client.return_value = mock_client
        mock_doc_ref = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc_ref.get.return_value = mock_doc
        mock_client.collection.return_value.document.return_value = mock_doc_ref

        storage = FirestoreStorage("test-project", "games")
        result = storage.delete_game("abc123")
        self.assertTrue(result)
        mock_doc_ref.delete.assert_called_once()

    @patch("storage.firestore_module")
    def test_delete_game_nonexistent(self, mock_fs):
        mock_client = MagicMock()
        mock_fs.Client.return_value = mock_client
        mock_doc_ref = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_doc_ref.get.return_value = mock_doc
        mock_client.collection.return_value.document.return_value = mock_doc_ref

        storage = FirestoreStorage("test-project", "games")
        result = storage.delete_game("nonexistent")
        self.assertFalse(result)


class TestFirestoreSerialization(unittest.TestCase):
    """Tests for Firestore array serialization/deserialization.

    These test the _serialize and _deserialize class methods directly,
    so they don't need google-cloud-firestore to be installed.
    """

    def setUp(self):
        self.state = {
            "puzzle": [[5, 0, 1, 0, 0, 0, 0, 0, 0],
                       [0, 3, 0, 0, 0, 0, 0, 0, 0],
                       [0, 0, 9, 0, 0, 0, 0, 0, 0]] + [[0] * 9] * 6,
            "solution": [[5, 7, 1, 2, 4, 3, 6, 8, 9],
                         [8, 3, 2, 5, 7, 9, 1, 4, 6],
                         [4, 6, 9, 1, 2, 8, 3, 5, 7]] + [[1] * 9] * 6,
            "board": [[5, 0, 1, 0, 0, 0, 0, 0, 0],
                      [0, 3, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 9, 0, 0, 0, 0, 0, 0]] + [[0] * 9] * 6,
            "given": [[True, False, True, False, False, False, False, False, False],
                      [False, True, False, False, False, False, False, False, False],
                      [False, False, True, False, False, False, False, False, False]] + [[False] * 9] * 6,
            "notes": [[[False] * 9 for _ in range(9)] for _ in range(9)],
            "undoStack": [
                {
                    "board": [[5, 0, 1] + [0] * 6] + [[0] * 9] * 8,
                    "notes": [[[False] * 9] * 9] * 9,
                    "given": [[True, False, True] + [False] * 6] + [[False] * 9] * 8,
                    "mistakes": 0,
                }
            ],
            "redoStack": [],
            "mistakes": 2,
            "elapsed": 150,
            "difficulty": 40,
            "completed": False,
        }

    def test_serialize_converts_arrays_to_strings(self):
        serialized = FirestoreStorage._serialize(self.state)
        for key in FirestoreStorage._ARRAY_FIELDS:
            self.assertIsInstance(serialized[key], str, f"{key} should be a string after serialization")

    def test_deserialize_converts_strings_back_to_arrays(self):
        serialized = FirestoreStorage._serialize(self.state)
        deserialized = FirestoreStorage._deserialize(serialized)
        for key in FirestoreStorage._ARRAY_FIELDS:
            self.assertIsInstance(deserialized[key], list, f"{key} should be a list after deserialization")

    def test_roundtrip_preserves_data(self):
        """Serialize then deserialize should produce identical data."""
        serialized = FirestoreStorage._serialize(self.state)
        deserialized = FirestoreStorage._deserialize(serialized)
        for key in self.state:
            self.assertEqual(deserialized[key], self.state[key], f"{key} mismatch in roundtrip")

    def test_serialize_preserves_non_array_fields(self):
        """Non-array fields like mistakes, elapsed should not be converted."""
        serialized = FirestoreStorage._serialize(self.state)
        self.assertEqual(serialized["mistakes"], 2)
        self.assertEqual(serialized["elapsed"], 150)
        self.assertEqual(serialized["difficulty"], 40)
        self.assertEqual(serialized["completed"], False)

    def test_deserialize_handles_missing_fields(self):
        """Deserializing data without array fields should not crash."""
        data = {"mistakes": 5, "elapsed": 30}
        result = FirestoreStorage._deserialize(data)
        self.assertEqual(result["mistakes"], 5)

    def test_deserialize_handles_non_string_arrays(self):
        """If a field is already a list (not a string), deserialization should leave it."""
        data = {"puzzle": [[1, 2, 3]], "mistakes": 0}
        result = FirestoreStorage._deserialize(data)
        self.assertEqual(result["puzzle"], [[1, 2, 3]])

    def test_serialize_does_not_mutate_input(self):
        """Serialization should not modify the original state."""
        original_puzzle = self.state["puzzle"]
        FirestoreStorage._serialize(self.state)
        self.assertIs(self.state["puzzle"], original_puzzle)
        self.assertIsInstance(self.state["puzzle"], list)

    def test_serialize_empty_state(self):
        """Serializing an empty dict should work."""
        result = FirestoreStorage._serialize({})
        self.assertEqual(result, {})

    def test_serialize_with_notes_nested_3_levels(self):
        """Notes are 3D arrays (9x9x9) — ensure they serialize correctly."""
        state = {"notes": [[[True, False] + [False] * 7] * 9] * 9}
        serialized = FirestoreStorage._serialize(state)
        self.assertIsInstance(serialized["notes"], str)
        deserialized = FirestoreStorage._deserialize(serialized)
        self.assertTrue(deserialized["notes"][0][0][0])
        self.assertFalse(deserialized["notes"][0][0][1])

    def test_serialize_with_undo_stack_containing_nested_arrays(self):
        """Undo stack entries contain nested board/notes arrays."""
        state = {
            "undoStack": [
                {
                    "board": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
                    "notes": [[[False] * 9] * 9] * 9,
                    "given": [[True] * 9] * 9,
                    "mistakes": 3,
                }
            ]
        }
        serialized = FirestoreStorage._serialize(state)
        self.assertIsInstance(serialized["undoStack"], str)
        deserialized = FirestoreStorage._deserialize(serialized)
        self.assertEqual(deserialized["undoStack"][0]["board"], [[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        self.assertEqual(deserialized["undoStack"][0]["mistakes"], 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
