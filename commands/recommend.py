"""Recommend command — adds related songs to the queue."""
from player.playback_controller import get_controller
from recommender.recommender_engine import RecommenderEngine
from search_engine.yt_search import search_song
import logging

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
        return "[red]ERR: NO_TRACK_FOR_ANALYSIS[/red]"

    output = [f"\n[bold magenta]⚡ ANALYZING.VIBE:[/bold magenta] [cyan]{current_song.title}[/cyan]"]

    # 1. Get high-quality recommendations from Spotify (with language guard)
    recommendations = recommender.get_spotify_recommendations(
        f"{current_song.title} {current_song.artist}",
        target_lang=controller.seed_language,
        seed_video_id=getattr(current_song, 'video_id', None)
    )

    if not recommendations:
        return "[yellow]WARN: NO_MATCHES_FOUND[/yellow]"

    # 2. Resolve those songs on YouTube and add to queue
    output.append(f"[dim]Found {len(recommendations)} matches. Resolving streams...[/dim]")

    added_count = 0
    for rec in recommendations:
        query = f"{rec['title']} {rec['artist']}"
        song = search_song(query)
        if song:
            controller.queue_manager.add_song(song)
            output.append(f"  [bold cyan]+[/bold cyan] {song.title} [dim]by {song.artist}[/dim]")
            added_count += 1
        else:
            output.append(f"  [red]![/red] SKIPPED: {query} [dim](NOT_FOUND)[/dim]")

    if added_count > 0:
        output.append(f"\n[bold reverse green] SUCCESS [/bold reverse green] Added {added_count} tracks to queue.")
    else:
        output.append("\n[bold reverse red] FAILED [/bold reverse red] No tracks resolved.")

    return "\n".join(output)