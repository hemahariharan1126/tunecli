"""
YouTube Music Client — Searches for songs and resolves stream URLs.
"""

from ytmusicapi import YTMusic


class YTMusicClient:
    def __init__(self):
        self._yt = YTMusic()

    def search_song(self, query: str) -> dict | None:
        """
        Search YouTube Music for a track matching the query.

        Returns a dict with:
            video_id, title, artist, duration_seconds
        """
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

    def get_stream_url(self, video_id: str, quality: str = "high") -> str:
        """
        Build a yt-dlp compatible URL for mpv to stream.
        Quality hint is passed to mpv/yt-dlp via ytdl-format.
        """
        return f"https://music.youtube.com/watch?v={video_id}"

    def get_recommendations(self, video_id: str) -> list[dict]:
        """
        Get similar/related songs based on a seed video_id.
        """
        try:
            results = self._yt.get_watch_playlist(videoId=video_id, limit=5)
            tracks = results.get("tracks", [])
            recommended = []
            for item in tracks[1:6]:  # Skip the first one as it's the seed
                recommended.append({
                    "video_id": item.get("videoId"),
                    "title":    item.get("title"),
                    "artist":   item.get("artists", [{}])[0].get("name", "Unknown"),
                    "duration_seconds": item.get("duration_seconds", 0),
                })
            return recommended
        except Exception:
            return []
