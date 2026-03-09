"""Pause command."""
from player.playback_controller import get_controller

def pause(args):
    controller = get_controller()
    controller.pause()