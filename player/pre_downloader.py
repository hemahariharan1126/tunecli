"""
Pre-Downloader — Background worker that silently downloads upcoming songs
in the queue to a local cache directory so MPV can play them without
any network dependency.
"""

import os
import threading
import logging
import yt_dlp
from config import AUDIO_CACHE_DIR, MAX_PREDOWNLOAD_SONGS


class PreDownloader:
    """
    Background download engine. Silently downloads songs to AUDIO_CACHE_DIR
    ahead of time so the Playback Controller can serve them from disk.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._downloading: set[str] = set()  # Track in-progress downloads by video_id
        self._downloaded: dict[str, str] = {}  # video_id -> local file path
        os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)

    def get_local_path(self, video_id: str) -> str | None:
        """
        Returns the local file path if the song has been pre-downloaded.
        Returns None if the file doesn't exist or hasn't been downloaded yet.
        """
        path = self._downloaded.get(video_id)
        if path and os.path.isfile(path):
            return path
        return None

    def is_downloading(self, video_id: str) -> bool:
        """Check if a download is currently in progress for this video_id."""
        with self._lock:
            return video_id in self._downloading

    def schedule(self, songs: list) -> None:
        """
        Schedule upcoming songs for background download.
        Only downloads up to MAX_PREDOWNLOAD_SONGS at a time.
        Skips songs already downloaded or currently downloading.
        """
        candidates = songs[:MAX_PREDOWNLOAD_SONGS]
        for song in candidates:
            if not song.video_id:
                continue
            if self.get_local_path(song.video_id):
                continue  # Already on disk
            with self._lock:
                if song.video_id in self._downloading:
                    continue  # Already in progress
                self._downloading.add(song.video_id)

            # Launch a daemon thread per song download
            t = threading.Thread(
                target=self._download,
                args=(song,),
                daemon=True,
                name=f"preload-{song.video_id[:8]}",
            )
            t.start()

    def _download(self, song) -> None:
        """Internal: Download a single song via yt-dlp to the audio cache."""
        video_id = song.video_id
        url = f"https://www.youtube.com/watch?v={video_id}"
        output_template = os.path.join(AUDIO_CACHE_DIR, f"{video_id}.%(ext)s")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "extractor_args": {"youtube": {"player_client": ["ios", "android"]}},
            # Don't postprocess — we want the raw audio file, fast
            "postprocessors": [],
        }

        try:
            logging.info(f"[PreDownload] Starting: {song.title}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                ext = info.get("ext", "webm")
                local_path = os.path.join(AUDIO_CACHE_DIR, f"{video_id}.{ext}")
                if os.path.isfile(local_path):
                    self._downloaded[video_id] = local_path
                    logging.info(f"[PreDownload] Done: {song.title} → {local_path}")
                else:
                    logging.warning(f"[PreDownload] File not found after download: {local_path}")
        except Exception as e:
            logging.error(f"[PreDownload] Failed for '{song.title}': {e}")
        finally:
            with self._lock:
                self._downloading.discard(video_id)

    def purge_file(self, video_id: str) -> None:
        """Delete the local cached file for a given video ID after it has been played."""
        path = self._downloaded.pop(video_id, None)
        if path and os.path.isfile(path):
            try:
                os.remove(path)
                logging.info(f"[PreDownload] Cache purged: {path}")
            except Exception as e:
                logging.warning(f"[PreDownload] Failed to purge {path}: {e}")

    def purge_all(self) -> None:
        """Delete all downloaded files in the audio cache directory."""
        for video_id in list(self._downloaded.keys()):
            self.purge_file(video_id)
        # Safety sweep for any orphaned files
        try:
            for f in os.listdir(AUDIO_CACHE_DIR):
                fp = os.path.join(AUDIO_CACHE_DIR, f)
                if os.path.isfile(fp):
                    os.remove(fp)
        except Exception as e:
            logging.warning(f"[PreDownload] Purge sweep error: {e}")


# Singleton
_pre_downloader_instance = None

def get_pre_downloader() -> PreDownloader:
    global _pre_downloader_instance
    if _pre_downloader_instance is None:
        _pre_downloader_instance = PreDownloader()
    return _pre_downloader_instance
