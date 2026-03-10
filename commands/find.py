"""Find command — records audio, identifies via Shazam, and recommends similar."""
import sounddevice as sd
import soundfile as sf
from shazamio import Shazam
import asyncio
import tempfile
import os
import queue
from rich.console import Console

from player.playback_controller import get_controller
from recommender.recommender_engine import RecommenderEngine

console = Console()

def find(args):
    """
    M!find
    Records audio from the terminal, identifies the song, and provides recommendations.
    """
    console.print("\n[bold magenta]🎤 AUDIO.LISTENING[/bold magenta] [dim](Type 'q' and press Enter to stop)[/dim]")
    
    q = queue.Queue()
    recording = True
    
    def callback(indata, frames, time, status):
        """This is called for each audio block."""
        if recording:
            q.put(indata.copy())
            
    # Settings
    samplerate = 44100
    channels = 1
    
    # Start recording
    try:
        stream = sd.InputStream(samplerate=samplerate, channels=channels, callback=callback)
        with stream:
            while True:
                user_input = console.input("")
                if user_input.strip().lower() == 'q':
                    recording = False
                    break
    except Exception as e:
        console.print(f"[bold red]ERR.MIC: Could not access microphone: {e}[/bold red]")
        return
        
    console.print("\n[dim]🎙️ RECORDING.STOPPED. Processing audio...[/dim]")
    
    audio_data = []
    while not q.empty():
        audio_data.append(q.get())
        
    if not audio_data:
         console.print("[bold red]ERR.AUDIO: No audio data recorded.[/bold red]")
         return
         
    import numpy as np
    audio_data = np.concatenate(audio_data, axis=0)
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_filename = tmp.name
        
    sf.write(tmp_filename, audio_data, samplerate)
    
    # Identify song using Shazam
    console.print("[dim]🔍 IDENTIFYING.TRACK...[/dim]")
    
    async def identify():
        shazam = Shazam()
        out = await shazam.recognize(tmp_filename)
        return out
        
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    try:
        result = loop.run_until_complete(identify())
    except Exception as e:
        console.print(f"[bold red]ERR.SHAZAM: Identification failed: {e}[/bold red]")
        os.remove(tmp_filename)
        return
        
    os.remove(tmp_filename)
    
    if 'track' not in result and 'matches' not in result and not result.get('track'):
         console.print("[bold red]ERR.MATCH: No song identified from the audio.[/bold red]")
         return
         
    track = result.get('track', {})
    if not track:
         console.print("[bold red]ERR.MATCH: No track details found.[/bold red]")
         return
         
    title = track.get('title', 'Unknown Title')
    artist = track.get('subtitle', 'Unknown Artist')
    
    console.print(f"\n[bold green]🎵 IDENTIFIED:[/bold green] [cyan]{title}[/cyan] by [yellow]{artist}[/yellow]")
    
    # Get recommendations
    console.print(f"[dim]⚡ FINDING.RECOMMENDATIONS...[/dim]")
    
    controller = get_controller()
    
    try:
        recommender = RecommenderEngine()
        recommendations = recommender.get_spotify_recommendations(
            f"{title} {artist}",
            target_lang=controller.seed_language
        )
    except Exception as e:
        console.print(f"[yellow]WARN: Recommender unavailable (missing API keys or network error).[/yellow]")
        recommendations = None
    
    options = []
    
    console.print("\n[bold cyan]WHAT WOULD YOU LIKE TO PLAY?[/bold cyan]")
    
    # Option 1 is always the identified song
    options.append({"title": title, "artist": artist, "type": "Identified Song"})
    console.print(f"  [bold green]1.[/bold green] [yellow](Identified)[/yellow] {title} [dim]by {artist}[/dim]")
    
    if recommendations:
        top_recs = recommendations[:5]
        for i, rec in enumerate(top_recs, 2):
            options.append({"title": rec['title'], "artist": rec['artist'], "type": "Recommendation"})
            console.print(f"  [bold cyan]{i}.[/bold cyan] [cyan](Similar)[/cyan] {rec['title']} [dim]by {rec['artist']}[/dim]")
            
    choice = console.input(f"\n[dim]Select a track to play (1-{len(options)}) or 'c' to cancel: [/dim]")
    
    if choice.isdigit() and 1 <= int(choice) <= len(options):
        selected = options[int(choice) - 1]
        query = f"{selected['title']} {selected['artist']}"
        console.print(f"[dim]Queueing {selected['type']}...[/dim]")
        controller.play_song(query)
    else:
        console.print("[dim]Operation cancelled.[/dim]")
