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


# --- Technique tips for in-game contextual help ---

_TECHNIQUE_TIPS = [
    {
        "technique": "scanning",
        "title": "Scanning",
        "description": "Check each row, column, and box for missing numbers. If 8 of 9 numbers are present, the missing one is obvious.",
        "level": "beginner",
        "how_to_find": "Look for rows, columns, or boxes with the most filled cells. The more numbers present, the easier to spot the missing one.",
        "lesson_id": "scanning",
    },
    {
        "technique": "naked-singles",
        "title": "Naked Singles",
        "description": "When a cell has only one possible candidate, that's the answer. Check row, column, and box to eliminate options.",
        "level": "beginner",
        "how_to_find": "Look for cells surrounded by many filled numbers. Cross-reference the row, column, and box to see what's left.",
        "lesson_id": "naked-singles",
    },
    {
        "technique": "hidden-singles",
        "title": "Hidden Singles",
        "description": "When a number can only go in one cell within a row, column, or box, that's where it belongs.",
        "level": "beginner",
        "how_to_find": "For each number 1-9, scan each row/column/box and count how many cells could hold it. If only one, that's your move.",
        "lesson_id": "hidden-singles",
    },
    {
        "technique": "naked-pairs",
        "title": "Naked Pairs",
        "description": "Two cells with the same two candidates lock those numbers. Eliminate them from other cells in that unit.",
        "level": "intermediate",
        "how_to_find": "Use auto-notes to fill pencil marks, then look for two cells in the same unit with identical pairs of candidates.",
        "lesson_id": "naked-pairs",
    },
    {
        "technique": "hidden-pairs",
        "title": "Hidden Pairs",
        "description": "When two numbers can only go in the same two cells, those cells are locked to those numbers.",
        "level": "intermediate",
        "how_to_find": "For each pair of numbers, check if they share the same two candidate cells in a row, column, or box.",
        "lesson_id": "hidden-pairs",
    },
    {
        "technique": "pointing-pairs",
        "title": "Pointing Pairs",
        "description": "When a number's candidates in a box are all in one row/column, eliminate it from the rest of that row/column.",
        "level": "intermediate",
        "how_to_find": "For each box, check if any number's candidates are all in the same row or column within the box.",
        "lesson_id": "pointing-pairs",
    },
    {
        "technique": "x-wing",
        "title": "X-Wing",
        "description": "When a number has exactly two candidates in two rows aligned in the same columns, eliminate from other cells in those columns.",
        "level": "advanced",
        "how_to_find": "Look for numbers with very few candidates per row. Check if two rows have candidates in the same two columns.",
        "lesson_id": "x-wing",
    },
    {
        "technique": "xy-wing",
        "title": "XY-Wing",
        "description": "Three bivalue cells forming a pivot-wing pattern can eliminate candidates from cells seeing both wings.",
        "level": "advanced",
        "how_to_find": "Find bivalue cells (2 candidates). Check if one (pivot) shares units with two others that have a common candidate.",
        "lesson_id": "xy-wing",
    },
    {
        "technique": "unique-rectangle",
        "title": "Unique Rectangle",
        "description": "Exploit the one-solution rule: if four cells forming a rectangle would create two solutions, eliminate the impossible candidate.",
        "level": "expert",
        "how_to_find": "Look for four cells forming a rectangle where three have the same two candidates. The fourth must have another option.",
        "lesson_id": "unique-rectangle",
    },
    {
        "technique": "coloring",
        "title": "Coloring",
        "description": "Track conjugate pairs with alternating colors to find contradictions and eliminate candidates.",
        "level": "expert",
        "how_to_find": "Pick a number with few candidates. Find conjugate pairs and color them alternately. Same-colored cells in one unit = contradiction.",
        "lesson_id": "coloring",
    },
]


def get_technique_tips(level=None):
    """Return technique tips, optionally filtered by level."""
    if level:
        return [t for t in _TECHNIQUE_TIPS if t["level"] == level]
    return _TECHNIQUE_TIPS


def get_technique(technique_id):
    """Return a single technique by ID, or None if not found."""
    for t in _TECHNIQUE_TIPS:
        if t["technique"] == technique_id:
            return t
    return None


def get_tutorial_stats(progress):
    """Calculate tutorial statistics from progress data."""
    content = load_content()
    total = len(content["lessons"])
    completed = len(progress.get("completed_lessons", []))

    level_progress = {}
    for level in ["beginner", "intermediate", "advanced", "expert"]:
        level_lessons = [l for l in content["lessons"] if l["level"] == level]
        level_total = len(level_lessons)
        level_completed = len([l for l in level_lessons if l["id"] in progress.get("completed_lessons", [])])
        level_progress[level] = {
            "total": level_total,
            "completed": level_completed,
            "rate": (level_completed / level_total * 100) if level_total > 0 else 0,
        }

    return {
        "total_lessons": total,
        "completed_lessons": completed,
        "completion_rate": (completed / total * 100) if total > 0 else 0,
        "level_progress": level_progress,
        "completed_steps": len(progress.get("completed_steps", [])),
    }
