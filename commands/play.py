"""Play command — searches and adds to queue."""
from player.playback_controller import get_controller
from rich.console import Console

console = Console()

def play(args):
    if not args:
        console.print("[yellow]Usage: M!play <song name>[/yellow]")
        return

    query = " ".join(args)
    controller = get_controller()
    controller.play_song(query)