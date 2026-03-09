"""Previous command — plays the last song from history."""
from player.playback_controller import get_controller

def prev(args):
    controller = get_controller()
    controller.prev()
