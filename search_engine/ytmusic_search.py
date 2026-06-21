"""
YTMusic Search Engine — Uses ytmusicapi to search the official YouTube Music
catalog. Only returns officially licensed tracks (no fan uploads or covers).

This engine provides higher precision than the yt-dlp engine at the cost of
slightly lower recall for niche/regional content.
"""

import logging
import yt_dlp
from ytmusicapi import YTMusic
from core.song import Song
from search_engine.fuzzy_match import best_match, _score
from typing import Optional, Tuple

# Video type that guarantees an official audio track
_OFFICIAL_VIDEO_TYPE = "MUSIC_VIDEO_TYPE_ATV"

# yt-dlp options for stream URL extraction only (no search)
_YDL_STREAM_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'skip_download': True,
    'extractor_args': {'youtube': {'player_client': ['ios', 'android']}},
}


class YTMusicSearch:
    """
    Search engine backed by the YouTube Music API.
    Results are sourced exclusively from the official YT Music catalog.
    """
    def __init__(self):
        # Initialize without authentication — unauthenticated requests work
        # for searching public catalog songs.
        self._ytm = YTMusic()
        self._ydl = yt_dlp.YoutubeDL(_YDL_STREAM_OPTS)
        logging.info("[YTMusic] Search engine initialized (unauthenticated)")

    def _get_stream_url(self, video_id: str) -> str:
        """
        Extract a playable audio stream URL from a YouTube video ID using yt-dlp.
        This is required because ytmusicapi only returns metadata, not stream URLs.
        """
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            info = self._ydl.extract_info(url, download=False)
            return info.get('url', '') if info else ''
        except Exception as e:
            logging.warning(f"[YTMusic] Stream extraction failed for {video_id}: {e}")
            return ''

    def _ytmusic_result_to_candidate(self, result: dict) -> dict | None:
        """
        Map a raw ytmusicapi search result to our internal candidate dict format.
        Applies a large bonus for guaranteed official audio tracks.
        """
        try:
            video_id = result.get('videoId', '')
            if not video_id:
                return None

            title = result.get('title', '')
            duration_seconds = result.get('duration_seconds', 0)

            # Extract artist name
            artists = result.get('artists', [])
            artist = artists[0].get('name', 'Unknown') if artists else 'Unknown'

            # Extract thumbnail
            thumbnails = result.get('thumbnails', [])
            thumbnail = thumbnails[-1].get('url', '') if thumbnails else ''

            # Determine video type for the Official Bonus
            video_type = result.get('videoType', '')
            is_official = video_type == _OFFICIAL_VIDEO_TYPE

            return {
                'title': title,
                'artist': artist,
                'duration': int(duration_seconds),
                'video_id': video_id,
                'stream_url': '',  # Resolved lazily when needed
                'thumbnail': thumbnail,
                '_is_official': is_official,  # Internal flag for scoring
            }
        except Exception as e:
            logging.warning(f"[YTMusic] Failed to map result: {e}")
            return None

    def search(self, query: str, lang: str | None = None) -> Song | None:
        """
        Search YouTube Music for an official song and return a Song object.
        Falls back to None if ytmusicapi returns nothing.
        """
        logging.info(f"[YTMusic] Searching official catalog for: '{query}'")

        try:
            # Search with filter='songs' to exclude videos, podcasts, etc.
            results = self._ytm.search(query, filter='songs', limit=10)
        except Exception as e:
            logging.error(f"[YTMusic] API search failed: {e}")
            return None

        if not results:
            logging.warning(f"[YTMusic] No results from YouTube Music for: '{query}'")
            return None

        # Map results to our candidate format
        candidates = []
        for r in results:
            candidate = self._ytmusic_result_to_candidate(r)
            if candidate:
                candidates.append(candidate)

        if not candidates:
            return None

        # Score candidates with our fuzzy matcher
        # Apply an additional ATV bonus directly in the scoring step
        scored = []
        for c in candidates:
            base_score = _score(query, c)
            # Official Audio Track gets a massive +200 precision bonus
            official_bonus = 200 if c.get('_is_official') else 0
            scored.append((c, base_score + official_bonus))

        scored.sort(key=lambda x: x[1], reverse=True)
        best = scored[0][0]

        logging.info(
            f"[YTMusic] Winner: '{best['title']}' by '{best['artist']}' "
            f"(Official: {best.get('_is_official', False)}, Score: {scored[0][1]:.1f})"
        )

        # Resolve the stream URL now that we have our winner
        stream_url = self._get_stream_url(best['video_id'])

        return Song(
            title=best['title'],
            artist=best['artist'],
            duration=best['duration'],
            video_id=best['video_id'],
            stream_url=stream_url,
            thumbnail=best['thumbnail'],
        )


# Singleton
_ytmusic_engine: YTMusicSearch | None = None

def get_ytmusic_engine() -> YTMusicSearch:
    global _ytmusic_engine
    if _ytmusic_engine is None:
        _ytmusic_engine = YTMusicSearch()
    return _ytmusic_engine
