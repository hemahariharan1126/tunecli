"""
Playback Controller — Glue logic between the search engine, MPV player, and queue.
"""

from core.song import Song
from player.mpv_player import get_player
from player.queue_manager import QueueManager
from search_engine.yt_search import search_song
import logging

from rich.console import Console
from rich.text import Text

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
        self.seed_language = None # Locked language for recommendations
        self._is_refilling = False
        self._last_play_time = 0
        import time
        self._time_func = time.time
        
        # Register for auto-play when a song ends
        if self.mpv_player:
            self.mpv_player.set_eof_callback(self._on_song_end)

    def _on_song_end(self, event):
        """Called when MPV reaches the end of a file."""
        # For 'end-file', python-mpv provides an MpvEventEndFile object in event.data
        # This object has 'reason' and 'EOF' (constant 0) attributes
        try:
            data = getattr(event, 'data', None)
            if not data:
                return

            # Safely access the reason and EOF constant from the object
            reason = getattr(data, 'reason', None)
            eof_val = getattr(data, 'EOF', 0)
            
            if reason == eof_val:  # Natural EOF (Success)
                # Skip guard: if the song ended in less than 3 seconds, it's likely a failure
                elapsed = self._time_func() - self._last_play_time
                if elapsed < 3.0:
                    logging.warning(f"Song ended too quickly ({elapsed:.1f}s). Skipping auto-play to avoid runaway.")
                    self.console.print("\n[bold reverse red] ERR: PLAYBACK_FAIL [/bold reverse red] [dim]Skipping auto-play runaway.[/dim]")
                    return

                logging.info("Song ended naturally. Moving to next...")
                self._play_next()
                
                # If radio mode is on, check if we need more songs
                if self.radio_mode:
                    self._check_radio_refill()
            else:
                logging.debug(f"Song ended with reason code: {reason} (ignore auto-play)")
        except Exception as e:
            logging.error(f"Error processing EOF event: {e}")

    def play_song(self, query: str):
        """Search for a song and start playback or add to queue."""
        # Search for the song (Silenced background log)
        song = search_song(query)
        if not song:
            self.console.print(f"[red]  ERR: NOT_FOUND: {query}[/red]")
            return

        # Add to queue
        self.queue_manager.add_song(song)

        # Detect and lock seed language if this is the first song
        if self.seed_language is None:
            from recommender.recommender_engine import RecommenderEngine
            engine = RecommenderEngine()
            self.seed_language = engine.detect_language(f"{song.title} {song.artist}")
            logging.info(f"Language context locked to: {self.seed_language}")

        # If nothing is currently playing, start playback
        if self.mpv_player and not self.mpv_player.is_playing():
            self._play_next()
        else:
            self.console.print(f"  [bold cyan]+[/bold cyan] [white]{song.title}[/white] [dim]added to queue.[/dim]")

    def _play_next(self):
        """Immediately play the next song from the queue."""
        if not self.mpv_player:
            self.console.print("[red]ERR: MPV_NOT_INIT[/red]")
            return

        next_song = self.queue_manager.next_song()
        if next_song:
            self._last_play_time = self._time_func()
            self.mpv_player.play(next_song)
            # Silenced 'MOUNTED' print; the status bar handles now-playing info
            
            # If radio mode is on, keep the queue topped up
            if self.radio_mode:
                self._check_radio_refill()
        else:
            self.queue_manager.now_playing_song = None
            self.console.print("[dim]  INFO: QUEUE_EMPTY[/dim]")
            
            # If radio mode is on but queue is empty, try a refill from history
            if self.radio_mode:
                self._check_radio_refill()

    def _check_radio_refill(self):
        """Trigger a refill if the queue is running low."""
        if self._is_refilling:
            return
            
        queue_len = len(self.get_queue())
        if queue_len < 3:
            import threading
            threading.Thread(target=self._refill_radio, daemon=True).start()

    def _refill_radio(self):
        """Fetch recommendations and add to queue."""
        self._is_refilling = True
        try:
            from recommender.recommender_engine import RecommenderEngine
            engine = RecommenderEngine()
            
            # Use current song as seed, or last historical song if none playing
            seed_song = self.queue_manager.now_playing()
            if not seed_song and self.queue_manager.history:
                seed_song = self.queue_manager.history[-1]
                
            seed_query = f"{seed_song.title} {seed_song.artist}" if seed_song else "lofi beats"
            
            recs = engine.get_spotify_recommendations(
                seed_query, 
                limit=5, 
                target_lang=self.seed_language
            )
            
            if not recs:
                logging.warning("RADIO.ERR: No recommendations. Triggering bulletproof fallback.")
                # Hard fallback to keep the queue alive
                song = search_song("lofi chill beats official audio")
                if song:
                    self.queue_manager.add_song(song)
                else:
                    return

            for r in recs:
                # Search and add each to queue
                query = f"{r['title']} {r['artist']}"
                song = search_song(query)
                if song:
                    self.queue_manager.add_song(song)
                    # Silenced Radio queue log

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
            self.console.print("[bold yellow]  [HLD] PLAYBACK.STOPPED[/bold yellow]")

    def resume(self):
        if self.mpv_player:
            self.mpv_player.resume()
            self.console.print("[bold green]  [RUN] PLAYBACK.RESUMED[/bold green]")

    def stop(self):
        if self.mpv_player:
            self.mpv_player.stop()
            self.queue_manager.clear()
            self.radio_mode = False # Disable radio on hard stop
            self.console.print("[bold red]  [OFF] SYSTEM.HALT: QUEUE_CLEARED[/bold red]")

    def skip(self):
        """Skip current track and play next."""
        self.console.print("[dim]  SKIPPING.TRACK...[/dim]")
        if self.mpv_player:
            self.mpv_player.stop()
        self._play_next()

    def prev(self):
        """Go back to previous track if history exists."""
        prev_song = self.queue_manager.prev_song()
        if prev_song and self.mpv_player:
            self._last_play_time = self._time_func()
            self.mpv_player.play(prev_song)
            self.console.print(f"  [bold magenta]«[/bold magenta] [white]RESTORING:[/white] [cyan]{prev_song.title}[/cyan]")
        else:
            self.console.print("[yellow]  WARN: NO_HISTORY_AVAILABLE[/yellow]")

    def set_volume(self, volume: int):
        if self.mpv_player:
            self.mpv_player.set_volume(volume)
            self.console.print(f"  [dim]GAIN.SET:[/dim] [bold cyan]{volume}%[/bold cyan]")

    def get_queue(self):
        return self.queue_manager.get_queue()

    def set_mood(self, mood: str):
        self.current_mood = mood
        self.console.print(f"  [dim]VIBE.LOCK:[/dim] [bold magenta]{mood.upper()}[/bold magenta]")

# Global controller instance
controller = PlaybackController()

def get_controller():
    return controller
