"""
Global configuration and environment variable loader for TuneCLI.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Spotify ──────────────────────────────────────────────
SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_REDIRECT_URI: str = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")

# ── Gemini (LLM) ─────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

# ── Audio Quality Thresholds (Mbps) ──────────────────────
QUALITY_HIGH_THRESHOLD: float = 20.0
QUALITY_MEDIUM_THRESHOLD: float = 10.0

QUALITY_MAP: dict = {
    "high": "bestaudio[abr<=320]",
    "medium": "bestaudio[abr<=128]",
    "low": "worstaudio",
}

# ── Cache Paths ───────────────────────────────────────────
CACHE_DIR: str = "cache"
SONG_FEATURES_CACHE: str = f"{CACHE_DIR}/song_features.json"
HISTORY_CACHE: str = f"{CACHE_DIR}/history.json"

# ── Database Paths ────────────────────────────────────────
DATABASE_DIR: str = "database"
SONGS_DB: str = f"{DATABASE_DIR}/songs.db"
PREFERENCES_DB: str = f"{DATABASE_DIR}/user_preferences.db"

# ── Mood Feature Mapping ──────────────────────────────────
MOOD_MAP: dict = {
    "sad":     {"valence": (0.0, 0.3), "energy": (0.0, 0.4)},
    "chill":   {"valence": (0.3, 0.6), "energy": (0.0, 0.5)},
    "party":   {"valence": (0.6, 1.0), "energy": (0.7, 1.0)},
    "focus":   {"valence": (0.3, 0.6), "energy": (0.2, 0.5)},
    "romantic":{"valence": (0.5, 0.8), "energy": (0.2, 0.6)},
}

# ── K-Means Clustering ────────────────────────────────────
N_CLUSTERS: int = 5
