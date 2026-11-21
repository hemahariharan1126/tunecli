"""
Recommender Engine — Orchestrates candidate retrieval, persistent storage,
feature vectors, clustering, mood filters, and cosine similarity.
"""

import os
import json
import logging
import numpy as np
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0  # Ensure deterministic results

from recommender.feature_vector import build_feature_vector
from recommender.similarity import rank_by_similarity
from recommender.mood_filter import filter_by_mood
from recommender.clustering import SongClusterer
from api.audio_features import AudioFeatureService
from config import HISTORY_CACHE


class RecommenderEngine:
    def __init__(self):
        self._feature_service = AudioFeatureService()
        self._clusterer = SongClusterer()
        self._song_library: list[dict] = []   # list of enriched song dicts
        self._vectors: list[np.ndarray] = []
        self._library_fitted = False
        self._load_persistent_candidates()

    def _load_persistent_candidates(self) -> None:
        """
        Loads tracks from history and cached features to pre-populate
        the local candidate library on startup.
        """
        candidates = []
        # Check history cache
        history_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".history.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    entries = json.load(f)
                    for item in entries:
                        if item.get("title"):
                            candidates.append({
                                "title": item["title"],
                                "artist": item.get("artist", "Unknown"),
                                "genre": item.get("genre", "general"),
                            })
            except Exception as e:
                logging.debug(f"[Recommender] History load note: {e}")

        # Also load from song_features_cache if present
        if hasattr(self._feature_service, "_cache") and self._feature_service._cache:
            for query, feat in self._feature_service._cache.items():
                if isinstance(feat, dict):
                    candidates.append({
                        "title": query,
                        "artist": feat.get("artist", "Unknown"),
                        **feat
                    })

        if candidates:
            # Deduplicate by title
            unique_map = {}
            for c in candidates:
                key = c["title"].lower().strip()
                if key not in unique_map:
                    unique_map[key] = c
            self.load_library(list(unique_map.values()))

    def load_library(self, songs: list[dict]):
        """
        Load a list of song feature dicts into the engine and fit clustering.
        Each dict may contain audio feature keys, or defaults will be applied safely.
        """
        self._song_library = songs
        self._vectors = [build_feature_vector(s) for s in songs]
        if len(songs) >= 5:
            try:
                matrix = np.stack(self._vectors)
                self._clusterer.fit(matrix)
                self._library_fitted = True
            except Exception as e:
                logging.debug(f"[Recommender] Cluster fit note: {e}")
                self._library_fitted = False

    def recommend(
        self,
        seed_query: str,
        mood: str | None = None,
        top_n: int = 10,
    ) -> list[dict]:
        """
        Generate a ranked recommendation list based on a seed song.
        Falls back to YTMusic or LLM recommendations if the local library is sparse.
        """
        # If candidate library is sparse, fetch via external API pipeline
        if len(self._song_library) < 3:
            return self.get_spotify_recommendations(seed_query, limit=top_n)

        # 1. Check if seed song exists directly in candidate library
        seed_vec = None
        for i, s in enumerate(self._song_library):
            if s.get("title", "").lower().strip() == seed_query.lower().strip():
                seed_vec = self._vectors[i]
                break

        # 2. If not in candidate library, check audio features service or default
        if seed_vec is None:
            seed_features = self._feature_service.get_features(seed_query)
            if not seed_features:
                seed_vec = build_feature_vector({"tempo": 120.0, "energy": 0.5, "valence": 0.5})
            else:
                seed_vec = build_feature_vector(seed_features)

        # Restrict search to same cluster if library is fitted
        candidates = list(enumerate(self._vectors))
        if self._library_fitted and len(candidates) >= 5:
            try:
                cluster_id = self._clusterer.predict_cluster(seed_vec)
                indices = self._clusterer.get_cluster_indices(cluster_id)
                if indices:
                    candidates = [(i, self._vectors[i]) for i in indices]
            except Exception:
                pass

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

        # 1. Script-based heuristic (highest reliability — unambiguous Unicode ranges)
        if any('\u0b80' <= c <= '\u0bff' for c in text): return "ta"  # Tamil script
        if any('\u0900' <= c <= '\u097f' for c in text): return "hi"  # Devanagari (Hindi/Marathi)
        if any('\u0c00' <= c <= '\u0c7f' for c in text): return "te"  # Telugu script
        if any('\u0d00' <= c <= '\u0d7f' for c in text): return "ml"  # Malayalam script
        if any('\u0c80' <= c <= '\u0cff' for c in text): return "kn"  # Kannada script

        # 2. Keyword-based boosting for Latin-script regional content
        tamil_keywords = [
            'tamil', 'kollywood', 'kuthu', 'gaana', 'kolaveri', 'tamil album',
            'tamil songs', 'tamil hits', 'tamil movie',
            'anirudh', 'anirudh ravichander', 'ar rahman', 'yuvan', 'yuvan shankar raja',
            'harris jayaraj', 'devi sri prasad', 'dsp', 'santhosh narayanan',
            'gv prakash', 'sean roldan', 'd imman', 'ilaiyaraaja', 'ilayaraja',
            'james vasanthan', 'karthik raja', 'vidyasagar',
            'sid sriram', 'haricharan', 'vijay prakash', 'karthik singer',
            'chinmayi', 'tippu', 'benny dayal',
            'vijay thalapathy', 'thalapathy', 'thala ajith', 'thala',
            'rajinikanth', 'rajini', 'kamal haasan', 'kamal',
            'vikram', 'suriya', 'sivakarthikeyan', 'simbu', 'str',
            'vijay sethupathi', 'dhanush', 'nayanthara',
        ]

        hindi_keywords = [
            'hindi', 'bollywood', 'hindi songs', 'hindi album', 'hindi movie',
            'filmi', 'desi beats',
            'pritam', 'vishal shekhar', 'amit trivedi', 'shankar ehsaan loy',
            'a r rahman hindi', 'sajid wajid', 'meet bros', 'tanishk bagchi',
            'arijit singh', 'shreya ghoshal', 'sonu nigam', 'udit narayan',
            'lata mangeshkar', 'kishore kumar', 'kumar sanu', 'alka yagnik',
            'atif aslam', 'badshah', 'yo yo honey singh', 'neha kakkar',
            'armaan malik', 'jubin nautiyal', 'darshan raval',
            'kesariya', 'tum hi ho', 'raabta', 'dilwale', 'kabir singh',
        ]

        telugu_keywords = [
            'telugu', 'tollywood', 'devi sri prasad telugu', 'ss thaman',
            'thaman', 'mahesh babu', 'allu arjun', 'prabhas', 'ram charan',
        ]

        malayalam_keywords = [
            'malayalam', 'mollywood', 'ouseppachan', 'vidyasagar malayalam',
            'mohanlal', 'mammootty',
        ]

        if any(kw in lower_text for kw in tamil_keywords):
            return "ta"
        if any(kw in lower_text for kw in hindi_keywords):
            return "hi"
        if any(kw in lower_text for kw in telugu_keywords):
            return "te"
        if any(kw in lower_text for kw in malayalam_keywords):
            return "ml"

        # 3. Statistical detection via langdetect
        try:
            detected = detect(text)
            if detected in ['id', 'so', 'tl', 'af', 'sw'] and len(text.split()) <= 5:
                return "ta"
            return detected
        except Exception:
            return "en"

    def get_spotify_recommendations(self, seed_query: str, limit: int = 5, target_lang: str | None = None, seed_video_id: str | None = None) -> list[dict]:
        """
        Get high-quality recommendations, optionally filtered by language.
        Tries Spotify -> YTMusic -> LLM Fallback gracefully.
        """
        try:
            # 1. Try Spotify if available
            if not self._feature_service.is_available:
                raise Exception("Spotify integration disabled or restricted.")
                
            seed_data = self._feature_service.get_features(seed_query)
            if not seed_data or "id" not in seed_data:
                raise Exception("Could not find seed track on Spotify.")

            sp_client = self._feature_service._spotify
            recs = sp_client.get_recommendations(seed_track_ids=[seed_data["id"]], limit=limit * 2)

            if not recs:
                raise Exception("Spotify returned no recommendations.")

            formatted = [{"title": r["name"], "artist": r["artist"]} for r in recs]
            
            # Apply Language Guard
            if target_lang:
                filtered = []
                for r in formatted:
                    text_to_check = f"{r['title']} {r['artist']}"
                    if self.detect_language(text_to_check) == target_lang:
                        filtered.append(r)
                return filtered[:limit]
            
            return formatted[:limit]

        except Exception as e:
            # Fall back to YTMusic
            logging.info(f"[Recommender] Spotify skipped/failed ({e}). Falling back to YTMusic...")
            
            from api.ytmusic_client import YTMusicClient
            yt_client = YTMusicClient()
            
            if not seed_video_id:
                found_song = yt_client.search_song(seed_query)
                if found_song:
                    seed_video_id = found_song.get("video_id")

            if seed_video_id:
                logging.info(f"[Recommender] Searching YTMusic related tracks for video_id: {seed_video_id}")
                recs = yt_client.get_recommendations(seed_video_id, limit=limit * 2)
                if recs:
                    formatted = [{"title": r["title"], "artist": r["artist"]} for r in recs]
                    if target_lang:
                        filtered = [r for r in formatted if self.detect_language(f"{r['title']} {r['artist']}") == target_lang]
                        if filtered:
                            return filtered[:limit]
                    return formatted[:limit]
            
            # 3. Tertiary LLM Fallback
            logging.info("[Recommender] Engaging LLM Fallback Recommender...")
            from api.llm_client import get_llm_client
            llm_client = get_llm_client()
            llm_recs = llm_client.get_similar_songs(seed_query, target_lang, limit=limit)
            
            if llm_recs:
                return llm_recs[:limit]
            
            return []
