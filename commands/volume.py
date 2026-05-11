"""Volume command — controls MPV volume."""
from player.playback_controller import get_controller
from rich.console import Console

def volume(args):
    controller = get_controller()
    if not args:
        if controller.mpv_player:
            vol = controller.mpv_player.get_volume()
            return f"  [dim]GAIN.LEVEL:[/dim] [bold cyan]{vol}%[/bold cyan]"
        return "[red]ERR: PLAYER_NOT_INIT[/red]"

    try:
        vol = int(args[0])
        return controller.set_volume(vol)
    except ValueError:
        return "[red]ERR: INVALID_VOL_DATA[/red]"