"""
M!speed — Control playback speed via MPV's native speed property.

Usage:
  M!speed          → Show current speed
  M!speed 1.5      → 1.5× speed (0.25 to 4.0 range)
  M!speed 0.75     → 75% slowdown
  M!speed normal   → Reset to 1.0×
  M!speed reset    → Reset to 1.0×
"""

from player.playback_controller import get_controller

_MIN_SPEED = 0.25
_MAX_SPEED = 4.0


def speed(args: list[str]) -> str:
    controller = get_controller()

    if not controller.mpv_player:
        return "[red]ERR: PLAYER_NOT_INIT[/red]"

    # No args — show current speed
    if not args:
        current = controller.mpv_player.get_speed()
        if current == 1.0:
            indicator = "[dim]⚡ SPEED:[/dim] [white]1.0× (normal)[/white]"
        elif current > 1.0:
            indicator = f"[bold bright_cyan]⚡ SPEED:[/bold bright_cyan] [white]{current:.2f}× (fast)[/white]"
        else:
            indicator = f"[bold yellow]⚡ SPEED:[/bold yellow] [white]{current:.2f}× (slow)[/white]"
        return (
            f"  {indicator}\n"
            f"  [dim]Set with: [bold]M!speed 1.5[/bold] · [bold]M!speed 0.75[/bold] · "
            f"[bold]M!speed normal[/bold][/dim]"
        )

    arg = args[0].lower()

    if arg in ("normal", "reset", "1", "1.0", "default"):
        controller.mpv_player.set_speed(1.0)
        return "[dim]⚡ SPEED → 1.0× (normal)[/dim]"

    try:
        rate = float(arg)
    except ValueError:
        return (
            "[red]ERR: INVALID_SPEED[/red] [dim]Use a number between "
            f"{_MIN_SPEED} and {_MAX_SPEED}, or 'normal'.[/dim]"
        )

    if not (_MIN_SPEED <= rate <= _MAX_SPEED):
        return (
            f"[red]ERR: OUT_OF_RANGE[/red] [dim]Speed must be between "
            f"[bold]{_MIN_SPEED}[/bold] and [bold]{_MAX_SPEED}[/bold].[/dim]"
        )

    controller.mpv_player.set_speed(rate)

    if rate > 1.0:
        label = f"[bold bright_cyan]⚡ SPEED → {rate:.2f}× (fast)[/bold bright_cyan]"
    elif rate < 1.0:
        label = f"[bold yellow]⚡ SPEED → {rate:.2f}× (slow)[/bold yellow]"
    else:
        label = "[dim]⚡ SPEED → 1.0× (normal)[/dim]"

    return f"  {label}"
