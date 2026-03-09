"""
Queue Manager — Manages the list of songs to be played, including history and shuffle/repeat modes.
"""

import random
from collections import deque
from core.song import Song
from typing import List, Optional

class QueueManager:
    def __init__(self):
        self.queue = deque()
        self.history = []
        self.current_song: Optional[Song] = None
        self.shuffle_mode = False
        self.repeat_mode = "none"  # "none", "one", "all"

    def add_song(self, song: Song, at_front: bool = False):
        """Add a song to the queue."""
        if at_front:
            self.queue.appendleft(song)
        else:
            self.queue.append(song)

    def next_song(self) -> Optional[Song]:
        """Fetch the next song based on repeat/shuffle modes."""
        # Handle repeat one
        if self.repeat_mode == "one" and self.current_song:
            return self.current_song

        # Handle moving current song to history
        if self.current_song:
            self.history.append(self.current_song)

        if not self.queue:
            # Handle repeat all
            if self.repeat_mode == "all" and self.history:
                self.queue.extend(self.history)
                self.history = []
            else:
                self.current_song = None
                return None

        # Handle shuffle
        if self.shuffle_mode:
            self.current_song = random.choice(list(self.queue))
            self.queue.remove(self.current_song)
        else:
            self.current_song = self.queue.popleft()

        return self.current_song

    def prev_song(self) -> Optional[Song]:
        """Go back to the previous song in history."""
        if not self.history:
            return None

        if self.current_song:
            self.queue.appendleft(self.current_song)

        self.current_song = self.history.pop()
        return self.current_song

    def skip_song(self) -> Optional[Song]:
        """Skip current song."""
        return self.next_song()

    def set_shuffle(self, enabled: bool):
        self.shuffle_mode = enabled

    def set_repeat(self, mode: str):
        """Set repeat mode: 'none', 'one', 'all'."""
        if mode in ["none", "one", "all"]:
            self.repeat_mode = mode

    def clear(self):
        """Empty the queue."""
        self.queue.clear()
        self.current_song = None

    def get_queue(self) -> List[Song]:
        return list(self.queue)

    def now_playing(self) -> Optional[Song]:
        return self.current_song

    def queue_length(self) -> int:
        return len(self.queue)