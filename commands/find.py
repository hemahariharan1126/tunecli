"""
Find Command — Records audio for 5 seconds and identifies the song via Shazam.
Integrated with the TUI via background workers and selection modals.
"""

import sounddevice as sd
import soundfile as sf
from shazamio import Shazam
import asyncio
import tempfile
import os
import queue
import time
import logging
import numpy as np

from player.playback_controller import get_controller
from recommender.recommender_engine import RecommenderEngine

def find(args):
    """
    M!find (Non-blocking Logic Provider)
    Records audio and identifies the track.
    Returns: 
        - dict: if identification succeeds (containing options for the UI)
        - str: if an error occurs or no match is found
    """
    q = queue.Queue()
    samplerate = 44100
    channels = 1
    duration = 5 # Fixed recording window
    
    def callback(indata, frames, time, status):
        q.put(indata.copy())
            
    # 1. Record Audio
    try:
        # Note: This runs within a @work(thread=True) worker from ui/app.py
        with sd.InputStream(samplerate=samplerate, channels=channels, callback=callback):
            time.sleep(duration)
    except Exception as e:
        return f"[red]ERR.MIC: Could not access microphone: {e}[/red]"
        
    audio_data = []
    while not q.empty():
        audio_data.append(q.get())
        
    if not audio_data:
         return "[red]ERR.AUDIO: No audio data recorded.[/red]"
         
    audio_data = np.concatenate(audio_data, axis=0)
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_filename = tmp.name
    sf.write(tmp_filename, audio_data, samplerate)
    
    # 2. Identify track (Async Shazam)
    async def identify():
        shazam = Shazam()
        return await shazam.recognize(tmp_filename)
        
    try:
        result = asyncio.run(identify())
    except Exception as e:
        return f"[red]ERR.SHAZAM: Identification failed: {e}[/red]"
    finally:
        if os.path.exists(tmp_filename):
            try:
                os.remove(tmp_filename)
            except Exception:
                pass
    
    if not result or 'track' not in result:
         return "[yellow]WARN: NO_MATCH_FOUND. Try again or check mic volume.[/yellow]"
         
    track = result['track']
    title = track.get('title', 'Unknown Title')
    artist = track.get('subtitle', 'Unknown Artist')
    
    # 3. Fetch Recommendations
    controller = get_controller()
    options = [{"title": title, "artist": artist, "type": "Identified"}]
    
    try:
        recommender = RecommenderEngine()
        recs = recommender.get_spotify_recommendations(
            f"{title} {artist}",
            target_lang=controller.seed_language
        )
        if recs:
            for r in recs[:4]:
                options.append({"title": r['title'], "artist": r['artist'], "type": "Similar"})
    except Exception:
        logging.warning("Find command: Recommender unavailable for extra options.")

    # Return the selection data structure
    return {
        "type": "selection",
        "title": f"IDENTIFIED: {title}",
        "options": options
    }
