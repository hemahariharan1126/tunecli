"""
MPV Player — Wrapper around python-mpv for audio playback.
"""

import mpv
import logging
from core.song import Song

class MPVPlayer:
    def __init__(self):
        try:
            # Initialize MPV with no video and ytdl support
            self.player = mpv.MPV(
                ytdl=True, 
                video=False, 
                ytdl_format="bestaudio/best",
                log_handler=logging.debug,
                input_default_bindings=True
            )
            # Use same extractor args as search engine to bypass 403 blocks
            try:
                self.player.ytdl_raw_options = {
                    'extractor-args': 'youtube:player_client=ios,android'
                }
            except Exception as e:
                logging.warning(f"Could not set ytdl_raw_options: {e}")

            self.playing = False
            self._eof_callback = None

            # Register event handler for auto-play logic
            @self.player.event_callback('end-file')
            def handle_event(event):
                # Ensure playing flag is reset as soon as a file ends
                self.playing = False
                # We pass the event object to the callback
                if self._eof_callback:
                    try:
                        self._eof_callback(event)
                    except Exception as e:
                        logging.error(f"Error in EOF callback: {e}")

        except OSError as e:
            logging.error(f"Failed to initialize MPV: {e}")
            raise RuntimeError("MPV is not installed or not in PATH.")

    def set_eof_callback(self, callback):
        """Set a function to be called when a file ends playback."""
        self._eof_callback = callback

    def play(self, song: Song):
        """Play a song using its stream URL or video ID."""
        # Prefer the YouTube Watch URL if video_id is available. 
        # This allows MPV to resolve it fresh, avoiding expired direct URLs.
        url = f"https://www.youtube.com/watch?v={song.video_id}" if song.video_id else song.stream_url
        
        if not url:
            logging.error("No valid URL or Video ID to play.")
            return

        logging.info(f"Sending stream to MPV: {url}")
        if song.video_id:
            logging.info("Using YouTube watch URL; MPV will use its internal ytdl_hook with fresh extraction.")
        
        try:
            # mpv handles the ytdl resolution if stream_url is not direct
            self.player.play(url)
            self.playing = True
            # We don't wait_for_property here to avoid blocking the UI
            # instead we just flag it as potentially playing
        except Exception as e:
            logging.error(f"MPV play error: {e}")
            self.playing = False

    def pause(self):
        """Pause playback."""
        try:
            self.player.pause = True
            self.playing = False
        except Exception as e:
            logging.error(f"MPV pause error: {e}")

    def resume(self):
        """Resume playback."""
        try:
            self.player.pause = False
            self.playing = True
        except Exception as e:
            logging.error(f"MPV resume error: {e}")

    def stop(self):
        """Stop playback completely."""
        try:
            self.player.stop()
            self.playing = False
        except Exception as e:
            logging.error(f"MPV stop error: {e}")

    def skip(self):
        """Skip current song (handled by controller but here for completeness)."""
        self.stop()

    def set_volume(self, volume: int):
        """Set volume (0-100)."""
        try:
            self.player.volume = max(0, min(100, volume))
        except Exception as e:
            logging.error(f"MPV volume error: {e}")

    def get_volume(self) -> int:
        """Get current volume."""
        try:
            return int(self.player.volume)
        except:
            return 100

    def is_playing(self) -> bool:
        """Check if playing and not paused."""
        try:
            return self.playing and not self.player.pause
        except:
            return False

    def get_position(self) -> float:
        """Get current playback position in seconds."""
        try:
            return self.player.time_pos or 0.0
        except:
            return 0.0

    def get_duration(self) -> float:
        """Get current song duration in seconds."""
        try:
            return self.player.duration or 0.0
        except:
            return 0.0

    def terminate(self):
        """Cleanup MPV instance."""
        self.player.terminate()

# Singleton instance
player_instance = None

def get_player():
    global player_instance
    if player_instance is None:
        player_instance = MPVPlayer()
    return player_instance