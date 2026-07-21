"""Game storage layer using Google Cloud Firestore.

Falls back to an in-memory store when Firestore is not available (local dev).
This allows the app to run locally without GCP credentials.

Environment variables:
    FIRESTORE_PROJECT  — GCP project ID with a Firestore database.
                         If unset, uses in-memory storage.
    FIRESTORE_COLLECTION — Firestore collection name (default: "games").
"""
from __future__ import annotations

import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any

# Try to import Firestore; fall back gracefully if not installed/available.
try:
    from google.cloud import firestore as firestore_module

    _FIRESTORE_AVAILABLE = True
except ImportError:
    firestore_module = None  # type: ignore[assignment]
    _FIRESTORE_AVAILABLE = False


def _now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


class GameStorage:
    """Abstract game storage interface."""

    def create_game(self, state: dict[str, Any]) -> str:
        raise NotImplementedError

    def get_game(self, game_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    def save_game(self, game_id: str, state: dict[str, Any]) -> None:
        raise NotImplementedError

    def list_games(self, limit: int = 50) -> list[dict[str, Any]]:
        raise NotImplementedError

    def delete_game(self, game_id: str) -> bool:
        raise NotImplementedError


class InMemoryStorage(GameStorage):
    """In-memory game storage for local development and testing."""

    def __init__(self) -> None:
        self._games: dict[str, dict[str, Any]] = {}

    def create_game(self, state: dict[str, Any]) -> str:
        game_id = str(uuid.uuid4())
        state = dict(state)
        state["game_id"] = game_id
        state["created_at"] = _now_iso()
        state["updated_at"] = state["created_at"]
        self._games[game_id] = state
        return game_id

    def get_game(self, game_id: str) -> dict[str, Any] | None:
        game = self._games.get(game_id)
        return dict(game) if game else None

    def save_game(self, game_id: str, state: dict[str, Any]) -> None:
        if game_id not in self._games:
            raise KeyError(f"Game {game_id} not found")
        merged = dict(self._games[game_id])
        merged.update(state)
        merged["game_id"] = game_id
        merged["updated_at"] = _now_iso()
        self._games[game_id] = merged

    def list_games(self, limit: int = 50) -> list[dict[str, Any]]:
        games = sorted(
            self._games.values(),
            key=lambda g: g.get("updated_at", ""),
            reverse=True,
        )
        # Return metadata only (no board/solution/stacks)
        return [self._summarize(g) for g in games[:limit]]

    def delete_game(self, game_id: str) -> bool:
        return self._games.pop(game_id, None) is not None

    @staticmethod
    def _summarize(game: dict[str, Any]) -> dict[str, Any]:
        """Return a lightweight metadata dict for list views."""
        board = game.get("board", [])
        puzzle = game.get("puzzle", [])
        # Count filled and total cells, handling non-9x9 boards gracefully
        filled = 0
        total = 0
        if board and len(board) == 9 and all(len(r) == 9 for r in board):
            filled = sum(1 for r in range(9) for c in range(9) if board[r][c] != 0)
        if puzzle and len(puzzle) == 9 and all(len(r) == 9 for r in puzzle):
            total = sum(1 for r in range(9) for c in range(9) if puzzle[r][c] == 0)
        return {
            "game_id": game.get("game_id"),
            "difficulty": game.get("difficulty"),
            "mistakes": game.get("mistakes", 0),
            "elapsed": game.get("elapsed", 0),
            "completed": game.get("completed", False),
            "created_at": game.get("created_at"),
            "updated_at": game.get("updated_at"),
            "progress": f"{filled}/{total}" if total > 0 else "0/0",
        }


class FirestoreStorage(GameStorage):
    """Firestore-backed game storage for production."""

    def __init__(self, project_id: str, collection: str = "games") -> None:
        if not _FIRESTORE_AVAILABLE:
            raise RuntimeError(
                "google-cloud-firestore is not installed. "
                "Install with: pip install google-cloud-firestore"
            )
        self._db = firestore_module.Client(project=project_id)
        self._collection = self._db.collection(collection)

    def create_game(self, state: dict[str, Any]) -> str:
        game_id = str(uuid.uuid4())
        state = dict(state)
        state["game_id"] = game_id
        state["created_at"] = _now_iso()
        state["updated_at"] = state["created_at"]
        self._collection.document(game_id).set(state)
        return game_id

    def get_game(self, game_id: str) -> dict[str, Any] | None:
        doc = self._collection.document(game_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        if data:
            data["game_id"] = game_id
        return data

    def save_game(self, game_id: str, state: dict[str, Any]) -> None:
        state = dict(state)
        state["updated_at"] = _now_iso()
        self._collection.document(game_id).set(state, merge=True)

    def list_games(self, limit: int = 50) -> list[dict[str, Any]]:
        docs = (
            self._collection.order_by("updated_at", direction="DESCENDING")
            .limit(limit)
            .stream()
        )
        games = []
        for doc in docs:
            data = doc.to_dict()
            if data:
                data["game_id"] = doc.id
                games.append(InMemoryStorage._summarize(data))
        return games

    def delete_game(self, game_id: str) -> bool:
        ref = self._collection.document(game_id)
        doc = ref.get()
        if not doc.exists:
            return False
        ref.delete()
        return True


# Factory: pick the right storage based on environment.
_storage: GameStorage | None = None


def get_storage() -> GameStorage:
    """Return the singleton storage instance.

    Uses Firestore if FIRESTORE_PROJECT is set; otherwise in-memory.
    """
    global _storage
    if _storage is not None:
        return _storage

    project = os.environ.get("FIRESTORE_PROJECT")
    collection = os.environ.get("FIRESTORE_COLLECTION", "games")

    if project and _FIRESTORE_AVAILABLE:
        try:
            _storage = FirestoreStorage(project, collection)
        except Exception:
            # If Firestore initialization fails, fall back to in-memory.
            _storage = InMemoryStorage()
    else:
        _storage = InMemoryStorage()

    return _storage
