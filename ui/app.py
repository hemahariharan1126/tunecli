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

# Theme system
from ui.themes import get_theme_css, get_theme_path, get_saved_theme
import importlib

# Lazy Command Dispatcher mapping command name to (module_name, function_name)
_COMMAND_REGISTRY = {
    "play":          ("commands.play", "play"),
    "play-playlist": ("commands.play_playlist", "play_playlist"),
    "pause":         ("commands.pause", "pause"),
    "resume":        ("commands.resume", "resume"),
    "skip":          ("commands.skip", "skip"),
    "stop":          ("commands.stop", "stop"),
    "queue":         ("commands.queue", "show_queue"),
    "mood":          ("commands.mood", "mood"),
    "recommend":     ("commands.recommend", "recommend"),
    "volume":        ("commands.volume", "volume"),
    "help":          ("commands.help", "help_command"),
    "find":          ("commands.find", "find"),
    "scenario":      ("commands.scenario", "scenario"),
    "radio":         ("commands.radio", "radio"),
    "next":          ("commands.next", "next_command"),
    "prev":          ("commands.prev", "prev"),
    "theme":         ("commands.theme", "theme"),
    "lang":          ("commands.lang", "lang"),
    "eq":            ("commands.eq", "eq"),
    "reorder":       ("commands.reorder", "reorder"),
    "ask":           ("commands.ask", "ask"),
    "remove":        ("commands.remove", "remove"),
    "source":        ("commands.source", "source"),
    "loop":          ("commands.loop", "loop"),
    "update":        ("commands.update", "update_command"),
    "hist":          ("commands.hist", "show_history"),
}

class _LazyCommandDispatch(dict):
    """Lazy dictionary that imports command modules only upon first execution."""
    def __init__(self, registry: dict):
        super().__init__()
        self._registry = registry
        self._cache = {}

    def __contains__(self, key):
        return key in self._registry

    def keys(self):
        return self._registry.keys()

    def get(self, key, default=None):
        if key not in self._registry:
            return default
        if key not in self._cache:
            mod_name, func_name = self._registry[key]
            mod = importlib.import_module(mod_name)
            self._cache[key] = getattr(mod, func_name)
        return self._cache[key]

    def __getitem__(self, key):
        handler = self.get(key)
        if handler is None:
            raise KeyError(key)
        return handler

COMMAND_DISPATCH = _LazyCommandDispatch(_COMMAND_REGISTRY)


class TuneCLIApp(App):
    """Main TuneCLI Textual application orchestrator."""

    CSS_PATH = "styles/theme.tcss"
    TITLE    = "M! TuneCLI"

    BINDINGS = [
        ("ctrl+c", "quit",             "Quit"),
        ("ctrl+q", "quit",             "Quit"),
        ("space",  "toggle_playback",  "Pause/Resume"),
        ("right",  "seek_forward",     "Seek +5s"),
        ("left",   "seek_backward",    "Seek -5s"),
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

        def _safe_log_write(msg: str) -> None:
            try:
                self.call_from_thread(log.write, msg)
            except Exception:
                log.write(msg)
        self.controller._app_log_callback = _safe_log_write
        
        self._check_for_updates()

    @work(thread=True)
    def _check_for_updates(self) -> None:
        """Silently check for remote updates in the background on startup."""
        import subprocess
        import os
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            # Fetch silently
            subprocess.run(["git", "fetch", "origin", "master"], cwd=base_dir, capture_output=True, timeout=10)
            # Count behind
            res = subprocess.run(["git", "rev-list", "--count", "HEAD..origin/master"], cwd=base_dir, capture_output=True, text=True, timeout=5)
            count = int(res.stdout.strip())
            if count > 0:
                msg = f"\n[bold bright_green]↑ UPDATE AVAILABLE[/bold bright_green] There are [white]{count}[/white] new updates! Type [bold]M!update[/bold] to install them."
                if hasattr(self.controller, "_app_log_callback") and self.controller._app_log_callback:
                    self.controller._app_log_callback(msg)
        except Exception:
            pass  # Fail silently to not disturb the user if Git or network is broken

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

    def action_seek_forward(self) -> None:
        self.controller.seek(5)
        self._update_ui()

    def action_seek_backward(self) -> None:
        self.controller.seek(-5)
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

        if parsed.name in ("exit", "quit", "end"):
            self.exit()
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
                cmd_name = selected.get("command", "play")
                
                if cmd_name == "play-playlist":
                    query = selected.get("query", selected['title'])
                    self.run_command_worker(COMMAND_DISPATCH["play-playlist"], [query], "play-playlist")
                else:
                    if "query" in selected and selected["query"]:
                        query = selected["query"]
                    else:
                        query = f"{selected['title']} {selected['artist']}"
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
