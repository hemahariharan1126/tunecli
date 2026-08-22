"""
URL Resolver — Detects and resolves YouTube and Spotify URLs into Song objects.
Used by the playback controller to bypass the search pipeline when
the user provides a direct link to M!play.

Supported YouTube formats:
    https://www.youtube.com/watch?v=VIDEO_ID
    https://youtu.be/VIDEO_ID
    https://music.youtube.com/watch?v=VIDEO_ID
    https://www.youtube.com/shorts/VIDEO_ID

Supported Spotify formats (no API key required):
    https://open.spotify.com/track/TRACK_ID        — single track
    https://open.spotify.com/playlist/PLAYLIST_ID  — full playlist
"""

import re
import json
import logging
import yt_dlp
import requests
from core.song import Song

# ── YouTube URL Detection ─────────────────────────────────────────────────────
_YT_URL_PATTERN = re.compile(
    r"(https?://)?"
    r"(www\.)?"
    r"(youtube\.com/watch\?v=|youtu\.be/|music\.youtube\.com/watch\?v=|youtube\.com/shorts/)"
    r"[A-Za-z0-9_\-]{11}",
    re.IGNORECASE,
)

# ── Spotify URL Detection ─────────────────────────────────────────────────────
_SPOTIFY_TRACK_PATTERN = re.compile(
    r"https?://open\.spotify\.com/track/[A-Za-z0-9]+",
    re.IGNORECASE,
)

_SPOTIFY_PLAYLIST_PATTERN = re.compile(
    r"https?://open\.spotify\.com/playlist/[A-Za-z0-9]+",
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

# HTTP headers to mimic a browser so Spotify returns full Open Graph tags
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ── YouTube ───────────────────────────────────────────────────────────────────

def is_youtube_url(query: str) -> bool:
    """
    Returns True if the query string looks like a YouTube URL.
    Pure regex — no network call.
    """
    return bool(_YT_URL_PATTERN.search(query.strip()))


def resolve_url(url: str) -> Song | None:
    """
    Extract a Song object from a YouTube URL using yt-dlp.
    Returns None if extraction fails.
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


# ── Spotify ───────────────────────────────────────────────────────────────────

def is_spotify_url(query: str) -> bool:
    """
    Returns True if the query string looks like a Spotify track URL.
    Pure regex — no network call.
    """
    return bool(_SPOTIFY_TRACK_PATTERN.search(query.strip()))


def resolve_spotify_url(url: str) -> Song | None:
    """
    Resolve a Spotify track URL to a Song object without using the Spotify API.

    How it works:
        1. Extracts the track ID from the URL.
        2. Fetches the Spotify embed page (server-side rendered, contains full JSON).
        3. Parses the __NEXT_DATA__ JSON block to extract title and artists.
        4. Delegates to our existing search_song() to find the YouTube version.

    Returns a Song object on success, None on failure.
    """
    url = url.strip()
    logging.info(f"[SpotifyResolver] Resolving Spotify URL: {url}")

    try:
        # ── Step 1: Extract track ID ───────────────────────────────────────
        id_match = re.search(r"open\.spotify\.com/track/([A-Za-z0-9]+)", url)
        if not id_match:
            logging.error("[SpotifyResolver] Could not extract track ID from URL.")
            return None
        track_id = id_match.group(1)

        # ── Step 2: Fetch embed page (server-side rendered with full data) ─
        embed_url = f"https://open.spotify.com/embed/track/{track_id}"
        response = requests.get(embed_url, headers=_BROWSER_HEADERS, timeout=10)
        response.raise_for_status()

        # ── Step 3: Parse __NEXT_DATA__ JSON block ─────────────────────────
        next_data_match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            response.text,
            re.DOTALL,
        )
        if not next_data_match:
            logging.error("[SpotifyResolver] __NEXT_DATA__ block not found in embed page.")
            return None

        data = json.loads(next_data_match.group(1))
        entity = data["props"]["pageProps"]["state"]["data"]["entity"]

        track_name  = entity.get("name", "").strip()
        artists     = entity.get("artists", [])
        artist_name = artists[0].get("name", "Unknown Artist").strip() if artists else "Unknown Artist"
        # Duration is in milliseconds
        duration_ms = entity.get("duration", 0)
        duration_s  = int(duration_ms / 1000)

        if not track_name:
            logging.error("[SpotifyResolver] Track name is empty in JSON data.")
            return None

        logging.info(
            f"[SpotifyResolver] Parsed: '{track_name}' by '{artist_name}' ({duration_s}s)"
        )

        # ── Step 4: Search YouTube for the official version ────────────────
        from search_engine.yt_search import search_song
        search_query = f"{track_name} {artist_name}"
        logging.info(f"[SpotifyResolver] Searching YouTube for: '{search_query}'")

        song = search_song(search_query)
        if not song:
            logging.error(f"[SpotifyResolver] YouTube search failed for: '{search_query}'")
            return None

        # If the matched YouTube duration is unknown, fill in from Spotify
        if not song.duration and duration_s:
            song.duration = duration_s

        logging.info(
            f"[SpotifyResolver] Matched: '{song.title}' by '{song.artist}' | id={song.video_id}"
        )
        return song

    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logging.error(f"[SpotifyResolver] JSON parsing error: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"[SpotifyResolver] Network error fetching Spotify embed: {e}")
        return None
    except Exception as e:
        logging.error(f"[SpotifyResolver] Unexpected error: {e}")
        return None

# ── Spotify Playlist ──────────────────────────────────────────────────────────

def is_spotify_playlist_url(query: str) -> bool:
    """
    Returns True if the query string is a Spotify playlist URL.
    Pure regex — no network call.
    """
    return bool(_SPOTIFY_PLAYLIST_PATTERN.search(query.strip()))


def fetch_spotify_playlist_tracks(playlist_id: str) -> list[dict]:
    """
    Fetch all tracks from a Spotify playlist using embed page scraping.
    No API key, no token — uses the same __NEXT_DATA__ technique as single tracks.

    Returns a list of dicts: [{title, artist, duration_s}, ...]
    Returns an empty list on failure.
    """
    embed_url = f"https://open.spotify.com/embed/playlist/{playlist_id}"
    logging.info(f"[SpotifyPlaylist] Fetching embed: {embed_url}")

    try:
        response = requests.get(embed_url, headers=_BROWSER_HEADERS, timeout=15)
        response.raise_for_status()

        next_data_match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            response.text, re.DOTALL,
        )
        if not next_data_match:
            logging.error("[SpotifyPlaylist] __NEXT_DATA__ not found in embed page.")
            return []

        data   = json.loads(next_data_match.group(1))
        entity = data["props"]["pageProps"]["state"]["data"]["entity"]

        playlist_name = entity.get("name") or entity.get("title", "Unknown Playlist")
        track_list    = entity.get("trackList", [])

        logging.info(
            f"[SpotifyPlaylist] '{playlist_name}' — {len(track_list)} tracks found."
        )

        tracks = []
        for t in track_list:
            title  = (t.get("title") or "").strip()
            artist = (t.get("subtitle") or "").strip()
            # duration is in milliseconds in the embed JSON
            dur_ms = t.get("duration", 0)
            dur_s  = int(dur_ms / 1000)
            if title and artist:
                tracks.append({"title": title, "artist": artist, "duration_s": dur_s})

        return tracks

    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logging.error(f"[SpotifyPlaylist] JSON parsing error: {e}")
        return []
    except requests.exceptions.RequestException as e:
        logging.error(f"[SpotifyPlaylist] Network error: {e}")
        return []
    except Exception as e:
        logging.error(f"[SpotifyPlaylist] Unexpected error: {e}")
        return []


def resolve_spotify_playlist(
    url: str,
    on_song_found: callable = None,
) -> list[Song]:
    """
    Resolve a Spotify playlist URL to a list of Song objects.

    Args:
        url:          Spotify playlist URL.
        on_song_found: Optional callback called with each Song as it is resolved.
                       Used for background threading — allows the caller to add
                       songs to the queue as they are found, one by one.

    Returns:
        List of successfully resolved Song objects.
    """
    url = url.strip()

    # Step 1: Extract playlist ID
    id_match = re.search(r"open\.spotify\.com/playlist/([A-Za-z0-9]+)", url)
    if not id_match:
        logging.error("[SpotifyPlaylist] Could not extract playlist ID.")
        return []
    playlist_id = id_match.group(1)

    # Step 2: Fetch all track metadata from Spotify embed
    tracks = fetch_spotify_playlist_tracks(playlist_id)
    if not tracks:
        logging.error("[SpotifyPlaylist] No tracks returned from embed.")
        return []

    # Step 3: Search YouTube for each track
    from search_engine.yt_search import search_song
    resolved: list[Song] = []

    for i, t in enumerate(tracks):
        search_query = f"{t['title']} {t['artist']}"
        logging.info(
            f"[SpotifyPlaylist] [{i+1}/{len(tracks)}] Searching: '{search_query}'"
        )
        song = search_song(search_query)
        if song:
            # Fill in Spotify duration if YouTube missed it
            if not song.duration and t["duration_s"]:
                song.duration = t["duration_s"]
            resolved.append(song)
            if on_song_found:
                on_song_found(song)
        else:
            logging.warning(
                f"[SpotifyPlaylist] YouTube search failed for: '{search_query}' — skipping."
            )

    logging.info(
        f"[SpotifyPlaylist] Resolved {len(resolved)}/{len(tracks)} tracks."
    )
    return resolved


def search_spotify_playlist_by_name(query: str) -> str | None:
    """
    Search for a Spotify playlist by name using DuckDuckGo HTML search.
    Returns the first matching Spotify playlist URL, or None if not found.
    """
    import urllib.parse
    
    logging.info(f"[SpotifyPlaylistSearch] Searching DuckDuckGo for: '{query}'")
    search_query = f"site:open.spotify.com/playlist {query}"
    ddg_url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(search_query)
    
    try:
        r = requests.get(ddg_url, headers=_BROWSER_HEADERS, timeout=10)
        r.raise_for_status()
        
        # DuckDuckGo wraps outbound links in a redirect
        redirects = re.findall(r'uddg=([^&]+)', r.text)
        urls = [urllib.parse.unquote(u) for u in redirects if "open.spotify.com/playlist" in urllib.parse.unquote(u)]
        
        if urls:
            playlist_url = urls[0]
            logging.info(f"[SpotifyPlaylistSearch] Found playlist: {playlist_url}")
            return playlist_url
        else:
            logging.warning("[SpotifyPlaylistSearch] No Spotify playlist found in search results.")
            return None
            
    except Exception as e:
        logging.error(f"[SpotifyPlaylistSearch] Search failed: {e}")
        return None
