"""
Audio Features — Bridges Spotify feature extraction with local caching.
"""

import json
import os
from api.spotify_client import SpotifyClient
from config import SONG_FEATURES_CACHE


class AudioFeatureService:
    def __init__(self):
        self.is_available = True
        try:
            self._spotify = SpotifyClient()
        except Exception as e:
            import logging
            logging.warning(f"SpotifyClient disabled: {e}")
            self.is_available = False
        
        self._cache: dict = self._load_cache()

    def _load_cache(self) -> dict:
        if os.path.exists(SONG_FEATURES_CACHE):
            with open(SONG_FEATURES_CACHE, "r") as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        os.makedirs(os.path.dirname(SONG_FEATURES_CACHE), exist_ok=True)
        with open(SONG_FEATURES_CACHE, "w") as f:
            json.dump(self._cache, f, indent=2)

    def get_features(self, song_query: str) -> dict | None:
        """
        Return audio features for a song, using cache when available.
        Falls back to Spotify API if not cached.
        """
        if song_query in self._cache:
            return self._cache[song_query]

        if not self.is_available:
            return None

        track = self._spotify.search_song(song_query)
        if not track:
            return None

        features = self._spotify.get_audio_features(track["id"])
        if not features:
            return None

        result = {**track, **features}
        self._cache[song_query] = result
        self._save_cache()
        return result
