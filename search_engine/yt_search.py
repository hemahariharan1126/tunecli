"""
YouTube Search Engine — Using yt-dlp to find songs and extract stream URLs.
"""

import yt_dlp
from core.song import Song
from search_engine.fuzzy_match import best_match
import logging

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

    def search(self, query: str) -> Song | None:
        """
        Search YouTube for the query and return the best matching Song object.
        """
        try:
            logging.info(f"Searching YouTube for: {query}")
            # Add "official audio" to help narrow down results if not specified
            search_query = query if "official" in query.lower() or "lyrics" in query.lower() else f"{query} official audio"
            
            info = self.ydl.extract_info(f"ytsearch5:{search_query}", download=False)
            
            if not info or 'entries' not in info or not info['entries']:
                logging.warning(f"No YouTube results found for: {query}")
                return None
                
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
            
            # Use fuzzy matching to pick the best candidate
            best = best_match(query, candidates)
            
            if best:
                logging.info(f"Found match: {best['title']} by {best['artist']}")
                logging.info(f"Extracted stream URL: {best['stream_url'][:60]}...")
                return Song(
                    title=best['title'],
                    artist=best['artist'],
                    duration=best['duration'],
                    video_id=best['video_id'],
                    stream_url=best['stream_url'],
                    thumbnail=best['thumbnail']
                )
            else:
                logging.warning("Fuzzy match failed to find a high-quality result.")
                
        except Exception as e:
            logging.error(f"Search error: {e}")
            
        return None

# Singleton instance
yt_search_engine = YTSearch()

def search_song(query: str) -> Song | None:
    return yt_search_engine.search(query)
