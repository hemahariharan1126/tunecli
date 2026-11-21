"""
MPV Player — Wrapper around python-mpv for audio playback.
Supports direct stream URLs, local file playback, and EQ.

Architecture:
- Lazy MPV module loading and lazy player initialization.
- Full diagnostic reporting if native MPV or python-mpv is unavailable.
- Safe, non-crashing no-op behavior when MPV cannot be initialized.
- Idempotent termination.
"""

import logging
import threading
from typing import Optional, Callable
from core.song import Song


class MPVPlayer:
    def __init__(self):
        self.player = None
        self.playing = False
        self._eof_callback: Optional[Callable] = None
        self._current_song: Optional[Song] = None
        self._init_error: Optional[str] = None
        self._terminated = False

        self._initialize()

    def _initialize(self) -> None:
        """Lazily imports python-mpv and initializes the MPV client instance."""
        try:
            import mpv
        except OSError as e:
            self._init_error = (
                f"libmpv native library could not be loaded: {e}.\n"
                "On Windows, ensure 'lib/libmpv-2.dll' exists. Run StartTuneCLI.bat."
            )
            logging.error(f"[MPVPlayer] {self._init_error}")
            return
        except ImportError as e:
            self._init_error = (
                f"python-mpv is not installed: {e}. Run 'pip install python-mpv'."
            )
            logging.error(f"[MPVPlayer] {self._init_error}")
            return
        except Exception as e:
            self._init_error = f"Unexpected error importing mpv: {e}"
            logging.error(f"[MPVPlayer] {self._init_error}")
            return

        try:
            # Initialize MPV with no video and ytdl support
            self.player = mpv.MPV(
                ytdl=True,
                video=False,
                ytdl_format="bestaudio/best",
                log_handler=logging.debug,
                input_default_bindings=True,
                # Network resilience: forward buffer to minimize dropouts
                demuxer_max_bytes="50M",
                demuxer_max_back_bytes="20M",
                network_timeout=15,
            )

            # Use extractor args to bypass YouTube 403 blocks
            try:
                self.player.ytdl_raw_options = {
                    'extractor-args': 'youtube:player_client=ios,android'
                }
            except Exception as e:
                logging.warning(f"[MPVPlayer] Could not set ytdl_raw_options: {e}")

            # Register event handler for auto-play logic
            @self.player.event_callback('end-file')
            def handle_event(event):
                self.playing = False
                if self._eof_callback:
                    try:
                        self._eof_callback(event)
                    except Exception as e:
                        logging.error(f"[MPVPlayer] Error in EOF callback: {e}")

            logging.info("[MPVPlayer] Native MPV player initialized successfully.")

        except Exception as e:
            self.player = None
            self._init_error = f"Failed to instantiate MPV player: {e}"
            logging.error(f"[MPVPlayer] {self._init_error}")

    def is_available(self) -> bool:
        """Returns True if MPV is successfully initialized and ready to play."""
        return self.player is not None and not self._terminated

    def get_init_error(self) -> Optional[str]:
        """Returns the initialization error message, if any."""
        return self._init_error

    def set_eof_callback(self, callback: Callable):
        """Set a function to be called when a file ends playback."""
        self._eof_callback = callback

    def play(self, song: Song) -> bool:
        """Stream a song using its YouTube Watch URL or direct stream URL."""
        if not self.is_available():
            logging.error(f"[MPVPlayer] Cannot play '{song.title}': MPV unavailable ({self._init_error})")
            return False

        url = f"https://www.youtube.com/watch?v={song.video_id}" if song.video_id else song.stream_url
        if not url:
            logging.error("[MPVPlayer] No valid URL or Video ID to play.")
            return False

        logging.info(f"[MPVPlayer] Streaming: {url}")
        self._current_song = song
        try:
            self.player.play(url)
            self.playing = True
            return True
        except Exception as e:
            logging.error(f"[MPVPlayer] Play error: {e}")
            self.playing = False
            return False

    def play_local(self, song: Song, local_path: str) -> bool:
        """Play a pre-downloaded local audio file."""
        if not self.is_available():
            logging.error(f"[MPVPlayer] Cannot play local file: MPV unavailable ({self._init_error})")
            return False

        if not local_path:
            logging.warning("[MPVPlayer] play_local called with empty path. Falling back to stream.")
            return self.play(song)

        logging.info(f"[MPVPlayer] Playing local file: {local_path}")
        self._current_song = song
        try:
            self.player.play(local_path)
            self.playing = True
            return True
        except Exception as e:
            logging.error(f"[MPVPlayer] Local play error: {e}. Falling back to stream.")
            return self.play(song)

    def seek_to(self, position: float) -> None:
        """Seek to a specific position in seconds."""
        if not self.is_available():
            return
        try:
            self.player.seek(position, reference="absolute")
        except Exception as e:
            logging.warning(f"[MPVPlayer] Seek absolute error: {e}")

    def seek_relative(self, offset: float) -> None:
        """Seek relatively by offset in seconds."""
        if not self.is_available():
            return
        try:
            self.player.seek(offset, reference="relative")
        except Exception as e:
            logging.warning(f"[MPVPlayer] Seek relative error: {e}")

    def pause(self) -> None:
        """Pause playback."""
        if not self.is_available():
            return
        try:
            self.player.pause = True
            self.playing = False
        except Exception as e:
            logging.error(f"[MPVPlayer] Pause error: {e}")

    def resume(self) -> None:
        """Resume playback."""
        if not self.is_available():
            return
        try:
            self.player.pause = False
            self.playing = True
        except Exception as e:
            logging.error(f"[MPVPlayer] Resume error: {e}")

    def stop(self) -> None:
        """Stop playback completely."""
        if not self.is_available():
            return
        try:
            self.player.stop()
            self.playing = False
            self._current_song = None
        except Exception as e:
            logging.error(f"[MPVPlayer] Stop error: {e}")

    def skip(self) -> None:
        """Skip current song."""
        self.stop()

    def set_volume(self, volume: int) -> None:
        """Set volume (0-100)."""
        if not self.is_available():
            return
        try:
            self.player.volume = max(0, min(100, volume))
        except Exception as e:
            logging.error(f"[MPVPlayer] Volume error: {e}")

    def get_volume(self) -> int:
        """Get current volume."""
        if not self.is_available():
            return 100
        try:
            return int(self.player.volume)
        except Exception:
            return 100

    def is_playing(self) -> bool:
        """Check if playing and not paused."""
        if not self.is_available():
            return False
        try:
            return self.playing and not self.player.pause
        except Exception:
            return False

    def is_paused(self) -> bool:
        """Check if paused."""
        if not self.is_available():
            return False
        try:
            return bool(self.player.pause)
        except Exception:
            return False

    def get_position(self) -> float:
        """Get current playback position in seconds."""
        if not self.is_available():
            return 0.0
        try:
            return self.player.time_pos or 0.0
        except Exception:
            return 0.0

    def get_duration(self) -> float:
        """Get current song duration in seconds."""
        if not self.is_available():
            return 0.0
        try:
            return self.player.duration or 0.0
        except Exception:
            return 0.0

    def set_speed(self, rate: float) -> None:
        """Set playback speed (0.25 to 4.0). 1.0 is normal speed."""
        if not self.is_available():
            return
        try:
            self.player.speed = max(0.25, min(4.0, rate))
        except Exception as e:
            logging.error(f"[MPVPlayer] Speed error: {e}")

    def get_speed(self) -> float:
        """Get current playback speed."""
        if not self.is_available():
            return 1.0
        try:
            return float(self.player.speed) if self.player.speed is not None else 1.0
        except Exception:
            return 1.0

    def apply_fade_in(self, seconds: int) -> None:
        """Apply an audio fade-in effect at track start."""
        if not self.is_available() or seconds <= 0:
            return
        try:
            self.player.command("af", "add", f"lavfi=[afade=t=in:ss=0:d={seconds}]")
        except Exception as e:
            logging.debug(f"[MPVPlayer] Fade-in error: {e}")

    def set_eq(self, bands: list[int]) -> None:
        """Apply a 10-band equalizer using MPV's lavfi audio filter."""
        if not self.is_available():
            return
        try:
            freqs = [32, 64, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
            active = [
                f"equalizer=f={f}:width_type=o:w=2:g={g}"
                for f, g in zip(freqs, bands)
                if g != 0
            ]
            if not active:
                self.player.af = ""
            else:
                self.player.af = f"lavfi=[{','.join(active)}]"
            logging.info(f"[MPVPlayer] EQ applied: {bands}")
        except Exception as e:
            logging.warning(f"[MPVPlayer] set_eq failed: {e}")

    def reset_eq(self) -> None:
        """Remove all audio filters — flat EQ."""
        if not self.is_available():
            return
        try:
            self.player.af = ""
            logging.info("[MPVPlayer] EQ reset to flat.")
        except Exception as e:
            logging.warning(f"[MPVPlayer] reset_eq failed: {e}")

    def terminate(self) -> None:
        """Clean up MPV instance idempotently."""
        if self._terminated:
            return
        self._terminated = True
        if self.player:
            try:
                self.player.terminate()
            except Exception as e:
                logging.debug(f"[MPVPlayer] Error terminating MPV: {e}")
            self.player = None


# Singleton instance — lazy, created on first call to get_player()
_player_instance: Optional[MPVPlayer] = None
_player_lock = threading.Lock()


def get_player() -> MPVPlayer:
    """Return the singleton MPVPlayer, creating it on first call in a thread-safe manner."""
    global _player_instance
    if _player_instance is None:
        with _player_lock:
            if _player_instance is None:
                _player_instance = MPVPlayer()
    return _player_instance
