"""
Spotify API Client — Handles authentication and song/feature retrieval gracefully.
Resilient to missing credentials and 403 Forbidden on developer accounts.
"""

import logging
from typing import Optional
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET


class SpotifyClient:
    def __init__(self):
        self._sp = None
        self._is_active = False

        if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
            logging.info("[SpotifyClient] Credentials not configured; running without Spotify.")
            return

        try:
            import spotipy
            from spotipy.oauth2 import SpotifyClientCredentials
            auth_manager = SpotifyClientCredentials(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
            )
            self._sp = spotipy.Spotify(auth_manager=auth_manager, requests_timeout=8)
            self._is_active = True
        except Exception as e:
            logging.warning(f"[SpotifyClient] Authentication failed ({e}). Disabling Spotify integration.")
            self._is_active = False

    def is_available(self) -> bool:
        """Returns True if Spotify client is authenticated and functional."""
        return self._is_active and self._sp is not None

    def search_song(self, query: str) -> Optional[dict]:
        """
        Search Spotify for a song by name/artist.
        Returns the top result as a dict or None on error/not found.
        """
        if not self.is_available():
            return None

        try:
            results = self._sp.search(q=query, limit=1, type="track")
            items = results.get("tracks", {}).get("items", [])
            if not items:
                return None
            track = items[0]
            return {
                "id": track["id"],
                "name": track["name"],
                "artist": track["artists"][0]["name"],
                "album": track["album"]["name"],
                "duration_ms": track["duration_ms"],
            }
        except Exception as e:
            logging.warning(f"[SpotifyClient] search_song failed ({e}).")
            if "403" in str(e):
                self._is_active = False
            return None

    def get_audio_features(self, track_id: str) -> Optional[dict]:
        """
        Fetch Spotify audio features for a given track ID.
        Returns features dict or None if unavailable.
        """
        if not self.is_available():
            return None

        try:
            features = self._sp.audio_features([track_id])
            if not features or features[0] is None:
                return None
            f = features[0]
            return {
                "tempo":        f.get("tempo", 120.0),
                "energy":       f.get("energy", 0.5),
                "valence":      f.get("valence", 0.5),
                "acousticness": f.get("acousticness", 0.5),
                "danceability": f.get("danceability", 0.5),
                "loudness":     f.get("loudness", -8.0),
                "speechiness":  f.get("speechiness", 0.1),
                "liveness":     f.get("liveness", 0.1),
            }
        except Exception as e:
            logging.warning(f"[SpotifyClient] audio_features failed ({e}). Disabling audio feature calls.")
            if "403" in str(e):
                self._is_active = False
            return None

    def get_recommendations(self, seed_track_ids: list[str], limit: int = 10) -> list[dict]:
        """Fetch recommendations from Spotify given seed track IDs."""
        if not self.is_available():
            return []

        try:
            results = self._sp.recommendations(seed_tracks=seed_track_ids[:5], limit=limit)
            tracks = results.get("tracks", [])
            return [
                {
                    "name":   t["name"],
                    "artist": t["artists"][0]["name"] if t.get("artists") else "Unknown",
                    "id":     t["id"],
                }
                for t in tracks
            ]
        except Exception as e:
            logging.warning(f"[SpotifyClient] get_recommendations failed ({e}).")
            if "403" in str(e):
                self._is_active = False
            return []
