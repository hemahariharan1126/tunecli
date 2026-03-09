"""
Terminal UI — Main Textual application for TuneCLI.
"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Input, Log
from textual.reactive import reactive
from textual.containers import Container, Horizontal, Vertical

from parser.command_parser import parse_command
from player.playback_controller import PlaybackController
from api.audio_features import AudioFeatureService
from api.ytmusic_client import YTMusicClient
from recommender.recommender_engine import RecommenderEngine
from ui.theme import APP_NAME, BORDER_STYLE
from commands import play, pause, resume, skip, stop, queue, mood, recommend, volume, help as help_cmd


COMMAND_DISPATCH = {
    "play":      play,
    "pause":     pause,
    "resume":    resume,
    "skip":      skip,
    "stop":      stop,
    "queue":     queue,
    "mood":      mood,
    "recommend": recommend,
    "volume":    volume,
    "help":      help_cmd,
}


class NowPlayingPanel(Static):
    """Displays current track info."""

    DEFAULT_CSS = """
    NowPlayingPanel {
        border: round cyan;
        padding: 1 2;
        height: 12;
    }
    """

    song_title: reactive[str] = reactive("No song playing")
    artist: reactive[str] = reactive("")
    mood_label: reactive[str] = reactive("—")
    quality_label: reactive[str] = reactive("—")
    speed_label: reactive[str] = reactive("— Mbps")

    def render(self) -> str:
        return (
            f"[bold bright_cyan]🎵 {APP_NAME}[/bold bright_cyan]\n\n"
            f"[bold bright_white]▶ Now Playing[/bold bright_white]\n"
            f"  [bold]{self.song_title}[/bold]\n"
            f"  [dim]{self.artist}[/dim]\n\n"
            f"  [magenta]Mood:[/magenta]    {self.mood_label}\n"
            f"  [green]Network:[/green] {self.speed_label}   "
            f"  [cyan]Quality:[/cyan] {self.quality_label}\n"
        )


class QueuePanel(Static):
    """Displays the upcoming song queue."""

    DEFAULT_CSS = """
    QueuePanel {
        border: round bright_black;
        padding: 1 2;
    }
    """

    queue_items: reactive[list] = reactive([])

    def render(self) -> str:
        header = "[bold bright_blue]📋 Up Next[/bold bright_blue]\n"
        if not self.queue_items:
            return header + "  [dim]Queue is empty[/dim]"
        lines = [
            f"  [dim]{i+1}.[/dim] {s.get('title','?')} — {s.get('artist','?')}"
            for i, s in enumerate(self.queue_items[:8])
        ]
        return header + "\n".join(lines)


class TuneCLIApp(App):
    """Main TuneCLI Textual application."""

    CSS = """
    Screen {
        background: #0d0d1a;
    }
    Input {
        border: round cyan;
        margin: 0 0 0 0;
    }
    Log {
        border: round bright_black;
        height: 8;
        padding: 0 1;
    }
    """

    TITLE = APP_NAME
    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.controller = PlaybackController()
        self.now_playing_panel = NowPlayingPanel()
        self.queue_panel = QueuePanel()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            self.now_playing_panel,
            self.queue_panel,
        )
        yield Input(placeholder="Enter command: M!play <song> · M!help", id="cmd_input")
        yield Log(id="output_log", highlight=True)
        yield Footer()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        raw = event.value.strip()
        log_widget = self.query_one("#output_log", Log)
        input_widget = self.query_one("#cmd_input", Input)
        input_widget.clear()

        if not raw:
            return

        parsed = parse_command(raw)
        if not parsed:
            log_widget.write_line(f"[red]Unknown command. Try M!help[/red]")
            return

        handler = COMMAND_DISPATCH.get(parsed.name)
        if handler:
            result = handler.execute(parsed.args, self.controller)
            log_widget.write_line(result)
            self._refresh_panels()
        else:
            log_widget.write_line(f"[red]Handler not found for '{parsed.name}'[/red]")

    def _refresh_panels(self):
        """Sync the UI panels with current player state."""
        song = self.controller.current_song
        if song:
            self.now_playing_panel.song_title = song.get("title", "Unknown")
            self.now_playing_panel.artist = song.get("artist", "")
        else:
            self.now_playing_panel.song_title = "No song playing"
            self.now_playing_panel.artist = ""

        mood_val = self.controller.current_mood
        self.now_playing_panel.mood_label = mood_val.capitalize() if mood_val else "—"
        self.queue_panel.queue_items = self.controller.get_queue()
