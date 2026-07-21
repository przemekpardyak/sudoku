"""User authentication module — session-based auth for the Sudoku app.

Uses hashlib.pbkdf2_hmac for password hashing (no external dependencies).
Supports Firestore `users` collection for production, with an in-memory
fallback for local development and testing.

Environment variables:
    FIRESTORE_PROJECT  — GCP project ID with a Firestore database.
                          If unset, uses in-memory storage.
"""
from __future__ import annotations

import hashlib
import os
import secrets
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


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

_PBKDF2_ITERATIONS = 200_000
_HASH_ALGO = "sha256"


def _now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def hash_password(password: str) -> str:
    """Hash a password using pbkdf2_hmac with a random salt.

    Returns a string in the format: ``algo$iterations$salt_hex$hash_hex``.
    """
    salt = secrets.token_bytes(32)
    dk = hashlib.pbkdf2_hmac(_HASH_ALGO, password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return f"{_HASH_ALGO}${_PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a stored hash.

    Supports the ``algo$iterations$salt_hex$hash_hex`` format produced by
    :func:`hash_password`. Falls back to the legacy ``salt:hash`` hex format
    for backward compatibility.
    """
    if not stored_hash:
        return False
    try:
        if "$" in stored_hash:
            algo, iterations, salt_hex, hash_hex = stored_hash.split("$", 3)
            salt = bytes.fromhex(salt_hex)
            dk = hashlib.pbkdf2_hmac(algo, password.encode("utf-8"), salt, int(iterations))
            return secrets.compare_digest(dk.hex(), hash_hex)
        # Legacy colon-separated format (salt_hex:hash_hex)
        salt_hex, hash_hex = stored_hash.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac(_HASH_ALGO, password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
        return secrets.compare_digest(dk.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


# ---------------------------------------------------------------------------
# User storage interface
# ---------------------------------------------------------------------------


class UserStorage:
    """Abstract user storage interface."""

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        raise NotImplementedError

    def create_user(self, user: dict[str, Any]) -> str:
        raise NotImplementedError


class InMemoryUserStorage(UserStorage):
    """In-memory user storage for local development and testing."""

    def __init__(self) -> None:
        self._users: dict[str, dict[str, Any]] = {}
        self._username_index: dict[str, str] = {}

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        user = self._users.get(user_id)
        return dict(user) if user else None

    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        user_id = self._username_index.get(username)
        if not user_id:
            return None
        return self.get_user_by_id(user_id)

    def create_user(self, user: dict[str, Any]) -> str:
        user_id = user["user_id"]
        self._users[user_id] = dict(user)
        self._username_index[user["username"]] = user_id
        return user_id


class FirestoreUserStorage(UserStorage):
    """Firestore-backed user storage for production.

    Uses the `users` collection in the same Firestore database as games.
    """

    def __init__(self, project_id: str, collection: str = "users") -> None:
        if not _FIRESTORE_AVAILABLE:
            raise RuntimeError(
                "google-cloud-firestore is not installed. "
                "Install with: pip install google-cloud-firestore"
            )
        self._db = firestore_module.Client(project=project_id)
        self._collection = self._db.collection(collection)

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        doc = self._collection.document(user_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        if data:
            data["user_id"] = user_id
        return data

    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        # Query by username field
        query = self._collection.where("username", "==", username).limit(1)
        docs = list(query.stream())
        if not docs:
            return None
        doc = docs[0]
        data = doc.to_dict()
        if data:
            data["user_id"] = doc.id
        return data

    def create_user(self, user: dict[str, Any]) -> str:
        user_id = user["user_id"]
        self._collection.document(user_id).set(user)
        return user_id


# ---------------------------------------------------------------------------
# Singleton storage factory
# ---------------------------------------------------------------------------

_user_storage: UserStorage | None = None


def _get_user_storage() -> UserStorage:
    """Return the singleton user storage instance.

    Uses Firestore if FIRESTORE_PROJECT is set; otherwise in-memory.
    """
    global _user_storage
    if _user_storage is not None:
        return _user_storage

    project = os.environ.get("FIRESTORE_PROJECT")
    if project and _FIRESTORE_AVAILABLE:
        try:
            _user_storage = FirestoreUserStorage(project)
        except Exception:
            _user_storage = InMemoryUserStorage()
    else:
        _user_storage = InMemoryUserStorage()

    return _user_storage


def reset_user_store() -> None:
    """Reset the user store to a fresh in-memory instance (for testing)."""
    global _user_storage
    _user_storage = InMemoryUserStorage()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_user(username: str, password: str) -> dict[str, Any]:
    """Create a new user with a hashed password.

    Args:
        username: Unique username.
        password: Plaintext password (will be hashed, never stored).

    Returns:
        The created user dict (without the password hash).

    Raises:
        ValueError: If the username already exists.
    """
    if not username or not password:
        raise ValueError("Username and password are required")

    store = _get_user_storage()
    if store.get_user_by_username(username) is not None:
        raise ValueError(f"Username '{username}' already exists")

    user_id = str(uuid.uuid4())
    user = {
        "user_id": user_id,
        "username": username,
        "password_hash": hash_password(password),
        "created_at": _now_iso(),
    }
    store.create_user(user)
    return {"user_id": user_id, "username": username, "created_at": user["created_at"]}


def authenticate(username: str, password: str) -> dict[str, Any] | None:
    """Authenticate a user by username and password.

    Returns the user dict (without password_hash) if successful, else None.
    """
    store = _get_user_storage()
    user = store.get_user_by_username(username)
    if user is None:
        return None
    if not verify_password(password, user.get("password_hash", "")):
        return None
    return {"user_id": user["user_id"], "username": user["username"]}


def get_user(user_id: str) -> dict[str, Any] | None:
    """Get a user by ID.

    Returns the full stored user dict (including password_hash) if found,
    else None. The raw plaintext password is never stored.
    """
    store = _get_user_storage()
    user = store.get_user_by_id(user_id)
    if user is None:
        return None
    return dict(user)


def ensure_default_user() -> None:
    """Ensure the default user (testuser/password) exists.

    Creates it if it does not exist. Does NOT overwrite an existing testuser
    with a different password.
    """
    store = _get_user_storage()
    existing = store.get_user_by_username("testuser")
    if existing is not None:
        return
    create_user("testuser", "password")


def get_default_user() -> dict[str, Any] | None:
    """Get the default testuser's user info (for migration)."""
    store = _get_user_storage()
    user = store.get_user_by_username("testuser")
    if user is None:
        return None
    return {"user_id": user["user_id"], "username": user["username"]}
