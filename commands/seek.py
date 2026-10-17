"""
M!seek — Jump to a specific position in the currently playing song.

Usage:
  M!seek 1:30      → Jump to 1 minute 30 seconds (absolute)
  M!seek 90        → Jump to 90 seconds (absolute)
  M!seek +30       → Seek forward 30 seconds (relative)
  M!seek -15       → Seek backward 15 seconds (relative)
  M!seek 50%       → Jump to 50% of the song duration
"""

from player.playback_controller import get_controller


def _parse_seek_arg(arg: str, duration: float) -> tuple[float | None, str]:
    """
    Parse seek argument. Returns (seconds: float | None, mode: str).
    mode is 'absolute' or 'relative'.
    """
    arg = arg.strip()

    # Percentage: e.g. "50%"
    if arg.endswith("%"):
        try:
            pct = float(arg[:-1]) / 100.0
            return pct * duration, "absolute"
        except ValueError:
            return None, "absolute"

    # Relative: +30 or -15
    if arg.startswith("+") or arg.startswith("-"):
        sign = 1 if arg.startswith("+") else -1
        raw = arg[1:]
        try:
            return sign * float(raw), "relative"
        except ValueError:
            return None, "relative"

    # MM:SS format: e.g. "1:30"
    if ":" in arg:
        parts = arg.split(":")
        try:
            if len(parts) == 2:
                return int(parts[0]) * 60 + float(parts[1]), "absolute"
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2]), "absolute"
        except ValueError:
            return None, "absolute"

    # Plain seconds: e.g. "90"
    try:
        return float(arg), "absolute"
    except ValueError:
        return None, "absolute"


def seek(args: list[str]) -> str:
    controller = get_controller()

    if not controller.mpv_player:
        return "[red]ERR: PLAYER_NOT_INIT[/red]"

    if not controller.mpv_player.is_playing():
        return "[yellow]WARN: NOTHING_PLAYING[/yellow]"

    if not args:
        pos = controller.mpv_player.get_position()
        dur = controller.mpv_player.get_duration() or 1
        mp, sp = divmod(int(pos), 60)
        md, sd = divmod(int(dur), 60)
        pct = int(pos / dur * 100) if dur else 0
        return (
            f"[dim]⏱ POSITION:[/dim] [white]{mp:02d}:{sp:02d}[/white]"
            f" [dim]/ {md:02d}:{sd:02d}  ({pct}%)[/dim]\n"
            f"  [dim]Usage: [bold]M!seek 1:30[/bold] · "
            f"[bold]M!seek +30[/bold] · [bold]M!seek 50%[/bold][/dim]"
        )

    arg = " ".join(args)
    dur = controller.mpv_player.get_duration() or 0
    seconds, mode = _parse_seek_arg(arg, dur)

    if seconds is None:
        return (
            "[red]ERR: INVALID_SEEK_ARG[/red] [dim]Use: "
            "[bold]M!seek 1:30[/bold] · [bold]M!seek +30[/bold] · "
            "[bold]M!seek 50%[/bold][/dim]"
        )

    if mode == "absolute":
        seconds = max(0.0, min(seconds, dur))
        controller.mpv_player.seek_to(seconds)
        m, s = divmod(int(seconds), 60)
        return f"[dim]⏩ SEEK →[/dim] [white]{m:02d}:{s:02d}[/white]"
    else:
        controller.mpv_player.seek_relative(seconds)
        direction = "⏩" if seconds >= 0 else "⏪"
        sign = "+" if seconds >= 0 else ""
        return f"[dim]{direction} SEEK {sign}{int(seconds)}s[/dim]"
