"""
M!crossfade — Smooth audio transitions between tracks using MPV's lavfi afade filter.

Usage:
  M!crossfade          → Show current setting
  M!crossfade 3        → 3-second fade-out before each track ends
  M!crossfade off      → Disable crossfade (abrupt cuts)
"""

from player.playback_controller import get_controller

_MIN_CF = 1
_MAX_CF = 10


def crossfade(args: list[str]) -> str:
    controller = get_controller()
    current = getattr(controller, "crossfade_seconds", 0)

    if not args:
        if current > 0:
            return (
                f"[bold bright_cyan]〰 CROSSFADE:[/bold bright_cyan] "
                f"[white]{current}s[/white]  [dim](per-track fade-out)[/dim]\n"
                f"  [dim]Disable: [bold]M!crossfade off[/bold][/dim]"
            )
        return (
            "[dim]〰 CROSSFADE: OFF[/dim]\n"
            f"  [dim]Enable: [bold]M!crossfade 3[/bold] (1–{_MAX_CF}s)[/dim]"
        )

    arg = args[0].lower()

    if arg in ("off", "0", "disable", "none"):
        controller.crossfade_seconds = 0
        return "[dim]〰 CROSSFADE: OFF[/dim]  [dim]Tracks will cut immediately.[/dim]"

    try:
        secs = int(arg)
    except ValueError:
        return (
            "[red]ERR: INVALID_ARG[/red] [dim]Use a number of seconds "
            f"(1–{_MAX_CF}) or 'off'.[/dim]"
        )

    if not (_MIN_CF <= secs <= _MAX_CF):
        return (
            f"[red]ERR: OUT_OF_RANGE[/red] [dim]Crossfade must be "
            f"[bold]{_MIN_CF}[/bold]–[bold]{_MAX_CF}[/bold] seconds.[/dim]"
        )

    controller.crossfade_seconds = secs
    return (
        f"[bold bright_cyan]〰 CROSSFADE → {secs}s[/bold bright_cyan]  "
        f"[dim]Tracks will fade out {secs}s before ending.[/dim]"
    )
