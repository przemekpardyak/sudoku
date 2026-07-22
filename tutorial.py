"""
Tutorial system module.
Manages tutorial content, progress tracking, and lesson delivery.
"""
import json
import os
from pathlib import Path

# Load tutorial content from JSON file
CONTENT_PATH = Path(__file__).parent / "tutorials" / "content.json"

_content_cache = None


def load_content():
    """Load tutorial content from JSON file, with caching."""
    global _content_cache
    if _content_cache is None:
        with open(CONTENT_PATH) as f:
            _content_cache = json.load(f)
    return _content_cache


def get_all_lessons():
    """Return all lessons as a list of summaries (without full steps)."""
    content = load_content()
    lessons = []
    for lesson in content["lessons"]:
        lessons.append({
            "id": lesson["id"],
            "title": lesson["title"],
            "level": lesson["level"],
            "description": lesson["description"],
            "order": lesson["order"],
        })
    # Sort by order
    lessons.sort(key=lambda l: l["order"])
    return lessons


def get_lesson(lesson_id):
    """Return a single lesson by ID, or None if not found."""
    content = load_content()
    for lesson in content["lessons"]:
        if lesson["id"] == lesson_id:
            return lesson
    return None


def get_lessons_by_level(level):
    """Return lessons filtered by skill level."""
    content = load_content()
    lessons = [l for l in content["lessons"] if l["level"] == level]
    lessons.sort(key=lambda l: l["order"])
    return lessons


def get_progress_storage_key(user_id):
    """Return the Firestore/storage key for tutorial progress."""
    return f"tutorial_progress:{user_id}"


def get_initial_progress():
    """Return empty progress state for a new user."""
    return {
        "completed_lessons": [],
        "completed_steps": [],
        "started_lessons": [],
    }
