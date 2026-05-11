"""
Queue Component — Premium reactive panel for upcoming tracks.
"""

from textual.widgets import Static
from textual.reactive import reactive


_IDLE_ART = (
    "  [bright_black]┌─────────────────────────────────┐[/bright_black]\n"
    "  [bright_black]│[/bright_black]  [dim]♪  Queue is empty[/dim]              [bright_black]│[/bright_black]\n"
    "  [bright_black]│[/bright_black]  [dim]Type [bold]M!play <song>[/bold] to add[/dim]  [bright_black]│[/bright_black]\n"
    "  [bright_black]└─────────────────────────────────┘[/bright_black]\n"
)


class QueuePanel(Static):
    """Displays the upcoming song queue with now-playing indicator."""

    queue_items:    reactive[list]         = reactive([])
    now_playing:    reactive[object | None] = reactive(None)

    def render(self) -> str:
        count = len(self.queue_items)

        # ── Header ───────────────────────────────────────────
        count_badge = (
            f" [bold cyan]({count})[/bold cyan]"
            if count > 0
            else " [dim](empty)[/dim]"
        )
        header    = f"[bold bright_cyan]◈  UP NEXT[/bold bright_cyan]{count_badge}\n"
        separator = "[dim]─────────────────────────────────────────────[/dim]\n"

        # ── Now playing row ───────────────────────────────────
        np_line = ""
        if self.now_playing:
            np_title  = getattr(self.now_playing, "title",  "?")
            np_artist = getattr(self.now_playing, "artist", "?")
            max_len = 28
            if len(np_title) > max_len:
                np_title = np_title[:max_len - 1] + "…"
            np_line = (
                f"  [bold bright_cyan]▶[/bold bright_cyan] "
                f"[bold white]{np_title}[/bold white]\n"
                f"    [dim]🎤 {np_artist}[/dim]\n"
                f"  [dim]{'─' * 36}[/dim]\n"
            )

        # ── Idle state ────────────────────────────────────────
        if not self.queue_items:
            return header + separator + np_line + _IDLE_ART

        # ── Queue rows ────────────────────────────────────────
        lines = []
        for i, song in enumerate(self.queue_items[:12]):
            title  = getattr(song, "title",  "?")
            artist = getattr(song, "artist", "?")

            max_title = 26
            if len(title) > max_title:
                title = title[:max_title - 1] + "…"

            num_badge = f"[dim cyan]{i + 1:>2}.[/dim cyan]"
            # Zebra: odd rows slightly dimmer
            if i % 2 == 0:
                row = f"  {num_badge} [white]{title}[/white]\n      [dim]{artist}[/dim]"
            else:
                row = f"  {num_badge} [dim white]{title}[/dim white]\n      [dim]{artist}[/dim]"
            lines.append(row)

        body = "\n".join(lines)

        # Overflow hint
        overflow = ""
        if count > 12:
            overflow = f"\n  [dim]… and {count - 12} more[/dim]"

        return header + separator + np_line + body + overflow

    def update_state(self, controller) -> None:
        """Sync component state with playback controller."""
        self.queue_items = controller.get_queue()
        self.now_playing  = controller.queue_manager.now_playing()
