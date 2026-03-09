"""
Fuzzy Matcher — Ranks search candidates using rapidfuzz to
handle typos, alternate spellings, and partial song names.

Example:
    query = "bling lites"
    candidates = [{"title": "Blinding Lights", "artist": "The Weeknd"}, ...]
    best = best_match(query, candidates)
    # -> {"title": "Blinding Lights", ...}
"""

from rapidfuzz import fuzz, process
from typing import Optional


# Penalty keywords: results containing these score lower unless the user
# explicitly asked for them.
_PENALTY_KEYWORDS = {"cover", "remix", "live", "karaoke", "tribute", "instrumental"}

# Preferred keywords boost a result's score.
_BOOST_KEYWORDS = {"official", "audio", "lyrics", "vevo"}


def _score(query: str, candidate: dict) -> float:
    """
    Compute a composite relevance score for a single candidate.

    Score is based on:
        - Token-set ratio of query vs "Title Artist" string
        - Bonus for official / audio / vevo tags in title
        - Penalty for cover / remix / live tags in title
    """
    label = f"{candidate.get('title', '')} {candidate.get('artist', '')}".lower()
    title_lower = candidate.get("title", "").lower()

    base = fuzz.token_set_ratio(query.lower(), label)

    # Apply bonuses
    bonus = sum(8 for kw in _BOOST_KEYWORDS if kw in title_lower)

    # Apply penalties
    penalty = sum(15 for kw in _PENALTY_KEYWORDS if kw in title_lower)

    return base + bonus - penalty


def best_match(query: str, candidates: list[dict]) -> Optional[dict]:
    """
    Return the best matching candidate dict from the list,
    or None if the list is empty.

    Args:
        query      : Raw user query string (typos allowed).
        candidates : List of candidate dicts with at least 'title' and 'artist'.

    Returns:
        The highest-scoring candidate dict, or None.
    """
    if not candidates:
        return None

    if len(candidates) == 1:
        return candidates[0]

    scored = [(c, _score(query, c)) for c in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[0][0]


def autocorrect_query(query: str, known_titles: list[str]) -> str:
    """
    Given a misspelled query and a list of known song titles,
    return the closest matching known title (if confidence > 70).

    Useful when searching a local history or cache.

    Args:
        query        : User's raw query (may contain typos).
        known_titles : List of exact song title strings to match against.

    Returns:
        The best matching known title, or the original query if no good match.
    """
    if not known_titles:
        return query

    result = process.extractOne(query, known_titles, scorer=fuzz.token_set_ratio)
    if result and result[1] >= 70:
        return result[0]
    return query
