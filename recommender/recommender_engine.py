"""
Recommender Engine — Orchestrates feature vectors, clustering, mood filters,
and cosine similarity to generate the final recommendation queue.
"""

import numpy as np
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0  # Ensure deterministic results

from recommender.feature_vector import build_feature_vector
from recommender.similarity import rank_by_similarity
from recommender.mood_filter import filter_by_mood
from recommender.clustering import SongClusterer
from api.audio_features import AudioFeatureService


class RecommenderEngine:
    def __init__(self):
        self._feature_service = AudioFeatureService()
        self._clusterer = SongClusterer()
        self._song_library: list[dict] = []   # list of enriched song dicts
        self._vectors: list[np.ndarray] = []
        self._library_fitted = False

    def load_library(self, songs: list[dict]):
        """
        Load a list of song feature dicts into the engine and fit clustering.
        Each dict must contain the keys from feature_vector.FEATURE_KEYS.
        """
        self._song_library = songs
        self._vectors = [build_feature_vector(s) for s in songs]
        if len(songs) >= 5:
            matrix = np.stack(self._vectors)
            self._clusterer.fit(matrix)
            self._library_fitted = True

    def recommend(
        self,
        seed_query: str,
        mood: str | None = None,
        top_n: int = 10,
    ) -> list[dict]:
        """
        Generate a ranked recommendation list based on a seed song.

        Args:
            seed_query: Song name/artist to base recommendations on.
            mood: Optional mood filter ('sad', 'chill', 'party', 'focus').
            top_n: Number of recommendations to return.

        Returns:
            List of ranked song feature dicts.
        """
        seed_features = self._feature_service.get_features(seed_query)
        if not seed_features:
            return []

        seed_vec = build_feature_vector(seed_features)

        # Restrict search to same cluster if library is fitted
        candidates = list(enumerate(self._vectors))
        if self._library_fitted:
            cluster_id = self._clusterer.predict_cluster(seed_vec)
            indices = self._clusterer.get_cluster_indices(cluster_id)
            candidates = [(i, self._vectors[i]) for i in indices]

        ranked = rank_by_similarity(
            seed_vec,
            [(str(i), vec) for i, vec in candidates],
            top_n=top_n,
        )

        result_songs = [self._song_library[int(idx)] for idx, _ in ranked]

        if mood:
            result_songs = filter_by_mood(result_songs, mood)

        return result_songs

    def detect_language(self, text: str) -> str:
        """
        Detect the language of a title/artist string.
        Includes heuristics for non-Latin Indian scripts and regional keywords.
        """
        if not text:
            return "en"
            
        lower_text = text.lower()
        
        # 1. Script-based heuristic (highly reliable)
        if any('\u0b80' <= c <= '\u0bff' for c in text): return "ta" # Tamil
        if any('\u0900' <= c <= '\u097f' for c in text): return "hi" # Hindi
        
        # 2. Keyword-based boosting for Latin-script regional titles
        tamil_keywords = ['tamil', 'kuthu', 'anirudh', 'ar rahman', 'vijay', 'ajith', 'yuvan']
        hindi_keywords = ['hindi', 'bollywood', 'arijit', 'shreya ghoshal', 'kumarsanu', 'kesariya']
        
        if any(kw in lower_text for kw in tamil_keywords):
            return "ta"
        if any(kw in lower_text for kw in hindi_keywords):
            return "hi"
            
        # 3. General detection using langdetect
        try:
            detected = detect(text)
            # langdetect often confuses short Tamil/Hindi strings with Indonesian (id) or Somali (so)
            if detected in ['id', 'so', 'tl', 'af'] and (" " not in text or len(text) < 30):
                return "ta" # Statistical bias for the user's likely regional context
            return detected
        except:
            return "en"

    def get_spotify_recommendations(self, seed_query: str, limit: int = 5, target_lang: str | None = None) -> list[dict]:
        """
        Get high-quality recommendations, optionally filtered by language.
        Falls back to YTMusic if Spotify is blocked.
        """
        try:
            # 1. Get recommendations from Spotify
            seed_data = self._feature_service.get_features(seed_query)
            if not seed_data or "id" not in seed_data:
                raise Exception("Could not find seed track on Spotify.")

            sp_client = self._feature_service._spotify
            recs = sp_client.get_recommendations(seed_track_ids=[seed_data["id"]], limit=limit * 2) # Get extra for filtering

            if not recs:
                raise Exception("Spotify returned no recommendations.")

            formatted = [{"title": r["name"], "artist": r["artist"]} for r in recs]
            
            # 2. Apply Language Guard
            if target_lang:
                filtered = []
                for r in formatted:
                    text_to_check = f"{r['title']} {r['artist']}"
                    if self.detect_language(text_to_check) == target_lang:
                        filtered.append(r)
                return filtered[:limit]
            
            return formatted[:limit]

        except Exception as e:
            # Log the Spotify failure and fall back to YTMusic
            import logging
            logging.warning(f"Spotify recommendation failed ({e}). Falling back to YTMusic...")
            
            # Use YTMusic as fallback
            from api.ytmusic_client import YTMusicClient
            yt_client = YTMusicClient()
            
            from player.playback_controller import get_controller
            current_song = get_controller().queue_manager.now_playing()
            
            if current_song:
                vid = getattr(current_song, 'video_id', None)
                if vid:
                    logging.info(f"Fallback: Searching YTMusic recommendations for video_id: {vid}")
                    recs = yt_client.get_recommendations(vid)
                    if recs:
                        logging.info(f"Fallback: Found {len(recs)} tracks on YTMusic.")
                        formatted = [{"title": r["title"], "artist": r["artist"]} for r in recs]
                        
                        # Apply Language Guard to fallback
                        if target_lang:
                            filtered = [r for r in formatted if self.detect_language(f"{r['title']} {r['artist']}") == target_lang]
                            return filtered[:limit]
                        
                        return formatted[:limit]
                    else:
                        logging.warning("Fallback: YTMusic returned no recommendations.")
                else:
                    logging.warning("Fallback: Current song has no video_id.")
            else:
                logging.warning("Fallback: No song currently playing in controller.")
            
            return []
