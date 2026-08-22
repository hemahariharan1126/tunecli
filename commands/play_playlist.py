"""Play-playlist command — searches for a Spotify playlist by name and queues its tracks."""
from player.playback_controller import get_controller

def play_playlist(args):
    if not args:
        return "[yellow]Usage: M!play-playlist <playlist name>[/yellow]"

    query = " ".join(args)
    controller = get_controller()
    return controller.play_playlist(query)
