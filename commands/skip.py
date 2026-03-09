"""Skip command."""
from player.playback_controller import get_controller

def skip(args):
    controller = get_controller()
    controller.skip()
