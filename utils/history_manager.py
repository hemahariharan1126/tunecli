import os
import json
from pathlib import Path

# Save history in the project root
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_FILE = os.path.join(_ROOT, ".history.json")
MAX_HISTORY = 50

def _load_history() -> list:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _save_history(history: list) -> None:
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def add_history_entry(item_type: str, title: str, artist: str = "", query: str = "") -> None:
    """
    Appends a new playback to the history. 
    item_type: "song" or "playlist"
    """
    history = _load_history()
    
    # Remove duplicate if exists (so we bump it to the top)
    history = [item for item in history if not (item["title"] == title and item.get("artist") == artist)]
    
    new_entry = {
        "type": item_type,
        "title": title,
        "artist": artist,
        "query": query,
    }
    
    # Insert at front
    history.insert(0, new_entry)
    
    # Cap at MAX
    history = history[:MAX_HISTORY]
    
    _save_history(history)

def get_history() -> list:
    """Returns the playback history list."""
    return _load_history()
