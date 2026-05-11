"""Mood command — sets the current listening mood."""
from player.playback_controller import get_controller
from rich.console import Console

def mood(args):
    if not args:
        return "[yellow]Usage: M!mood <vibe> (e.g. happy, chill, focus)[/yellow]"

    mood_value = " ".join(args)
    controller = get_controller()
    return controller.set_mood(mood_value)