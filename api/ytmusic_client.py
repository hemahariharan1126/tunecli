"""
YouTube Music Client — Searches for songs, playlists, and resolves recommendations.
"""

import logging
from ytmusicapi import YTMusic


class YTMusicClient:
    def __init__(self):
        self._yt = YTMusic()

    def search_song(self, query: str) -> dict | None:
        """
        Search YouTube Music for a track matching the query.
        Returns a dict with: video_id, title, artist, duration_seconds
        """
        try:
            results = self._yt.search(query, filter="songs", limit=1)
            if not results:
                return None
            item = results[0]
            return {
                "video_id": item.get("videoId"),
                "title":    item.get("title"),
                "artist":   item.get("artists", [{}])[0].get("name", "Unknown"),
                "duration_seconds": item.get("duration_seconds", 0),
            }
        except Exception as e:
            logging.error(f"YTMusic search_song error: {e}")
            return None

    def get_stream_url(self, video_id: str, quality: str = "high") -> str:
        """Build a yt-dlp compatible URL for mpv to stream."""
        return f"https://music.youtube.com/watch?v={video_id}"

    def get_recommendations(self, video_id: str, limit: int = 5) -> list[dict]:
        """
        Get similar/related songs based on a seed video_id.
        Tries YouTube Music Related tab, and falls back to watch next queue.
        """
        # Strategy 1: Dynamic Related tab detection
        try:
            endpoint = 'next'
            data = {'videoId': video_id, 'enablePersistentPlaylistPanel': True, 'isAudioOnly': True}
            res = self._yt._send_request(endpoint, data)
            tabs = res.get('contents', {}).get('singleColumnMusicWatchNextResultsRenderer', {}).get('tabbedRenderer', {}).get('watchNextTabbedResultsRenderer', {}).get('tabs', [])
            
            related_browse_id = None
            for tab in tabs:
                tr = tab.get('tabRenderer', {})
                if 'Related' in tr.get('title', ''):
                    related_browse_id = tr.get('endpoint', {}).get('browseEndpoint', {}).get('browseId')
                    break
            
            if related_browse_id:
                sections = self._yt.get_song_related(related_browse_id)
                recommended = []
                for sec in sections:
                    for item in sec.get('contents', []):
                        vid = item.get('videoId')
                        if vid and vid != video_id:
                            recommended.append({
                                'video_id': vid,
                                'title': item.get('title', 'Unknown'),
                                'artist': item.get('artists', [{}])[0].get('name', 'Unknown') if item.get('artists') else 'Unknown',
                                'duration_seconds': item.get('duration_seconds', 0),
                            })
                            if len(recommended) >= limit:
                                return recommended
                if recommended:
                    return recommended[:limit]
        except Exception as e:
            logging.debug(f"YTMusic related tab parsing skipped: {e}")

        # Strategy 2: Standard watch playlist fallback
        try:
            results = self._yt.get_watch_playlist(videoId=video_id, limit=limit + 1)
            tracks = results.get("tracks", [])
            recommended = []
            for item in tracks[1:limit + 1]:
                recommended.append({
                    "video_id": item.get("videoId"),
                    "title":    item.get("title"),
                    "artist":   item.get("artists", [{}])[0].get("name", "Unknown"),
                    "duration_seconds": item.get("duration_seconds", 0),
                })
            return recommended
        except Exception:
            return []

    def search_playlist(self, query: str) -> dict | None:
        """
        Search for a playlist by name and return its metadata + tracks.
        """
        try:
            results = self._yt.search(query, filter="playlists", limit=5)
            if not results:
                return None
            
            for p in results:
                browse_id = p.get("browseId")
                if browse_id:
                    playlist_data = self._yt.get_playlist(browse_id)
                    tracks = playlist_data.get("tracks", [])
                    if tracks:
                        formatted_tracks = []
                        for t in tracks:
                            if t.get("videoId"):
                                formatted_tracks.append({
                                    "title": t.get("title", "Unknown"),
                                    "artist": t.get("artists", [{}])[0].get("name", "Unknown") if t.get("artists") else "Unknown",
                                    "videoId": t.get("videoId"),
                                    "duration_s": t.get("duration_seconds", 0),
                                })
                        return {
                            "title": playlist_data.get("title", p.get("title", query)),
                            "browseId": browse_id,
                            "tracks": formatted_tracks,
                        }
        except Exception as e:
            logging.error(f"YTMusic search_playlist error: {e}")
            return None
