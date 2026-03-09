"""Mood command — sets the current listening mood."""
from player.playback_controller import get_controller
from rich.console import Console

console = Console()

def mood(args):
    if not args:
        console.print("[yellow]Usage: M!mood <vibe> (e.g. happy, chill, focus)[/yellow]")
        return

    mood_value = " ".join(args)
    controller = get_controller()
    controller.set_mood(mood_value)