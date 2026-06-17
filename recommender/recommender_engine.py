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

        # 1. Script-based heuristic (highest reliability — unambiguous Unicode ranges)
        if any('\u0b80' <= c <= '\u0bff' for c in text): return "ta"  # Tamil script
        if any('\u0900' <= c <= '\u097f' for c in text): return "hi"  # Devanagari (Hindi/Marathi)
        if any('\u0c00' <= c <= '\u0c7f' for c in text): return "te"  # Telugu script
        if any('\u0d00' <= c <= '\u0d7f' for c in text): return "ml"  # Malayalam script
        if any('\u0c80' <= c <= '\u0cff' for c in text): return "kn"  # Kannada script

        # 2. Keyword-based boosting for Latin-script regional content
        #    (covers cases where artist/title is romanised Tamil/Hindi)
        tamil_keywords = [
            # Genre & language tags
            'tamil', 'kollywood', 'kuthu', 'gaana', 'kolaveri', 'tamil album',
            'tamil songs', 'tamil hits', 'tamil movie',
            # Composers / Music Directors
            'anirudh', 'anirudh ravichander', 'ar rahman', 'yuvan', 'yuvan shankar raja',
            'harris jayaraj', 'devi sri prasad', 'dsp', 'santhosh narayanan',
            'gv prakash', 'sean roldan', 'd imman', 'ilaiyaraaja', 'ilayaraja',
            'james vasanthan', 'karthik raja', 'vidyasagar',
            # Singers
            'sid sriram', 'haricharan', 'vijay prakash', 'karthik singer',
            'chinmayi', 'tippu', 'benny dayal',
            # Actors / Directors (whose names appear in song titles)
            'vijay thalapathy', 'thalapathy', 'thala ajith', 'thala',
            'rajinikanth', 'rajini', 'kamal haasan', 'kamal',
            'vikram', 'suriya', 'sivakarthikeyan', 'simbu', 'str',
            'vijay sethupathi', 'dhanush', 'nayanthara',
        ]

        hindi_keywords = [
            # Genre & language tags
            'hindi', 'bollywood', 'hindi songs', 'hindi album', 'hindi movie',
            'filmi', 'desi beats',
            # Composers
            'pritam', 'vishal shekhar', 'amit trivedi', 'shankar ehsaan loy',
            'a r rahman hindi', 'sajid wajid', 'meet bros', 'tanishk bagchi',
            # Singers
            'arijit singh', 'shreya ghoshal', 'sonu nigam', 'udit narayan',
            'lata mangeshkar', 'kishore kumar', 'kumar sanu', 'alka yagnik',
            'atif aslam', 'badshah', 'yo yo honey singh', 'neha kakkar',
            'armaan malik', 'jubin nautiyal', 'darshan raval',
            # Song/film keywords
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
            # langdetect frequently mis-classifies short Indian-language romanisations
            # as Indonesian (id), Somali (so), Tagalog (tl), or Afrikaans (af).
            # Apply a conservative Tamil bias for ambiguous short strings.
            if detected in ['id', 'so', 'tl', 'af', 'sw'] and len(text.split()) <= 5:
                return "ta"
            return detected
        except Exception:
            return "en"

    def get_spotify_recommendations(self, seed_query: str, limit: int = 5, target_lang: str | None = None, seed_video_id: str | None = None) -> list[dict]:
        """
        Get high-quality recommendations, optionally filtered by language.
        Falls back to YTMusic if Spotify is blocked.
        """
        try:
            # 1. Get recommendations from Spotify
            if not self._feature_service.is_available:
                raise Exception("Spotify integration disabled (missing API keys).")
                
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
            
            if seed_video_id:
                logging.info(f"Fallback: Searching YTMusic recommendations for video_id: {seed_video_id}")
                recs = yt_client.get_recommendations(seed_video_id)
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
                logging.warning("Fallback: No seed_video_id provided.")
            
            # 3. Tertiary LLM Fallback
            logging.warning("APIs failed. Engaging LLM Fallback Recommender...")
            from api.llm_client import get_llm_client
            llm_client = get_llm_client()
            llm_recs = llm_client.get_similar_songs(seed_query, target_lang, limit=limit)
            
            if llm_recs:
                logging.info(f"LLM Fallback generated {len(llm_recs)} recommendations.")
                return llm_recs[:limit]
            
            logging.error("LLM Fallback also failed.")
            return []
