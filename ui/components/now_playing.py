"""
Now Playing Component — Premium reactive panel for track info and progress.
"""

from textual.widgets import Static
from textual.reactive import reactive
from ui.visualizer import get_visualizer_frame


class NowPlayingPanel(Static):
    """Displays current track info with rich visual hierarchy."""

    song_title:   reactive[str]  = reactive("No song playing")
    artist:       reactive[str]  = reactive("")
    mood_label:   reactive[str]  = reactive("—")
    progress_bar: reactive[str]  = reactive("")
    time_label:   reactive[str]  = reactive("00:00 / 00:00")
    visualizer:   reactive[str]  = reactive("")
    volume_bar:   reactive[str]  = reactive("")
    is_playing:   reactive[bool] = reactive(False)
    radio_on:     reactive[bool] = reactive(False)

    def render(self) -> str:
        # ── Play / Pause icon ───────────────────────────────
        state_icon = "[bold bright_cyan]▶[/bold bright_cyan]" if self.is_playing else "[bold bright_black]⏸[/bold bright_black]"

        # ── Mood badge ──────────────────────────────────────
        if self.mood_label and self.mood_label != "—":
            mood_badge = f"[bold reverse magenta] {self.mood_label} [/bold reverse magenta]"
        else:
            mood_badge = "[dim]— no mood set —[/dim]"

        # ── Radio badge ─────────────────────────────────────
        radio_badge = (
            "  [bold magenta]📻 RADIO[/bold magenta]"
            if self.radio_on else ""
        )

        # ── Song title line ─────────────────────────────────
        if self.song_title == "No song playing":
            title_line = (
                "\n"
                "  [bold bright_black]♪[/bold bright_black]  [dim]Nothing playing[/dim]\n"
                "  [dim]Type [bold]M!play <song>[/bold] to start[/dim]\n"
            )
            artist_line = ""
            progress_section = ""
            vol_section = ""
        else:
            # Truncate long titles gracefully
            max_title_len = 42
            display_title = (
                self.song_title[:max_title_len - 1] + "…"
                if len(self.song_title) > max_title_len
                else self.song_title
            )
            max_artist_len = 38
            display_artist = (
                self.artist[:max_artist_len - 1] + "…"
                if len(self.artist) > max_artist_len
                else self.artist
            )
            title_line  = f"\n  {state_icon} [bold bright_white]{display_title}[/bold bright_white]{radio_badge}\n"
            artist_line = f"  [dim]🎤  {display_artist}[/dim]\n"
            progress_section = (
                f"\n"
                f"  {self.progress_bar}\n"
                f"  [dim]{self.time_label}[/dim]\n"
            )
            vol_section = f"\n  {self.volume_bar}\n"

        # ── Visualizer ───────────────────────────────────────
        if self.visualizer:
            vis_line = f"\n  {self.visualizer}\n"
        else:
            vis_line = ""

        # ── Mood section ─────────────────────────────────────
        mood_line = f"\n  [dim]Vibe →[/dim]  {mood_badge}\n"

        # ── Header ───────────────────────────────────────────
        header = "[bold bright_cyan]◈  NOW PLAYING[/bold bright_cyan]\n"
        separator = "[dim]─────────────────────────────────────────────[/dim]"

        return (
            header
            + separator
            + title_line
            + artist_line
            + progress_section
            + vol_section
            + vis_line
            + mood_line
        )

    def update_state(self, controller) -> None:
        """Sync component state with playback controller."""
        song = controller.queue_manager.now_playing()
        player = controller.mpv_player

        self.is_playing = bool(player and player.is_playing())
        self.radio_on   = controller.radio_mode

        if song:
            self.song_title = song.title
            self.artist     = song.artist

            # ── Progress bar ────────────────────────────────
            if player:
                duration = player.get_duration() or getattr(song, "duration", 0) or 1
                position = player.get_position()

                mc, sc = divmod(int(position), 60)
                mt, st = divmod(int(duration), 60)
                self.time_label = f"{mc:02d}:{sc:02d}  ──  {mt:02d}:{st:02d}"

                bar_width = 40
                filled    = int(bar_width * (position / duration))
                empty     = bar_width - filled
                self.progress_bar = (
                    "[cyan]" + "▓" * filled + "[/cyan]"
                    + "[bright_black]" + "░" * empty + "[/bright_black]"
                )

                # ── Volume bar ───────────────────────────────
                vol          = player.get_volume()
                vol_filled   = int(vol / 10)
                vol_empty    = 10 - vol_filled
                self.volume_bar = (
                    "[dim]🔊[/dim] "
                    "[cyan]" + "█" * vol_filled + "[/cyan]"
                    + "[bright_black]" + "░" * vol_empty + "[/bright_black]"
                    + f" [dim]{vol}%[/dim]"
                )

            # ── Visualizer ───────────────────────────────────
            self.visualizer = get_visualizer_frame(36, is_playing=self.is_playing)
        else:
            self.song_title  = "No song playing"
            self.artist      = ""
            self.progress_bar = ""
            self.time_label   = "00:00 / 00:00"
            self.visualizer   = ""
            self.volume_bar   = ""

        mood_val        = controller.current_mood
        self.mood_label = mood_val.upper() if mood_val else "—"
