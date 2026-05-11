"""Scenario command — analyzes a story and adds matching songs to queue."""
from player.playback_controller import get_controller
from api.llm_client import get_llm_client
from search_engine.yt_search import search_song
from rich.console import Group
from rich.panel import Panel
from rich.text import Text
import logging
import time

def scenario(args):
    if not args:
        return "[yellow]Usage: M!scenario \"your story here\"[/yellow]"

    story = " ".join(args)
    
    llm = get_llm_client()
    analysis = llm.analyze_scenario(story)
    
    if "error" in analysis:
        return f"[bold red]ERR: LLM_ANALYSIS_FAILED: {analysis['error']}[/bold red]"

    mood = analysis.get("mood", "unknown")
    tone = analysis.get("tone", "unknown")
    lang = analysis.get("language", "en")
    queries = analysis.get("queries", [])
    reasoning = analysis.get("reasoning", "")

    # 1. Create Analysis Panel
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

    controller = get_controller()
    
    # Sync controller state
    from config import MOOD_MAP
    if mood.lower() in MOOD_MAP:
        controller.set_mood(mood.lower())
    controller.seed_language = lang

    # 2. Search and collect track results
    track_results = [Text("\n⚡ FETCHING.TRACKS...", style="dim")]
    found_any = False
    
    for q in queries:
        song = search_song(q)
        if song:
            controller.queue_manager.add_song(song)
            track_results.append(Text.assemble(
                ("  ✓ ", "bold green"), (f"{song.title}", "white"), (" added.", "dim")
            ))
            found_any = True
        else:
            track_results.append(Text.assemble(
                ("  ✗ ", "bold red"), (f"Not found: {q}", "dim")
            ))

    # 3. Final Status Message
    if found_any:
        if controller.mpv_player and not controller.mpv_player.is_playing():
            controller._play_next()
        status_msg = Text("\n SUCCESS: Scenario soundtrack ready!", style="bold reverse green")
    else:
        status_msg = Text("\n FAILED: No matching tracks resolved.", style="bold reverse red")

    # 4. Return everything as a Group for the TUI Log
    return Group(
        info_panel,
        *track_results,
        status_msg
    )
