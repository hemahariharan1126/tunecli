"""
M!loop — Spotify-style loop control for TuneCLI.
Usage:
  M!loop        → Show current loop mode
  M!loop off    → No looping
  M!loop one    → Loop current song endlessly
  M!loop all    → Loop entire queue endlessly
"""
from player.playback_controller import get_controller

VALID_MODES = {"off", "one", "all"}

MODE_ICONS = {
    "none": "[dim]⟳  LOOP:OFF[/dim]",
    "one":  "[bold bright_cyan]🔂 LOOP:ONE[/bold bright_cyan]",
    "all":  "[bold bright_cyan]🔁 LOOP:ALL[/bold bright_cyan]",
}

MODE_MAP = {
    "off": "none",
    "one": "one",
    "all": "all",
}

def loop(args: list[str]) -> str:
    controller = get_controller()

    # No args → show current state
    if not args:
        current = controller.queue_manager.repeat_mode
        label = MODE_ICONS.get(current, current)
        return (
            f"[bold]Loop Mode:[/bold] {label}\n"
            f"  [dim]Set with: [bold]M!loop off[/bold] · "
            f"[bold]M!loop one[/bold] · [bold]M!loop all[/bold][/dim]"
        )

    mode_input = args[0].lower()
    if mode_input not in VALID_MODES:
        return (
            f"[bold red]ERR:[/bold red] [dim]Unknown mode '[bold]{args[0]}[/bold]'. "
            f"Valid: [bold]off[/bold] · [bold]one[/bold] · [bold]all[/bold][/dim]"
        )

    internal_mode = MODE_MAP[mode_input]
    controller.queue_manager.set_repeat(internal_mode)

    label = MODE_ICONS.get(internal_mode, internal_mode)
    return f"[bold bright_cyan]LOOP.MODE[/bold bright_cyan] [dim]set to[/dim] {label}"
