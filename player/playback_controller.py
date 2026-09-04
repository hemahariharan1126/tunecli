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

        # ── UI Log Callback ────────────────────────────────
        # Set by app.py after the TUI is mounted so background threads
        # can post messages directly to the visible log panel.
        self._app_log_callback = None

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

    def _post_playlist_summary(self, queued: int, total: int) -> None:
        """Post playlist load result to the UI log."""
        if queued == total:
            msg = f"[bold bright_green]✔ PLAYLIST READY[/bold bright_green] All [white]{queued}/{total}[/white] tracks queued successfully."
        else:
            missed = total - queued
            msg = (
                f"[bold yellow]⚠ PLAYLIST LOADED[/bold yellow] Queued [white]{queued}/{total}[/white] songs "
                f"([dim]{missed} not found on YouTube[/dim])."
            )
        logging.info(msg)
        if hasattr(self, '_app_log_callback') and self._app_log_callback:
            self._app_log_callback(msg)

    def play_song(self, query: str):
        """Search for a song and start playback or add to queue.
        
        Supports both text search queries and direct YouTube URLs.
        """
        # ── URL Gate ─────────────────────────────────────────────────────────
        # If the user passed a YouTube URL directly, resolve it via yt-dlp
        # and skip the 4-stage search pipeline entirely.
        from search_engine.url_resolver import (
            is_youtube_url, resolve_url,
            is_spotify_url, resolve_spotify_url,
            is_spotify_playlist_url, fetch_spotify_playlist_tracks,
        )
        from search_engine.yt_search import search_song as _search_song

        if is_youtube_url(query):
            song = resolve_url(query)
            if not song:
                return "[red]  ERR: URL_RESOLVE_FAILED — Could not extract song metadata from the URL.[/red]"

        elif is_spotify_playlist_url(query):
            # ── Spotify Playlist: Background Threading ────────────────────
            # 1. Immediately fetch all track metadata from Spotify embed (fast)
            import re as _re
            from utils.history_manager import add_history_entry
            
            id_match = _re.search(r"open\.spotify\.com/playlist/([A-Za-z0-9]+)", query)
            if not id_match:
                return "[red]  ERR: Could not parse playlist ID from URL.[/red]"
            playlist_id = id_match.group(1)
            add_history_entry("playlist", "Spotify Playlist", "", query)

            tracks = fetch_spotify_playlist_tracks(playlist_id)
            if not tracks:
                return "[red]  ERR: PLAYLIST_EMPTY — Could not fetch tracks from Spotify playlist.[/red]"

            # 2. Resolve the first track immediately so playback can start
            first = tracks[0]
            song = _search_song(f"{first['title']} {first['artist']}")
            if not song:
                return f"[red]  ERR: Could not find '{first['title']}' on YouTube.[/red]"
            if not song.duration and first["duration_s"]:
                song.duration = first["duration_s"]

            self.queue_manager.add_song(song)
            if self.mpv_player and not self.mpv_player.is_playing():
                self._play_next()

            # 3. Resolve the rest in a background thread — robust, isolated
            remaining = tracks[1:]
            total_tracks = len(tracks)  # includes track 1 already queued

            if remaining:
                def _queue_remaining(rem_tracks, total):
                    queued = 1  # Track 1 is already playing
                    failed = 0

                    for t in rem_tracks:
                        try:
                            # Attempt 1: full "Title Artist" query
                            q = f"{t['title']} {t['artist']}"
                            s = _search_song(q)

                            # Attempt 2: title-only retry if full query fails
                            if not s:
                                logging.warning(
                                    f"[Playlist] Retrying with title-only: '{t['title']}'"
                                )
                                s = _search_song(t['title'])

                            if s:
                                if not s.duration and t["duration_s"]:
                                    s.duration = t["duration_s"]
                                self.queue_manager.add_song(s)
                                queued += 1
                            else:
                                failed += 1
                                logging.warning(
                                    f"[Playlist] No YouTube match for: '{t['title']}'"
                                )

                        except Exception as e:
                            # Isolate: one bad track never kills remaining tracks
                            failed += 1
                            logging.error(
                                f"[Playlist] Error queuing '{t['title']}': {e}"
                            )

                    self._post_playlist_summary(queued, total)

                threading.Thread(
                    target=_queue_remaining,
                    args=(remaining, total_tracks),
                    daemon=True,
                    name="playlist-queuer",
                ).start()

            return (
                f"[bold bright_green]PLAYLIST[/bold bright_green] "
                f"[dim]Loading[/dim] [bold white]{len(tracks)}[/bold white] "
                f"[dim]tracks into queue...[/dim]\n"
                f"  [bold cyan]▶[/bold cyan] [white]{song.title}[/white] "
                f"[dim]is now playing.[/dim]"
            )

        elif is_spotify_url(query):
            song = resolve_spotify_url(query)
            if not song:
                return "[red]  ERR: SPOTIFY_RESOLVE_FAILED — Could not find song on YouTube from Spotify link.[/red]"

        else:
            # ── Standard text search path ─────────────────────────────────
            song = search_song(query)
            if not song:
                return f"[red]  ERR: NOT_FOUND: {query}[/red]"

        self.queue_manager.add_song(song)
        from utils.history_manager import add_history_entry
        add_history_entry("song", song.title, song.artist, f"{song.title} {song.artist}")

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

    def play_playlist(self, query: str):
        """Search for a Spotify playlist by name and play it."""
        from search_engine.url_resolver import search_spotify_playlist_by_name
        
        playlist_url = search_spotify_playlist_by_name(query)
        if not playlist_url:
            return f"[red]  ERR: NOT_FOUND: Could not find Spotify playlist for '{query}'[/red]"
            
        from utils.history_manager import add_history_entry
        add_history_entry("playlist", f"Playlist: {query}", "", query)
            
        # Hand off to the existing play_song which handles Spotify playlist URLs brilliantly
        return self.play_song(playlist_url)

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
        """Resume playback."""
        if self.mpv_player:
            self.mpv_player.resume()
            return "[bold green]  [RUN] PLAYBACK.RESUMED[/bold green]"

    def seek(self, offset: float) -> None:
        """Seek relatively by offset in seconds (+/-)."""
        if self.mpv_player and self.mpv_player.is_playing():
            self.mpv_player.seek_relative(offset)

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
