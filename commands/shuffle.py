"""
M!shuffle — Toggle or set shuffle mode for the playback queue.
Usage:
  M!shuffle        → Toggle shuffle on/off
  M!shuffle on     → Enable shuffle
  M!shuffle off    → Disable shuffle
"""

from player.playback_controller import get_controller


def shuffle(args: list[str]) -> str:
    controller = get_controller()
    qm = controller.queue_manager

    current = qm.shuffle_mode

    if not args:
        # Toggle
        qm.shuffle_mode = not current
    else:
        mode = args[0].lower()
        if mode in ("on", "1", "true", "yes"):
            qm.shuffle_mode = True
        elif mode in ("off", "0", "false", "no"):
            qm.shuffle_mode = False
        else:
            return (
                "[red]ERR: INVALID_ARG[/red] [dim]Use: "
                "[bold]M!shuffle on[/bold] · [bold]M!shuffle off[/bold][/dim]"
            )

    if qm.shuffle_mode:
        return (
            "[bold bright_cyan]🔀 SHUFFLE:ON[/bold bright_cyan]  "
            "[dim]Queue will play in random order.[/dim]"
        )
    else:
        return (
            "[dim]🔀 SHUFFLE:OFF[/dim]  "
            "[dim]Queue will play in order.[/dim]"
        )
