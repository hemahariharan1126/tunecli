"""
Song — Core data model representing a single track in TuneCLI.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Song:
    """
    Represents a single playable track.

    Attributes:
        title       : Human-readable track title
        artist      : Primary artist name
        duration    : Duration in seconds (0 if unknown)
        video_id    : YouTube video ID used for streaming
        stream_url  : Pre-resolved direct stream URL (optional)
        thumbnail   : Thumbnail URL for display (optional)
        album       : Album name (optional)
        genre       : Genre string (optional)
        mood        : Mood tag if set by recommender (optional)
    """
    title: str
    artist: str = "Unknown"
    duration: int = 0
    video_id: str = ""
    stream_url: str = ""
    thumbnail: str = ""
    album: str = ""
    genre: str = ""
    mood: str = ""

    def __str__(self) -> str:
        mins, secs = divmod(self.duration, 60)
        dur = f"{mins}:{secs:02d}" if self.duration else "?:??"
        return f"{self.title} — {self.artist} [{dur}]"

    def __repr__(self) -> str:
        return (
            f"Song(title={self.title!r}, artist={self.artist!r}, "
            f"duration={self.duration}, video_id={self.video_id!r})"
        )

    def to_dict(self) -> dict:
        """Serialise to a plain dict (used by UI panels)."""
        return {
            "title":      self.title,
            "artist":     self.artist,
            "duration":   self.duration,
            "video_id":   self.video_id,
            "stream_url": self.stream_url,
            "thumbnail":  self.thumbnail,
            "album":      self.album,
            "genre":      self.genre,
            "mood":       self.mood,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Song":
        """Deserialise from a dict."""
        return cls(
            title=data.get("title", "Unknown"),
            artist=data.get("artist", "Unknown"),
            duration=data.get("duration", 0),
            video_id=data.get("video_id", ""),
            stream_url=data.get("stream_url", ""),
            thumbnail=data.get("thumbnail", ""),
            album=data.get("album", ""),
            genre=data.get("genre", ""),
            mood=data.get("mood", ""),
        )
