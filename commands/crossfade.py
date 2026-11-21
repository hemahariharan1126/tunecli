"""
M!crossfade — Audio transition settings.

Note on architecture:
A single MPV process cannot play two independent audio streams simultaneously with true
waveform overlap. TuneCLI applies an audio fade-in at the beginning of each track to soften
abrupt track starts. This command controls that transition duration.

Usage:
  M!crossfade          → Show current setting
  M!crossfade 3        → 3-second fade-in on track start
  M!crossfade off      → Disable fade (immediate playback)
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
                f"[bold bright_cyan]〰 TRANSITION FADE:[/bold bright_cyan] "
                f"[white]{current}s[/white]  [dim](fade-in on track start)[/dim]\n"
                f"  [dim]Disable: [bold]M!crossfade off[/bold][/dim]"
            )
        return (
            "[dim]〰 TRANSITION FADE: OFF[/dim]\n"
            f"  [dim]Enable: [bold]M!crossfade 3[/bold] (1–{_MAX_CF}s fade-in)[/dim]"
        )

    arg = args[0].lower()

    if arg in ("off", "0", "disable", "none"):
        controller.crossfade_seconds = 0
        return "[dim]〰 TRANSITION FADE: OFF[/dim]  [dim]Tracks will start with immediate full volume.[/dim]"

    try:
        secs = int(arg)
    except ValueError:
        return (
            "[red]ERR: INVALID_ARG[/red] [dim]Use a number of seconds "
            f"(1–{_MAX_CF}) or 'off'.[/dim]"
        )

    if not (_MIN_CF <= secs <= _MAX_CF):
        return (
            f"[red]ERR: OUT_OF_RANGE[/red] [dim]Fade duration must be "
            f"[bold]{_MIN_CF}[/bold]–[bold]{_MAX_CF}[/bold] seconds.[/dim]"
        )

    controller.crossfade_seconds = secs
    return (
        f"[bold bright_cyan]✔ TRANSITION FADE ENABLED:[/bold bright_cyan] "
        f"[white]{secs}s[/white] [dim]fade-in applied on upcoming tracks.[/dim]"
    )

    controller.crossfade_seconds = secs
    return (
        f"[bold bright_cyan]〰 CROSSFADE → {secs}s[/bold bright_cyan]  "
        f"[dim]Tracks will fade out {secs}s before ending.[/dim]"
    )
