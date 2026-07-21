"""
Tests for the FirestoreStorage serialization and deserialization.
These tests verify that the _serialize and _deserialize methods correctly
handle array fields by converting them to/from JSON strings.
"""
import json
import unittest
from storage import FirestoreStorage


class TestFirestoreSerialization(unittest.TestCase):
    """Tests for Firestore serialization of nested arrays."""

    def test_serialize_converts_arrays_to_strings(self):
        """_serialize should convert array fields to JSON strings."""
        game = {
            'game_id': 'test-1',
            'puzzle': [[1, 2, 3], [4, 5, 6]],
            'solution': [[1, 2, 3], [4, 5, 6]],
            'board': [[1, 0, 3], [0, 5, 0]],
            'given': [[True, False, True], [False, True, False]],
            'notes': [[[False] * 9] * 3] * 2,
            'undoStack': [{'board': [[1]], 'notes': [[[False]]], 'given': [[True]], 'mistakes': 0}],
            'redoStack': [],
            'difficulty': 40,
            'elapsed': 100,
            'mistakes': 2,
        }
        serialized = FirestoreStorage._serialize(game)
        # Array fields should be strings
        for field in FirestoreStorage._ARRAY_FIELDS:
            self.assertIsInstance(serialized[field], str,
                                f"{field} should be serialized to string")
        # Non-array fields should be preserved
        self.assertEqual(serialized['difficulty'], 40)
        self.assertEqual(serialized['elapsed'], 100)

    def test_deserialize_converts_strings_back_to_arrays(self):
        """_deserialize should convert JSON strings back to arrays."""
        game = {
            'puzzle': json.dumps([[1, 2, 3], [4, 5, 6]]),
            'solution': json.dumps([[1, 2, 3], [4, 5, 6]]),
            'board': json.dumps([[1, 0, 3], [0, 5, 0]]),
            'given': json.dumps([[True, False, True], [False, True, False]]),
            'notes': json.dumps([[[False] * 9] * 3] * 2),
            'undoStack': json.dumps([{'board': [[1]], 'notes': [[[False]]], 'given': [[True]], 'mistakes': 0}]),
            'redoStack': json.dumps([]),
            'difficulty': 40,
            'elapsed': 100,
        }
        deserialized = FirestoreStorage._deserialize(game)
        # Array fields should be arrays again
        self.assertIsInstance(deserialized['puzzle'], list)
        self.assertIsInstance(deserialized['solution'], list)
        self.assertIsInstance(deserialized['board'], list)
        self.assertIsInstance(deserialized['given'], list)
        self.assertIsInstance(deserialized['notes'], list)
        self.assertIsInstance(deserialized['undoStack'], list)
        self.assertIsInstance(deserialized['redoStack'], list)
        # Values should match
        self.assertEqual(deserialized['puzzle'], [[1, 2, 3], [4, 5, 6]])
        self.assertEqual(deserialized['elapsed'], 100)

    def test_serialize_deserialize_roundtrip(self):
        """Serialize then deserialize should preserve all data."""
        original = {
            'puzzle': [[5, 0, 1, 0, 0, 0, 0, 0, 0]] * 9,
            'solution': [[5, 7, 1, 2, 4, 3, 6, 8, 9]] * 9,
            'board': [[5, 7, 0, 0, 0, 0, 0, 0, 0]] * 9,
            'given': [[True, False, True, False, False, False, False, False, False]] * 9,
            'notes': [[[False] * 9 for _ in range(9)] for _ in range(9)],
            'undoStack': [],
            'redoStack': [],
            'difficulty': 40,
            'elapsed': 250,
            'mistakes': 3,
            'completed': False,
        }
        serialized = FirestoreStorage._serialize(original)
        deserialized = FirestoreStorage._deserialize(serialized)
        # All array fields should match
        for field in FirestoreStorage._ARRAY_FIELDS:
            self.assertEqual(deserialized[field], original[field],
                           f"{field} should match after roundtrip")

    def test_serialize_preserves_non_array_fields(self):
        """_serialize should not modify non-array fields."""
        game = {
            'puzzle': json.dumps([[1]]),
            'difficulty': 50,
            'elapsed': 300,
            'mistakes': 5,
            'completed': True,
            'game_id': 'abc-123',
        }
        serialized = FirestoreStorage._serialize(game)
        self.assertEqual(serialized['difficulty'], 50)
        self.assertEqual(serialized['elapsed'], 300)
        self.assertEqual(serialized['completed'], True)
        self.assertEqual(serialized['game_id'], 'abc-123')

    def test_deserialize_handles_missing_fields(self):
        """_deserialize should handle missing array fields gracefully."""
        game = {
            'difficulty': 40,
            'elapsed': 100,
        }
        deserialized = FirestoreStorage._deserialize(game)
        self.assertEqual(deserialized['difficulty'], 40)
        self.assertEqual(deserialized['elapsed'], 100)
        # Missing array fields should not be present or should be None
        self.assertNotIn('puzzle', deserialized)


if __name__ == '__main__':
    unittest.main(verbosity=2)
