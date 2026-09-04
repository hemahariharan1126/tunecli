"""Hist command — view and replay playback history."""
from utils.history_manager import get_history

def show_history(args):
    history = get_history()
    
    if not history:
        return "[yellow]  INFO: No playback history found.[/yellow]"
        
    options = []
    for item in history:
        cmd_type = "play-playlist" if item.get("type") == "playlist" else "play"
        # We store the "query" to make replay exact
        options.append({
            "title": item.get("title", "Unknown"),
            "artist": item.get("artist", ""),
            "type": item.get("type", "song").upper(),
            "command": cmd_type,
            "query": item.get("query", "")
        })
        
    return {
        "type": "selection",
        "title": "Playback History",
        "options": options
    }
