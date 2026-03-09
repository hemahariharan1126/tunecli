"""
Helpers — General utility functions shared across TuneCLI modules.
"""

import json
import os


def ms_to_mmss(milliseconds: int) -> str:
    """Convert milliseconds to a MM:SS string."""
    total_seconds = milliseconds // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"


def seconds_to_mmss(seconds: int) -> str:
    """Convert seconds to a MM:SS string."""
    m = seconds // 60
    s = seconds % 60
    return f"{m}:{s:02d}"


def load_json(path: str, default=None):
    """Load a JSON file, return default if missing."""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else {}


def save_json(path: str, data):
    """Save data to a JSON file, creating parent dirs as needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
