"""
Playback State Model — Enumerates all valid states of the audio playback engine.
"""

from enum import Enum, auto


class PlaybackState(Enum):
    IDLE = auto()
    LOADING = auto()
    PLAYING = auto()
    PAUSED = auto()
    BUFFERING = auto()
    STOPPED = auto()
    ENDED = auto()
    ERROR = auto()

    def is_active(self) -> bool:
        """Returns True if the engine is in a state with an active song loaded."""
        return self in (PlaybackState.LOADING, PlaybackState.PLAYING, PlaybackState.PAUSED, PlaybackState.BUFFERING)

    def __str__(self) -> str:
        return self.name
