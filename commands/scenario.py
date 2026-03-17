"""Scenario command — analyzes a story and adds matching songs to queue."""
from player.playback_controller import get_controller
from api.llm_client import get_llm_client
from search_engine.yt_search import search_song
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import logging
import time

console = Console()

def scenario(args):
    if not args:
        console.print("[yellow]Usage: M!scenario \"your story here\"[/yellow]")
        return

    story = " ".join(args)
    console.print(f"\n[dim]✨ ANALYZING.SCENARIO...[/dim]")
    
    llm = get_llm_client()
    analysis = llm.analyze_scenario(story)
    
    if "error" in analysis:
        console.print(f"[bold red]ERR: LLM_ANALYSIS_FAILED: {analysis['error']}[/bold red]")
        return

    mood = analysis.get("mood", "unknown")
    tone = analysis.get("tone", "unknown")
    lang = analysis.get("language", "en")
    queries = analysis.get("queries", [])
    reasoning = analysis.get("reasoning", "")

    # Display analysis results
    info_panel = Panel(
        Text.assemble(
            ("MOOD: ", "bold cyan"), (f"{mood.upper()}\n", "white"),
            ("TONE: ", "bold cyan"), (f"{tone.upper()}\n", "white"),
            ("LANG: ", "bold cyan"), (f"{lang.upper()}\n", "white"),
            ("\n", ""),
            (f"{reasoning}", "italic dim")
        ),
        title="[bold magenta]SCENARIO.ANALYSIS[/bold magenta]",
        border_style="cyan"
    )
    console.print(info_panel)

    controller = get_controller()
    
    # Set the mood in the controller if it's one of the known ones
    from config import MOOD_MAP
    if mood.lower() in MOOD_MAP:
        controller.set_mood(mood.lower())
    
    # Update seed language for future recommendations
    controller.seed_language = lang

    # Search and add songs to queue
    console.print("[dim]  FETCHING.MATCHING.TRACKS...[/dim]")
    
    found_any = False
    for q in queries:
        console.print(f"  [cyan]>[/cyan] [dim]Searching:[/dim] {q}", end="\r")
        song = search_song(q)
        if song:
            controller.queue_manager.add_song(song)
            console.print(f"  [bold green]✓[/bold green] [white]{song.title}[/white] [dim]added.[/dim]")
            found_any = True
        else:
            console.print(f"  [bold red]✗[/bold red] [dim]Not found:[/dim] {q}")

    if found_any:
        # If nothing is currently playing, start playback
        if controller.mpv_player and not controller.mpv_player.is_playing():
            controller._play_next()
        console.print("\n[bold reverse green] SUCCESS [/bold reverse green] [white]Scenario soundtrack ready![/white]")
    else:
        console.print("\n[bold reverse red] FAILED [/bold reverse red] [white]Could not find any songs for this scenario.[/white]")
