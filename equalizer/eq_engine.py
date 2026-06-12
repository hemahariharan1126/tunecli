"""
EQ Engine — Orchestrates LLM inference, disk caching, and MPV application
for per-song equalizer optimization.

Cache lives at: ~/.tunecli_eq_cache.json
Cache key:      sha256(f"{title}|{artist}")[:16]  (16-char hex prefix)
"""

import json
import logging
from hashlib import sha256
from pathlib import Path

from core.song import Song
from api.llm_eq import get_llm_eq_client, FALLBACK_PRESETS

# ── Constants ─────────────────────────────────────────────────────────────────
BANDS      = [32, 64, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
FLAT_EQ    = [0] * 10
CACHE_PATH = Path.home() / ".tunecli_eq_cache.json"

# Band labels for display
BAND_LABELS = ["32Hz", "64Hz", "125Hz", "250Hz", "500Hz",
               "1kHz", "2kHz", "4kHz", "8kHz", "16kHz"]


class EQEngine:
    """
    Manages the full lifecycle of per-song EQ optimization:
      1. Check disk cache (zero API cost)
      2. If not cached → call LLMEQClient (token-optimized Gemini request)
      3. Save result to cache
      4. Apply bands to MPVPlayer via set_eq()

    Thread-safe: designed to run from a daemon background thread.
    """

    def __init__(self):
        self._cache: dict[str, list[int]] = self._load_cache_file()
        self._current_bands: list[int] = list(FLAT_EQ)

    # ── Public API ────────────────────────────────────────────────────────────

    def apply_for_song(self, song: Song, mpv_player) -> None:
        """
        Main entry point — called from a background thread after _play_next().
        Resolves EQ (cache or LLM), saves to cache, applies to MPV.
        """
        key = self._cache_key(song)

        # 1. Cache hit — instant, no API call
        if key in self._cache:
            bands = self._cache[key]
            logging.info(f"EQEngine: Cache hit for '{song.title}' → {bands}")
        else:
            # 2. Cache miss — ask the LLM (token-optimized)
            logging.info(f"EQEngine: Cache miss for '{song.title}' — calling LLM.")
            client = get_llm_eq_client()
            bands = client.get_eq(
                title  = song.title,
                artist = song.artist,
                lang   = "",         # caller (playback_controller) will inject seed_language
                mood   = song.mood or "",
            )
            # 3. Persist to disk cache
            self._cache[key] = bands
            self._save_cache_file()

        # 4. Apply to MPV
        self._current_bands = bands
        if mpv_player:
            mpv_player.set_eq(bands)

    def apply_for_song_with_lang(self, song: Song, mpv_player, lang: str = "") -> None:
        """
        Variant used by the playback controller — passes the detected language
        so the LLM can use it in the EQ fingerprint.
        """
        key = self._cache_key(song)

        if key in self._cache:
            bands = self._cache[key]
            logging.info(f"EQEngine: Cache hit '{song.title}' → {bands}")
        else:
            logging.info(f"EQEngine: LLM EQ request for '{song.title}' [{lang}]")
            client = get_llm_eq_client()
            bands = client.get_eq(
                title  = song.title,
                artist = song.artist,
                lang   = lang or "en",
                mood   = song.mood or "",
            )
            self._cache[key] = bands
            self._save_cache_file()

        self._current_bands = bands
        if mpv_player:
            mpv_player.set_eq(bands)

    def reset(self, mpv_player) -> None:
        """Apply a completely flat EQ (all bands = 0 dB)."""
        self._current_bands = list(FLAT_EQ)
        if mpv_player:
            mpv_player.reset_eq()
        logging.info("EQEngine: EQ reset to flat.")

    def get_current_bands(self) -> list[int]:
        """Return the currently-active EQ band gains."""
        return list(self._current_bands)

    def cache_size(self) -> int:
        """Return the number of cached EQ presets."""
        return len(self._cache)

    def get_cached_eq(self, song: Song) -> list[int] | None:
        """Return cached EQ for a song, or None if not yet cached."""
        return self._cache.get(self._cache_key(song))

    # ── Cache helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _cache_key(song: Song) -> str:
        """16-char hex cache key derived from title + artist."""
        raw = f"{song.title.strip().lower()}|{song.artist.strip().lower()}"
        return sha256(raw.encode()).hexdigest()[:16]

    @staticmethod
    def _load_cache_file() -> dict[str, list[int]]:
        try:
            if CACHE_PATH.exists():
                data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    logging.info(f"EQEngine: Loaded {len(data)} cached EQ presets.")
                    return data
        except Exception as e:
            logging.warning(f"EQEngine: Cache load failed ({e}). Starting fresh.")
        return {}

    def _save_cache_file(self) -> None:
        try:
            CACHE_PATH.write_text(
                json.dumps(self._cache, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logging.warning(f"EQEngine: Cache save failed: {e}")

    # ── Display helpers ───────────────────────────────────────────────────────

    @staticmethod
    def format_bar_chart(bands: list[int]) -> str:
        """
        Render a 10-band EQ as a compact ASCII bar chart for the RichLog.
        Positive gains → filled bars (▓), negative → empty indication.
        """
        lines = []
        for label, gain in zip(BAND_LABELS, bands):
            if gain >= 0:
                filled = min(gain, 12)
                bar = "[cyan]" + "▓" * filled + "[/cyan]" + "[bright_black]" + "░" * (12 - filled) + "[/bright_black]"
                sign = f"[bold cyan]+{gain:>2}dB[/bold cyan]"
            else:
                abs_gain = abs(gain)
                bar = "[bright_black]" + "░" * (12 - abs_gain) + "[/bright_black]" + "[dim red]" + "▓" * abs_gain + "[/dim red]"
                sign = f"[dim red]{gain:>3}dB[/dim red]"
            lines.append(f"  [dim]{label:>5}[/dim]  {bar}  {sign}")
        return "\n".join(lines)
