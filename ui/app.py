"""
TuneCLI App — Modular orchestrator for the reactive Textual UI.
"""

from textual import work
from textual.app import App, ComposeResult
from textual.widgets import RichLog, Input
from textual.containers import Container, Horizontal


from parser.command_parser import parse_command
from player.playback_controller import get_controller

# Modular Components
from ui.components.now_playing import NowPlayingPanel
from ui.components.queue import QueuePanel
from ui.components.input import CommandSuggester
from ui.components.modal import SelectionModal
from ui.components.status_bar import StatusBar
from ui.components.logo import LogoPanel

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
from commands.theme import theme as theme_func
from commands.lang import lang as lang_func
from commands.eq import eq as eq_func

# Theme system
from ui.themes import get_theme_css, get_theme_path, get_saved_theme

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
    "theme":     theme_func,
    "lang":      lang_func,
    "eq":        eq_func,
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
        self.controller        = get_controller()
        self.now_playing_panel = NowPlayingPanel()
        self.queue_panel       = QueuePanel()
        self.status_bar        = StatusBar()
        self.logo_panel        = LogoPanel()
        self.active_theme      = get_saved_theme()  # Load persisted theme

    def compose(self) -> ComposeResult:
        # ── Top HUD (docked via CSS) ─────────────────────────
        yield self.status_bar

        # ── Logo banner (docked below status bar) ────────────
        yield self.logo_panel

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
        yield RichLog(id="output_log", highlight=True, markup=True)

    def on_mount(self) -> None:
        """Initialize UI timer, focus, and apply saved theme."""
        self.set_interval(1.0, self._update_ui)
        self.query_one("#cmd_input", Input).focus()

        # Apply saved theme on startup (hot-swap if not default)
        if self.active_theme != "cyberpunk":
            self._apply_theme(self.active_theme, announce=False)

        # Welcome message
        log = self.query_one("#output_log", RichLog)
        log.write(
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
        raw          = event.value.strip()
        log_widget   = self.query_one("#output_log", RichLog)
        input_widget = self.query_one("#cmd_input", Input)
        input_widget.clear()

        if not raw:
            return

        parsed = parse_command(raw)
        if not parsed:
            log_widget.write(
                "[bold red]✗[/bold red] [dim]Unknown command.[/dim]  "
                "[dim]Try [bold]M!help[/bold][/dim]"
            )
            return

        handler = COMMAND_DISPATCH.get(parsed.name)
        if not handler:
            log_widget.write(
                f"[bold red]✗[/bold red] [dim]No handler for '[bold]{parsed.name}[/bold]'[/dim]"
            )
            return

        self.run_command_worker(handler, parsed.args, parsed.name)

    @work(thread=True)
    def run_command_worker(self, handler, args, name: str) -> None:
        """Executes a command in a background thread to keep UI responsive."""
        log_widget = self.query_one("#output_log", RichLog)

        # Immediate feedback line
        prefix = "LISTENING" if name == "find" else name.upper()
        self.call_from_thread(
            log_widget.write,
            f"[dim]  ⚡ CMD → {prefix}…[/dim]",
        )

        try:
            result = handler(args)

            if isinstance(result, dict) and result.get("type") == "selection":
                self.call_from_thread(self._launch_selection_modal, result)
            elif isinstance(result, dict) and result.get("type") == "theme_switch":
                self.call_from_thread(self._apply_theme, result["theme"])
            elif result:
                # RichLog.write() accepts both Rich Renderables and markup strings natively
                self.call_from_thread(log_widget.write, result)

            self.call_from_thread(self._update_ui)

        except Exception as e:
            self.call_from_thread(
                log_widget.write,
                f"[bold red]✗  ERR:[/bold red] [dim]{name.upper()} → {e}[/dim]",
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
                self.query_one("#output_log", RichLog).write(
                    "[dim]  ✕ Selection cancelled.[/dim]"
                )

        self.push_screen(SelectionModal(title, options), handle_selection)

    def _apply_theme(self, name: str, announce: bool = True) -> None:
        """Hot-swap the active CSS theme on the main thread."""
        try:
            from pathlib import Path
            path = Path(get_theme_path(name))
            self.stylesheet.read(path)
            self.refresh_css()
            self.active_theme = name
            if announce:
                log = self.query_one("#output_log", RichLog)
                label = name.upper()
                log.write(
                    f"[bold bright_cyan]◈  THEME → {label}[/bold bright_cyan]  "
                    f"[dim]applied & saved.[/dim]"
                )
        except Exception as e:
            log = self.query_one("#output_log", RichLog)
            log.write(f"[bold red]✗  THEME ERR:[/bold red] [dim]{e}[/dim]")
