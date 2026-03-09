"""Volume command — controls MPV volume."""
from player.playback_controller import get_controller
from rich.console import Console

console = Console()

def volume(args):
    if not args:
        controller = get_controller()
        if controller.mpv_player:
            vol = controller.mpv_player.get_volume()
            console.print(f"  [dim]GAIN.LEVEL:[/dim] [bold cyan]{vol}%[/bold cyan]")
        return

    try:
        vol = int(args[0])
        controller = get_controller()
        controller.set_volume(vol)
    except ValueError:
        console.print("[red]ERR: INVALID_VOL_DATA[/red]")