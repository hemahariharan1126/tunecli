"""Resume command."""
from player.playback_controller import get_controller

def resume(args):
    controller = get_controller()
    controller.resume()
