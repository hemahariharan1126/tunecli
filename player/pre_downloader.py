"""
Pre-Downloader — Background worker that silently downloads upcoming songs
in the queue to a local cache directory so MPV can play them without
any network dependency.

Features:
- Bounded ThreadPoolExecutor (prevents thread explosion).
- Thread-safe metadata access (get_local_path, is_downloading, etc.).
- Safe atomic download (.part file renamed on completion; partials removed on error).
- LRU cache eviction based on MAX_AUDIO_CACHE_FILES.
"""

import os
import glob
import threading
import logging
import concurrent.futures
from collections import OrderedDict
import yt_dlp
from config import AUDIO_CACHE_DIR, MAX_PREDOWNLOAD_SONGS, MAX_AUDIO_CACHE_FILES


class PreDownloader:
    """
    Background download engine. Silently downloads songs to AUDIO_CACHE_DIR
    ahead of time so the Playback Controller can serve them from disk.
    Uses a bounded ThreadPoolExecutor to prevent thread exhaustion.
    """
    def __init__(self, max_workers: int = 2):
        self._lock = threading.Lock()
        self._downloading: set[str] = set()  # Track in-progress downloads by video_id
        self._downloaded: OrderedDict[str, str] = OrderedDict()  # video_id -> local file path (LRU order)
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="tunecli-preload"
        )
        os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)
        self._scan_existing_cache()

    def _scan_existing_cache(self) -> None:
        """Scan cache dir on startup and clean any orphaned .part files."""
        try:
            for part in glob.glob(os.path.join(AUDIO_CACHE_DIR, "*.part*")):
                try:
                    os.remove(part)
                except Exception:
                    pass

            for entry in os.scandir(AUDIO_CACHE_DIR):
                if entry.is_file() and not entry.name.endswith(".part"):
                    vid, _ = os.path.splitext(entry.name)
                    self._downloaded[vid] = entry.path
        except Exception as e:
            logging.debug(f"[PreDownloader] Cache scan note: {e}")

    def get_local_path(self, video_id: str) -> str | None:
        """
        Returns the local file path if the song has been pre-downloaded.
        Marks it as recently accessed (LRU).
        """
        with self._lock:
            path = self._downloaded.get(video_id)
            if path and os.path.isfile(path):
                self._downloaded.move_to_end(video_id)
                return path
            elif video_id in self._downloaded:
                del self._downloaded[video_id]
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

            # Submit to bounded thread pool
            self._executor.submit(self._download, song)

    def _download(self, song) -> None:
        """Internal: Download a single song via yt-dlp to the audio cache atomically."""
        video_id = song.video_id
        url = f"https://www.youtube.com/watch?v={video_id}"
        # Use .part extension during download
        output_template = os.path.join(AUDIO_CACHE_DIR, f"{video_id}.part.%(ext)s")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "extractor_args": {"youtube": {"player_client": ["ios", "android"]}},
            "socket_timeout": 15,
            "postprocessors": [],
        }

        part_file = None
        try:
            logging.info(f"[PreDownload] Starting: {song.title}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                ext = info.get("ext", "webm")
                part_file = os.path.join(AUDIO_CACHE_DIR, f"{video_id}.part.{ext}")
                final_path = os.path.join(AUDIO_CACHE_DIR, f"{video_id}.{ext}")

                if os.path.isfile(part_file):
                    # Atomically rename .part file to final path
                    os.replace(part_file, final_path)
                    with self._lock:
                        self._downloaded[video_id] = final_path
                        self._downloaded.move_to_end(video_id)
                        self._enforce_cache_limit()
                    logging.info(f"[PreDownload] Done: {song.title} → {final_path}")
                elif os.path.isfile(final_path):
                    with self._lock:
                        self._downloaded[video_id] = final_path
                else:
                    logging.warning(f"[PreDownload] File not found after download for: {song.title}")
        except Exception as e:
            logging.error(f"[PreDownload] Failed for '{song.title}': {e}")
            # Clean up partial download artifact
            if part_file and os.path.isfile(part_file):
                try:
                    os.remove(part_file)
                except Exception:
                    pass
        finally:
            with self._lock:
                self._downloading.discard(video_id)

    def _enforce_cache_limit(self) -> None:
        """Evicts oldest downloaded files when cache exceeds MAX_AUDIO_CACHE_FILES (must be called under self._lock)."""
        while len(self._downloaded) > MAX_AUDIO_CACHE_FILES:
            oldest_vid, oldest_path = self._downloaded.popitem(last=False)
            if oldest_path and os.path.isfile(oldest_path):
                try:
                    os.remove(oldest_path)
                    logging.info(f"[PreDownload] Cache evicted LRU track: {oldest_path}")
                except Exception as e:
                    logging.warning(f"[PreDownload] Eviction error for {oldest_path}: {e}")

    def purge_file(self, video_id: str) -> None:
        """Delete the local cached file for a given video ID after it has been played."""
        with self._lock:
            path = self._downloaded.pop(video_id, None)
        if path and os.path.isfile(path):
            try:
                os.remove(path)
                logging.info(f"[PreDownload] Cache purged: {path}")
            except Exception as e:
                logging.warning(f"[PreDownload] Failed to purge {path}: {e}")

    def purge_all(self) -> None:
        """Delete all downloaded files in the audio cache directory."""
        with self._lock:
            vids = list(self._downloaded.keys())
        for video_id in vids:
            self.purge_file(video_id)
        # Safety sweep for any orphaned files
        try:
            for f in os.listdir(AUDIO_CACHE_DIR):
                fp = os.path.join(AUDIO_CACHE_DIR, f)
                if os.path.isfile(fp):
                    os.remove(fp)
        except Exception as e:
            logging.warning(f"[PreDownload] Purge sweep error: {e}")

    def shutdown(self) -> None:
        """Shutdown the executor gracefully on exit."""
        self._executor.shutdown(wait=False, cancel_futures=True)


# Singleton
_pre_downloader_instance = None

def get_pre_downloader() -> PreDownloader:
    global _pre_downloader_instance
    if _pre_downloader_instance is None:
        _pre_downloader_instance = PreDownloader()
    return _pre_downloader_instance
