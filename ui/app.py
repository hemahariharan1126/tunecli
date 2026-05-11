"""
TuneCLI App — Modular orchestrator for the reactive Textual UI.
"""

from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Log, Input
from textual.containers import Container, Horizontal
from rich.console import Console

from parser.command_parser import parse_command
from player.playback_controller import get_controller

# Modular Components
from ui.components.now_playing import NowPlayingPanel
from ui.components.queue import QueuePanel
from ui.components.input import CommandSuggester
from ui.components.modal import SelectionModal
from ui.components.status_bar import StatusBar

# Command Dispatch
from commands.play import play as play_func
from commands.pause import pause as pause_func
from commands.resume import resume as resume_func
from commands.skip import skip as skip_func
from commands.stop import stop as stop_func
from commands.queue import show_queue
from commands.mood import mood as mood_func
from commands.recommend import recommend as recommend_func
from commands.volume import volume as volume_func
from commands.help import help_command
from commands.find import find as find_func
from commands.scenario import scenario as scenario_func
from commands.radio import radio as radio_func
from commands.next import next_command
from commands.prev import prev as prev_func

COMMAND_DISPATCH = {
    "play":      play_func,
    "pause":     pause_func,
    "resume":    resume_func,
    "skip":      skip_func,
    "stop":      stop_func,
    "queue":     show_queue,
    "mood":      mood_func,
    "recommend": recommend_func,
    "volume":    volume_func,
    "help":      help_command,
    "find":      find_func,
    "scenario":  scenario_func,
    "radio":     radio_func,
    "next":      next_command,
    "prev":      prev_func,
}


class TuneCLIApp(App):
    """Main TuneCLI Textual application orchestrator."""

    CSS_PATH = "styles/theme.tcss"
    TITLE    = "M! TuneCLI"

    BINDINGS = [
        ("ctrl+c", "quit",             "Quit"),
        ("ctrl+q", "quit",             "Quit"),
        ("space",  "toggle_playback",  "Pause/Resume"),
        ("n",      "next_track",       "Next"),
        ("p",      "prev_track",       "Prev"),
        ("plus",   "volume_up",        "Vol+"),
        ("minus",  "volume_down",      "Vol-"),
    ]

    def __init__(self):
        super().__init__()
        self.controller       = get_controller()
        self.now_playing_panel = NowPlayingPanel()
        self.queue_panel       = QueuePanel()
        self.status_bar        = StatusBar()

    def compose(self) -> ComposeResult:
        # ── Top HUD (docked via CSS) ─────────────────────────
        yield self.status_bar

        # ── Main panels ──────────────────────────────────────
        yield Container(
            Horizontal(
                self.now_playing_panel,
                self.queue_panel,
            ),
            id="main_container",
        )

        # ── Command input ─────────────────────────────────────
        yield Input(
            placeholder="  ⚡  M!play <song>   ·   M!help   ·   M!radio on",
            id="cmd_input",
            suggester=CommandSuggester(list(COMMAND_DISPATCH.keys())),
        )

        # ── Output log ────────────────────────────────────────
        yield Log(id="output_log", highlight=True)

    def on_mount(self) -> None:
        """Initialize UI timer and focus."""
        self.set_interval(1.0, self._update_ui)
        self.query_one("#cmd_input", Input).focus()

        # Welcome message
        log = self.query_one("#output_log", Log)
        log.write_line(
            "[bold bright_cyan]⚡ M! TuneCLI — Ready[/bold bright_cyan]  "
            "[dim]Type [bold]M!help[/bold] to see all commands.[/dim]"
        )

    def _update_ui(self) -> None:
        """Fetch latest state from controller and update all UI panels."""
        self.now_playing_panel.update_state(self.controller)
        self.queue_panel.update_state(self.controller)
        self.status_bar.update_state(self.controller)

    # ── Keyboard actions ─────────────────────────────────────

    def action_toggle_playback(self) -> None:
        if self.controller.mpv_player and self.controller.mpv_player.is_playing():
            self.controller.pause()
        else:
            self.controller.resume()
        self._update_ui()

    def action_next_track(self) -> None:
        self.controller.skip()
        self._update_ui()

    def action_prev_track(self) -> None:
        self.controller.prev()
        self._update_ui()

    def action_volume_up(self) -> None:
        if self.controller.mpv_player:
            vol = self.controller.mpv_player.get_volume()
            self.controller.set_volume(min(vol + 5, 100))
        self._update_ui()

    def action_volume_down(self) -> None:
        if self.controller.mpv_player:
            vol = self.controller.mpv_player.get_volume()
            self.controller.set_volume(max(vol - 5, 0))
        self._update_ui()

    # ── Command input ─────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        raw         = event.value.strip()
        log_widget  = self.query_one("#output_log", Log)
        input_widget = self.query_one("#cmd_input", Input)
        input_widget.clear()

        if not raw:
            return

        parsed = parse_command(raw)
        if not parsed:
            log_widget.write_line(
                "[bold red]✗[/bold red] [dim]Unknown command.[/dim]  "
                "[dim]Try [bold]M!help[/bold][/dim]"
            )
            return

        handler = COMMAND_DISPATCH.get(parsed.name)
        if not handler:
            log_widget.write_line(
                f"[bold red]✗[/bold red] [dim]No handler for '[bold]{parsed.name}[/bold]'[/dim]"
            )
            return

        self.run_command_worker(handler, parsed.args, parsed.name)

    @work(thread=True)
    def run_command_worker(self, handler, args, name: str) -> None:
        """Executes a command in a background thread to keep UI responsive."""
        log_widget = self.query_one("#output_log", Log)

        # Immediate feedback line
        prefix = "LISTENING" if name == "find" else name.upper()
        self.call_from_thread(
            log_widget.write,
            f"[dim]  ⚡ CMD → {prefix}…[/dim]\n",
        )

        try:
            result = handler(args)

            if isinstance(result, dict) and result.get("type") == "selection":
                self.call_from_thread(self._launch_selection_modal, result)
            elif result:
                if not isinstance(result, str):
                    capture_console = Console(
                        force_terminal=True,
                        width=log_widget.content_size.width or 80,
                    )
                    with capture_console.capture() as capture:
                        capture_console.print(result)
                    result = capture.get()

                self.call_from_thread(log_widget.write, f"{result}\n")

            self.call_from_thread(self._update_ui)

        except Exception as e:
            self.call_from_thread(
                log_widget.write,
                f"[bold red]✗  ERR:[/bold red] [dim]{name.upper()} → {e}[/dim]\n",
            )

    def _launch_selection_modal(self, data: dict) -> None:
        """Handle structured command results by showing a selection modal."""
        options = data.get("options", [])
        title   = data.get("title", "Select Track")

        def handle_selection(index: int) -> None:
            if index >= 0:
                selected = options[index]
                query    = f"{selected['title']} {selected['artist']}"
                self.run_command_worker(COMMAND_DISPATCH["play"], [query], "play")
            else:
                self.query_one("#output_log", Log).write_line(
                    "[dim]  ✕ Selection cancelled.[/dim]"
                )

        self.push_screen(SelectionModal(title, options), handle_selection)
