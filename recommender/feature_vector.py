"""
Feature Vector — Converts a song's audio feature dict into a numpy array.
"""

import numpy as np

FEATURE_KEYS = ["tempo", "energy", "valence", "acousticness", "danceability"]
TEMPO_NORM_FACTOR = 250.0  # Normalize tempo to [0, 1] range


def build_feature_vector(features: dict) -> np.ndarray:
    """
    Build a normalized feature vector from a Spotify audio features dict.

    Tempo is normalized by dividing by TEMPO_NORM_FACTOR.
    Other features are already in [0, 1].
    """
    vector = []
    for key in FEATURE_KEYS:
        value = features.get(key, 0.0)
        if key == "tempo":
            value = value / TEMPO_NORM_FACTOR
        # Clamp to [0, 1]
        vector.append(min(max(float(value), 0.0), 1.0))
    return np.array(vector, dtype=np.float32)


def vector_keys() -> list[str]:
    return FEATURE_KEYS.copy()
