"""Recommend command — adds related songs to the queue."""
from player.playback_controller import get_controller
from recommender.recommender_engine import RecommenderEngine
from search_engine.yt_search import search_song
from rich.console import Console
import logging

console = Console()
# Recommender engine instance
recommender = RecommenderEngine()

def recommend(args):
    """
    M!recommend
    Finds songs similar to the current one using Spotify and adds them to the queue.
    """
    controller = get_controller()
    current_song = controller.queue_manager.now_playing()

    if not current_song:
        console.print("[red]ERR: NO_TRACK_FOR_ANALYSIS[/red]")
        return

    console.print(f"\n[bold magenta]⚡ ANALYZING.VIBE:[/bold magenta] [cyan]{current_song.title}[/cyan]")
    
    # 1. Get high-quality recommendations from Spotify (with language guard)
    recommendations = recommender.get_spotify_recommendations(
        f"{current_song.title} {current_song.artist}",
        target_lang=controller.seed_language
    )

    if not recommendations:
        console.print("[yellow]WARN: NO_MATCHES_FOUND[/yellow]")
        return

    # 2. Resolve those songs on YouTube and add to queue
    console.print(f"[dim]Found {len(recommendations)} matches. Resolving streams...[/dim]")
    
    added_count = 0
    for rec in recommendations:
        query = f"{rec['title']} {rec['artist']}"
        console.print(f"  [dim]SCANNING.YT: {query}[/dim]", end="\r")
        
        song = search_song(query)
        if song:
            controller.queue_manager.add_song(song)
            console.print(f"  [bold cyan]+[/bold cyan] {song.title} [dim]by {song.artist}[/dim]       ")
            added_count += 1
        else:
            console.print(f"  [red]![/red] SKIPPED: {query} [dim](NOT_FOUND)[/dim]             ")

    if added_count > 0:
        console.print(f"\n[bold reverse green] SUCCESS [/bold reverse green] Added {added_count} tracks to queue.")
    else:
        console.print("\n[bold reverse red] FAILED [/bold reverse red] No tracks resolved.")