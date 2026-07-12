"""
URL Resolver — Detects and resolves YouTube URLs into Song objects.
Used by the playback controller to bypass the search pipeline when
the user provides a direct YouTube link to M!play.

Supported formats:
    https://www.youtube.com/watch?v=VIDEO_ID
    https://youtu.be/VIDEO_ID
    https://music.youtube.com/watch?v=VIDEO_ID
    https://www.youtube.com/shorts/VIDEO_ID
"""

import re
import logging
import yt_dlp
from core.song import Song

# Regex that matches all YouTube URL variants
_YT_URL_PATTERN = re.compile(
    r"(https?://)?"
    r"(www\.)?"
    r"(youtube\.com/watch\?v=|youtu\.be/|music\.youtube\.com/watch\?v=|youtube\.com/shorts/)"
    r"[A-Za-z0-9_\-]{11}",
    re.IGNORECASE,
)

# yt-dlp options for metadata extraction only — no download, no search
_YDL_META_OPTS = {
    "format":         "bestaudio/best",
    "quiet":          True,
    "no_warnings":    True,
    "skip_download":  True,
    "extract_flat":   False,
    "extractor_args": {"youtube": {"player_client": ["ios", "android"]}},
}


def is_youtube_url(query: str) -> bool:
    """
    Returns True if the query string looks like a YouTube URL.
    Pure regex — no network call, runs in microseconds.
    """
    return bool(_YT_URL_PATTERN.search(query.strip()))


def resolve_url(url: str) -> Song | None:
    """
    Extract a Song object from a YouTube URL using yt-dlp.
    Returns None if extraction fails.

    The returned Song has:
        title    — raw YouTube video title
        artist   — uploader/channel name
        duration — track length in seconds
        video_id — YouTube video ID
        thumbnail — thumbnail URL
    """
    url = url.strip()
    logging.info(f"[URLResolver] Resolving YouTube URL: {url}")

    try:
        with yt_dlp.YoutubeDL(_YDL_META_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            logging.error(f"[URLResolver] yt-dlp returned no info for: {url}")
            return None

        video_id  = info.get("id", "")
        title     = info.get("title", "Unknown Title")
        artist    = info.get("uploader") or info.get("channel") or "Unknown Artist"
        duration  = int(info.get("duration", 0))
        thumbnail = info.get("thumbnail", "")

        logging.info(
            f"[URLResolver] Resolved: '{title}' by '{artist}' "
            f"({duration}s) | id={video_id}"
        )

        return Song(
            title=title,
            artist=artist,
            duration=duration,
            video_id=video_id,
            stream_url="",   # MPV resolves fresh via video_id
            thumbnail=thumbnail,
        )

    except Exception as e:
        logging.error(f"[URLResolver] Failed to resolve '{url}': {e}")
        return None
