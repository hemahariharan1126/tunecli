"""
Ask command — uses Ollama LLM to deduce a song from a prompt/lyrics and play it.
"""

from api.llm_client import get_llm_client
from search_engine.yt_search import search_song
from player.playback_controller import get_controller
import logging

def ask(args: list[str]) -> str:
    """M!ask <prompt> — deduces and plays a song using the Ollama LLM."""
    if not args:
        return "[bold red]✗  Usage:[/bold red] [dim]M!ask <description or lyrics>[/dim]\n[dim]Example: M!ask the song where they sing mama just killed a man[/dim]"

    prompt = " ".join(args)
    client = get_llm_client()
    
    # Deducing the song via Ollama
    result = client.identify_song(prompt)
    if "error" in result:
        return f"[bold red]✗  Ollama Error:[/bold red] [dim]{result['error']}[/dim]"
        
    title = result.get('title') or result.get('song') or result.get('name') or ''
    artist = result.get('artist', '')
    reasoning = result.get('reasoning', 'Deduced from your prompt.')
    
    if not title or not artist:
        return f"[bold red]✗  LLM Error:[/bold red] [dim]Failed to parse song title and artist. Raw Output: {result}[/dim]"
        
    # Search and Play
    search_query = f"{title} {artist}"
    song = search_song(search_query)
    
    if not song:
        return f"[bold red]✗  Not Found:[/bold red] [dim]Ollama suggested '{search_query}', but YouTube couldn't find it.[/dim]"
        
    controller = get_controller()
    controller.queue_manager.add_song(song)
    
    # Auto-play if nothing is playing
    if not controller.queue_manager.now_playing():
        controller._play_next()
        
    return (
        f"  [bold reverse cyan] OLLAMA.DEDUCED [/bold reverse cyan]  \n"
        f"[dim]Reasoning:[/dim] {reasoning}\n"
        f"[bold green]▶ Queued:[/bold green] [bold]{song.title}[/bold] - {song.artist}"
    )
