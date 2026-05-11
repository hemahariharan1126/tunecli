"""Play command — searches and adds to queue."""
from player.playback_controller import get_controller

def play(args):
    if not args:
        return "[yellow]Usage: M!play <song name>[/yellow]"

    query = " ".join(args)
    controller = get_controller()
    return controller.play_song(query)