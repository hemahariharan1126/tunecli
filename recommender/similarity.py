"""
Similarity — Cosine similarity calculation between song feature vectors.
"""

import numpy as np


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Compute cosine similarity between two feature vectors.
    Returns a float in [0, 1] where 1.0 is identical.
    """
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


def rank_by_similarity(
    target_vec: np.ndarray,
    candidates: list[tuple[str, np.ndarray]],
    top_n: int = 10,
) -> list[tuple[str, float]]:
    """
    Rank a list of (song_id, feature_vector) candidates by similarity
    to the target_vec.

    Returns:
        List of (song_id, similarity_score) sorted descending.
    """
    scored = [
        (song_id, cosine_similarity(target_vec, vec))
        for song_id, vec in candidates
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_n]
