"""
Spotify API Client — Handles authentication and song/feature retrieval.
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET


class SpotifyClient:
    def __init__(self):
        auth_manager = SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
        )
        self._sp = spotipy.Spotify(auth_manager=auth_manager)

    def search_song(self, query: str) -> dict | None:
        """
        Search Spotify for a song by name/artist.

        Returns the top result as a dict with keys:
            id, name, artist, album, duration_ms
        """
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

    def get_audio_features(self, track_id: str) -> dict | None:
        """
        Fetch Spotify audio features for a given track ID.

        Returns a dict with float values for:
            tempo, energy, valence, acousticness,
            danceability, loudness, speechiness, liveness
        """
        features = self._sp.audio_features([track_id])
        if not features or features[0] is None:
            return None
        f = features[0]
        return {
            "tempo":        f["tempo"],
            "energy":       f["energy"],
            "valence":      f["valence"],
            "acousticness": f["acousticness"],
            "danceability": f["danceability"],
            "loudness":     f["loudness"],
            "speechiness":  f["speechiness"],
            "liveness":     f["liveness"],
        }

    def get_recommendations(self, seed_track_ids: list, limit: int = 5) -> list[dict]:
        """
        Get similar/related tracks from Spotify based on seed track IDs.
        Returns a list of dicts with 'name' and 'artist'.
        """
        try:
            results = self._sp.recommendations(seed_tracks=seed_track_ids, limit=limit)
            recommended = []
            for track in results.get("tracks", []):
                recommended.append({
                    "name": track["name"],
                    "artist": track["artists"][0]["name"],
                })
            return recommended
        except Exception as e:
            # logging isn't imported here, but we should handle it
            print(f"Spotify recommendation error: {e}")
            return []
