"""
YouTube Search Engine — Using yt-dlp to find songs and extract stream URLs.
"""

import yt_dlp
from core.song import Song
from search_engine.fuzzy_match import best_match, _score
import logging
import re
from typing import Tuple, Optional

# Language suffix map — appended to YT queries when a language lock is active
LANG_SUFFIX: dict[str, str] = {
    "ta": "Tamil",
    "hi": "Hindi",
    "te": "Telugu",
    "ml": "Malayalam",
    "kn": "Kannada",
}

# Configure yt-dlp options
YDL_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
    'skip_download': True,
    'force_generic_extractor': False,
    'default_search': 'ytsearch5',  # Search top 5 results
    'extractor_args': {'youtube': {'player_client': ['ios', 'android']}}, # Bypasses YouTube 403 block
}

class YTSearch:
    def __init__(self):
        self.ydl = yt_dlp.YoutubeDL(YDL_OPTS)

    def _execute_search(self, raw_query: str, search_string: str) -> Tuple[Optional[Song], float]:
        """
        Executes the search and returns a tuple: (Song object, score).
        If no match is found, returns (None, 0.0).
        """
        try:
            info = self.ydl.extract_info(f"ytsearch5:{search_string}", download=False)
            
            if not info or 'entries' not in info or not info['entries']:
                return None, 0.0
                
            candidates = []
            for entry in info['entries']:
                candidates.append({
                    'title': entry.get('title', ''),
                    'artist': entry.get('uploader', 'Unknown'),
                    'duration': int(entry.get('duration', 0)),
                    'video_id': entry.get('id', ''),
                    'stream_url': entry.get('url', ''),
                    'thumbnail': entry.get('thumbnail', ''),
                })
            
            best = best_match(raw_query, candidates)
            if best:
                score = _score(raw_query, best)
                song = Song(
                    title=best['title'],
                    artist=best['artist'],
                    duration=best['duration'],
                    video_id=best['video_id'],
                    stream_url=best['stream_url'],
                    thumbnail=best['thumbnail']
                )
                return song, score
                
        except Exception as e:
            logging.error(f"Search execute error: {e}")
            
        return None, 0.0

    def search(self, query: str, lang: str | None = None) -> Song | None:
        """
        Search YouTube for the query and return the best matching Song object.
        Implements a 4-Stage Iterative Search Fallback to guarantee success.
        """
        logging.info(f"Searching YouTube for: {query} [lang={lang}]")
        best_overall_song = None
        best_overall_score = -999.0

        lang_tag = LANG_SUFFIX.get(lang or "", "")
        
        # --- STAGE 1: Strict Audio Search ---
        already_qualified = any(kw in query.lower() for kw in ["official", "lyrics", "audio"])
        negative_filters = "-8d -slowed -sped -remix -cover"
        if any(term in query.lower() for term in ["8d", "slowed", "sped", "remix", "cover"]):
            negative_filters = ""

        if lang_tag and not already_qualified:
            strict_search_string = f"{query} {lang_tag} official audio {negative_filters}"
        elif already_qualified:
            strict_search_string = f"{query} {negative_filters}"
        else:
            strict_search_string = f"{query} official audio {negative_filters}"
        
        strict_search_string = strict_search_string.strip()
        
        logging.info(f"Stage 1 (Strict): {strict_search_string}")
        song1, score1 = self._execute_search(query, strict_search_string)
        if song1 and score1 > best_overall_score:
            best_overall_song, best_overall_score = song1, score1
            
        if best_overall_score > 180:
            logging.info(f"Stage 1 Winner: {song1.title} by {song1.artist} (Score: {score1:.1f})")
            return song1
            
        # --- STAGE 2: Raw Query Search ---
        raw_search_string = f"{query} {lang_tag}".strip()
        logging.info(f"Stage 2 (Raw): {raw_search_string}")
        
        song2, score2 = self._execute_search(query, raw_search_string)
        if song2 and score2 > best_overall_score:
            best_overall_song, best_overall_score = song2, score2

        if best_overall_score > 180:
            logging.info(f"Stage 2 Winner: {best_overall_song.title} by {best_overall_song.artist} (Score: {best_overall_score:.1f})")
            return best_overall_song
            
        # --- STAGE 3: Stop-Word Stripping ---
        # Remove noisy generic words that mess up YouTube's internal engine
        noisy_words = r'\b(song|from|movie|the|video|audio|lyrics|hd|hq)\b'
        stripped_query = re.sub(noisy_words, '', query, flags=re.IGNORECASE)
        stripped_query = re.sub(r'\s+', ' ', stripped_query).strip()
        
        if stripped_query and stripped_query.lower() != query.lower():
            stripped_search_string = f"{stripped_query} {lang_tag}".strip()
            logging.info(f"Stage 3 (Stripped): {stripped_search_string}")
            song3, score3 = self._execute_search(stripped_query, stripped_search_string)
            if song3 and score3 > best_overall_score:
                best_overall_song, best_overall_score = song3, score3

            if best_overall_score > 180:
                logging.info(f"Stage 3 Winner: {best_overall_song.title} by {best_overall_song.artist} (Score: {best_overall_score:.1f})")
                return best_overall_song

        # --- STAGE 4: LLM Query Extraction ---
        # If all mathematical matches fail to find a verified upload, ask the AI to translate the query.
        logging.warning(f"Math searches yielded weak score ({best_overall_score:.1f}). Triggering Stage 4 (LLM AI Extraction)...")
        try:
            from api.llm_client import get_llm_client
            llm_client = get_llm_client()
            ai_search_string = llm_client.extract_song_metadata(query)
            
            if ai_search_string:
                logging.info(f"Stage 4 (LLM Translated): '{ai_search_string}'")
                song4, score4 = self._execute_search(ai_search_string, ai_search_string)
                if song4 and score4 > best_overall_score:
                    best_overall_song, best_overall_score = song4, score4
                    
                if best_overall_score > 180:
                    logging.info(f"Stage 4 Winner: {best_overall_song.title} by {best_overall_song.artist} (Score: {best_overall_score:.1f})")
                    return best_overall_song
        except Exception as e:
            logging.error(f"Stage 4 LLM Error: {e}")

        # --- EXHAUSTED ---
        if best_overall_song:
            logging.info(f"Iterative search exhausted. Returning best result: {best_overall_song.title} by {best_overall_song.artist} (Score: {best_overall_score:.1f})")
            return best_overall_song
            
        logging.error(f"All 4 search stages completely failed to find a match for: {query}")
        return None

# Singleton instance
yt_search_engine = YTSearch()

def search_song(query: str, lang: str | None = None) -> Song | None:
    return yt_search_engine.search(query, lang=lang)
