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

    def reorder_song(self, from_idx: int, to_idx: int) -> tuple[bool, str, str]:
        """
        Move a song within the queue using 1-based indexing.
        Returns: (success: bool, error_message: str, song_title: str)
        """
        q_len = len(self.queue)
        if q_len == 0:
            return False, "Queue is empty.", ""
            
        if not (1 <= from_idx <= q_len):
            return False, f"Invalid 'from' index: {from_idx}. Queue length is {q_len}.", ""
            
        if not (1 <= to_idx <= q_len):
            return False, f"Invalid 'to' index: {to_idx}. Queue length is {q_len}.", ""
            
        if from_idx == to_idx:
            song = self.queue[from_idx - 1]
            return True, "", song.title
            
        # Convert to list for safe mutation
        queue_list = list(self.queue)
        song = queue_list.pop(from_idx - 1)
        queue_list.insert(to_idx - 1, song)
        
        # Re-assign back to deque
        self.queue = deque(queue_list)
        return True, "", song.title

    def remove_song(self, idx: int) -> tuple[bool, str, str]:
        """
        Remove a song from the queue using 1-based indexing.
        Returns: (success: bool, error_message: str, song_title: str)
        """
        q_len = len(self.queue)
        if q_len == 0:
            return False, "Queue is empty.", ""
            
        if not (1 <= idx <= q_len):
            return False, f"Invalid index: {idx}. Queue length is {q_len}.", ""
            
        # Convert to list for safe mutation
        queue_list = list(self.queue)
        song = queue_list.pop(idx - 1)
        
        # Re-assign back to deque
        self.queue = deque(queue_list)
        return True, "", song.title

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