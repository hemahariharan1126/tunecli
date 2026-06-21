"""
Playback Controller — Glue logic between the search engine, MPV player, and queue.
Implements the Hybrid Playback Engine:
  - Layer 1: Instant Streaming with Auto-Resume Recovery
  - Layer 2: Background Pre-Downloading for disk-backed gapless playback
"""

from core.song import Song
from player.mpv_player import get_player
from player.queue_manager import QueueManager
from player.pre_downloader import get_pre_downloader
from search_engine.yt_search import search_song
from equalizer.eq_engine import EQEngine
import logging
import time
import threading

from rich.console import Console
from rich.text import Text

# Human-readable language names for user feedback
LANG_NAMES: dict[str, str] = {
    "ta": "Tamil 🎵",
    "hi": "Hindi 🎵",
    "te": "Telugu 🎵",
    "ml": "Malayalam 🎵",
    "kn": "Kannada 🎵",
    "en": "English 🎵",
}

# Minimum playback completion ratio to be considered a natural finish.
# If a song played less than 85% of its duration, we treat it as a network drop.
_NATURAL_FINISH_THRESHOLD = 0.85

class PlaybackController:
    def __init__(self):
        self.console = Console()
        self.queue_manager = QueueManager()
        try:
            self.mpv_player = get_player()
        except RuntimeError as e:
            logging.error(f"PlaybackController error: {e}")
            self.mpv_player = None
            
        self.current_mood = ""
        self.radio_mode = False
        self.seed_language = None
        self._is_refilling = False
        self._last_play_time = 0.0
        self._lang_overridden = False
        self._time_func = time.time

        # ── Auto-Resume State ──────────────────────────────
        # Tracks the last known good playback position of the current song.
        self._current_song: Song | None = None
        self._resume_retry_count = 0
        self._MAX_RESUME_RETRIES = 2  # Retry up to 2 times before skipping

        # ── Pre-Downloader ─────────────────────────────────
        self._pre_downloader = get_pre_downloader()

        # EQ engine — LLM-driven per-song equalizer
        self.eq_engine = EQEngine()
        self.eq_enabled = True
        
        # Register for auto-play when a song ends
        if self.mpv_player:
            self.mpv_player.set_eof_callback(self._on_song_end)

    def _on_song_end(self, event):
        """
        Called when MPV signals End of File.
        Core of the Hybrid Playback Engine:
          1. Detects premature EOF (network drop) vs natural finish.
          2. If dropped: triggers Auto-Resume Recovery.
          3. If finished naturally: moves to next song using pre-downloaded file if available.
        """
        try:
            data = getattr(event, 'data', None)
            if not data:
                return

            reason = getattr(data, 'reason', None)
            eof_val = getattr(data, 'EOF', 0)
            
            if reason != eof_val:
                # Non-natural end (e.g., stop() was called manually), do nothing
                logging.debug(f"Song ended with reason code: {reason} (ignoring)")
                return

            # ── Natural EOF path ───────────────────────────
            elapsed = self._time_func() - self._last_play_time

            # Runaway guard: song ended in under 3 seconds — something is very wrong
            if elapsed < 3.0:
                logging.warning(f"Song ended too quickly ({elapsed:.1f}s). Aborting auto-play.")
                return

            # ── Premature EOF guard (Auto-Resume Recovery) ─
            # Check if we're confident a network drop occurred
            song = self._current_song
            if song and song.duration and song.duration > 30:
                completion_ratio = elapsed / song.duration
                if completion_ratio < _NATURAL_FINISH_THRESHOLD:
                    # Network drop detected! The song didn't play enough to be "finished"
                    if self._resume_retry_count < self._MAX_RESUME_RETRIES:
                        self._resume_retry_count += 1
                        logging.warning(
                            f"[AutoResume] Drop detected at {elapsed:.0f}s "
                            f"({completion_ratio:.0%} of {song.duration:.0f}s). "
                            f"Retrying (attempt {self._resume_retry_count}/{self._MAX_RESUME_RETRIES})..."
                        )
                        # Resume from the last known position in a background thread
                        threading.Thread(
                            target=self._auto_resume,
                            args=(song, elapsed),
                            daemon=True,
                            name="auto-resume",
                        ).start()
                        return
                    else:
                        # Exhausted retries — accept the drop and move on
                        logging.warning("[AutoResume] Max retries exceeded. Moving to next song.")
                        self._resume_retry_count = 0

            # ── Natural finish — move to next ──────────────
            logging.info("Song ended naturally. Moving to next...")
            self._resume_retry_count = 0

            # Purge the cached file of the song that just finished
            if song and song.video_id:
                self._pre_downloader.purge_file(song.video_id)

            self._play_next()
            
            # If radio mode is on, check if we need more songs
            if self.radio_mode:
                self._check_radio_refill()

        except Exception as e:
            logging.error(f"Error processing EOF event: {e}")

    def _auto_resume(self, song: Song, last_position: float) -> None:
        """
        Background recovery thread.
        Re-fetches a fresh stream URL and resumes from the last known position.
        """
        try:
            logging.info(f"[AutoResume] Fetching fresh stream for: {song.title}")
            # Re-search to get fresh stream metadata
            fresh_song = search_song(f"{song.title} {song.artist}")
            if not fresh_song or not self.mpv_player:
                logging.error("[AutoResume] Could not fetch fresh stream. Skipping.")
                self._play_next()
                return

            # Replace the stream URL but keep the queue position
            self._current_song = fresh_song
            self._last_play_time = self._time_func() - last_position  # Preserve elapsed time

            self.mpv_player.play(fresh_song)

            # Wait briefly for MPV to initialize the new stream, then seek
            time.sleep(2.0)
            self.mpv_player.seek_to(last_position)
            logging.info(f"[AutoResume] Resumed at {last_position:.1f}s successfully.")

        except Exception as e:
            logging.error(f"[AutoResume] Recovery failed: {e}. Skipping to next.")
            self._play_next()

    def play_song(self, query: str):
        """Search for a song and start playback or add to queue."""
        song = search_song(query)
        if not song:
            return f"[red]  ERR: NOT_FOUND: {query}[/red]"

        self.queue_manager.add_song(song)

        # ── Language detection: lock on the very first song ─────────────────
        lang_notice = ""
        if self.seed_language is None:
            from recommender.recommender_engine import RecommenderEngine
            engine = RecommenderEngine()
            detected = engine.detect_language(f"{song.title} {song.artist}")
            self.seed_language = detected
            logging.info(f"Language context locked to: {self.seed_language}")
            lang_name = LANG_NAMES.get(detected, detected.upper())
            lang_notice = (
                f"\n  [bold reverse cyan] LANG.LOCK [/bold reverse cyan] "
                f"[dim]Detected [/dim][bold bright_cyan]{lang_name}[/bold bright_cyan]"
                f"[dim] — recommend & radio will stay in this language.[/dim]"
            )

        # If nothing is currently playing, start playback
        if self.mpv_player and not self.mpv_player.is_playing():
            self._play_next()
            return (
                f"[bold cyan]▶[/bold cyan] [white]{song.title}[/white]"
                f" [dim]is now playing.[/dim]{lang_notice}"
            )
        else:
            # Schedule background pre-download for queued songs
            self._schedule_predownload()
            return (
                f"  [bold cyan]+[/bold cyan] [white]{song.title}[/white]"
                f" [dim]added to queue.[/dim]{lang_notice}"
            )

    def _schedule_predownload(self) -> None:
        """Ask the pre-downloader to silently cache upcoming songs."""
        upcoming = self.queue_manager.get_queue()
        if upcoming:
            self._pre_downloader.schedule(upcoming)

    def _play_next(self):
        """
        Play the next song from the queue using the Hybrid Playback Engine.
        Priority: Pre-downloaded local file > Live stream.
        """
        if not self.mpv_player:
            return "[red]ERR: MPV_NOT_INIT[/red]"

        next_song = self.queue_manager.next_song()
        if next_song:
            self._last_play_time = self._time_func()
            self._current_song = next_song
            self._resume_retry_count = 0

            # ── Hybrid Engine: prefer local file ─────────
            local_path = self._pre_downloader.get_local_path(next_song.video_id)
            if local_path:
                logging.info(f"[Hybrid] Playing from disk: {next_song.title}")
                self.mpv_player.play_local(next_song, local_path)
            else:
                logging.info(f"[Hybrid] Streaming: {next_song.title}")
                self.mpv_player.play(next_song)

            # Schedule the next batch of songs for pre-downloading
            self._schedule_predownload()

            # Trigger EQ optimization in a background thread (non-blocking)
            if self.eq_enabled:
                threading.Thread(
                    target=self.eq_engine.apply_for_song_with_lang,
                    args=(next_song, self.mpv_player, self.seed_language or "en"),
                    daemon=True,
                    name=f"eq-{next_song.title[:20]}",
                ).start()

            # If radio mode is on, keep the queue topped up
            if self.radio_mode:
                self._check_radio_refill()
        else:
            self.queue_manager.now_playing_song = None

            # If radio mode is on but queue is empty, try a refill from history
            if self.radio_mode:
                self._check_radio_refill()

    def _check_radio_refill(self):
        """Trigger a refill if the queue is running low."""
        if self._is_refilling:
            return
            
        queue_len = len(self.get_queue())
        if queue_len < 3:
            threading.Thread(target=self._refill_radio, daemon=True).start()

    def _refill_radio(self):
        """Fetch recommendations and add to queue."""
        self._is_refilling = True
        try:
            from recommender.recommender_engine import RecommenderEngine
            engine = RecommenderEngine()
            
            seed_song = self.queue_manager.now_playing()
            if not seed_song and self.queue_manager.history:
                seed_song = self.queue_manager.history[-1]
                
            seed_query = f"{seed_song.title} {seed_song.artist}" if seed_song else "lofi beats"
            seed_vid = getattr(seed_song, 'video_id', None) if seed_song else None
            
            recs = engine.get_spotify_recommendations(
                seed_query, 
                limit=5, 
                target_lang=self.seed_language,
                seed_video_id=seed_vid
            )
            
            if not recs:
                logging.warning("RADIO.ERR: LLM Fallback also failed to generate recommendations.")
                return

            for r in recs:
                query = f"{r['title']} {r['artist']}"
                song = search_song(query, lang=self.seed_language)
                if song:
                    self.queue_manager.add_song(song)

            # Pre-download the newly added radio songs
            self._schedule_predownload()

            # If refilled and nothing is playing, start it
            if self.mpv_player and not self.mpv_player.is_playing():
                 self._play_next()
                 
        except Exception as e:
            logging.error(f"Radio refill error: {e}")
        finally:
            self._is_refilling = False

    def pause(self):
        if self.mpv_player:
            self.mpv_player.pause()
            return "[bold yellow]  [HLD] PLAYBACK.STOPPED[/bold yellow]"

    def resume(self):
        if self.mpv_player:
            self.mpv_player.resume()
            return "[bold green]  [RUN] PLAYBACK.RESUMED[/bold green]"

    def stop(self):
        if self.mpv_player:
            self.mpv_player.stop()
            self.queue_manager.clear()
            self.radio_mode = False
            return "[bold red]  [OFF] SYSTEM.HALT: QUEUE_CLEARED[/bold red]"

    def skip(self):
        """Skip current track and play next."""
        if self.mpv_player:
            self.mpv_player.stop()
        self._play_next()
        return "[dim]  SKIPPING.TRACK...[/dim]"

    def prev(self):
        """Go back to previous track if history exists."""
        prev_song = self.queue_manager.prev_song()
        if prev_song and self.mpv_player:
            self._last_play_time = self._time_func()
            self._current_song = prev_song
            self._resume_retry_count = 0
            self.mpv_player.play(prev_song)
            return f"  [bold magenta]«[/bold magenta] [white]RESTORING:[/white] [cyan]{prev_song.title}[/cyan]"
        else:
            return "[yellow]  WARN: NO_HISTORY_AVAILABLE[/yellow]"

    def set_volume(self, volume: int):
        if self.mpv_player:
            self.mpv_player.set_volume(volume)
            return f"  [dim]GAIN.SET:[/dim] [bold cyan]{volume}%[/bold cyan]"

    def get_queue(self):
        return self.queue_manager.get_queue()

    def set_mood(self, mood: str):
        self.current_mood = mood
        return f"  [dim]VIBE.LOCK:[/dim] [bold magenta]{mood.upper()}[/bold magenta]"

    def shutdown(self):
        """Clean up resources on app exit."""
        self._pre_downloader.purge_all()

# Global controller instance
controller = PlaybackController()

def get_controller():
    return controller
