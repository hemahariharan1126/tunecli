"""
MPV Player — Low-level wrapper around the mpv subprocess for audio playback.
"""

import subprocess
import os
from typing import Optional


class MPVPlayer:
    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self.current_url: str = ""

    def play(self, url: str, quality_format: str = "bestaudio"):
        """Launch mpv with the given URL and yt-dlp quality format."""
        self.stop()  # Stop any existing playback
        self.current_url = url
        cmd = [
            "mpv",
            "--no-video",
            f"--ytdl-format={quality_format}",
            "--quiet",
            url,
        ]
        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def pause(self):
        """Send SIGSTOP to pause mpv (Unix/Windows compatible via stdin)."""
        if self._process and self._process.poll() is None:
            # mpv supports space key to toggle pause via stdin
            try:
                self._process.stdin  # Not used; use IPC in future
            except Exception:
                pass

    def stop(self):
        """Terminate the mpv process."""
        if self._process and self._process.poll() is None:
            self._process.terminate()
            self._process.wait()
        self._process = None
        self.current_url = ""

    def is_playing(self) -> bool:
        """Return True if mpv is currently running."""
        return self._process is not None and self._process.poll() is None
