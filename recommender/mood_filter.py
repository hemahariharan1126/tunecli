"""
Mood Filter — Filters a list of songs by mood-defined audio feature ranges.
"""

from config import MOOD_MAP


def filter_by_mood(songs: list[dict], mood: str) -> list[dict]:
    """
    Filter a list of song feature dicts by a named mood.

    Args:
        songs: List of dicts, each containing 'valence' and 'energy' keys.
        mood: One of the keys defined in config.MOOD_MAP.

    Returns:
        Filtered list matching mood constraints.
    """
    if mood not in MOOD_MAP:
        return songs  # Return all if mood unknown

    mood_ranges = MOOD_MAP[mood]
    result = []
    for song in songs:
        match = all(
            low <= song.get(feature, 0.0) <= high
            for feature, (low, high) in mood_ranges.items()
        )
        if match:
            result.append(song)
    return result
