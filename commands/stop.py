"""Stop command."""
from player.playback_controller import get_controller

def stop(args):
    controller = get_controller()
    return controller.stop()
