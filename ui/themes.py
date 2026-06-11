"""
Theme Registry — Manages TuneCLI's available themes.
Supports runtime switching and persistence across restarts via .env.
"""

import os
from dotenv import load_dotenv, set_key

load_dotenv()

_ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STYLES = os.path.join(_ROOT, "ui", "styles")
_ENV    = os.path.join(_ROOT, ".env")

# ── Theme registry ───────────────────────────────────────────────────────────
THEMES: dict[str, str] = {
    "cyberpunk":  os.path.join(_STYLES, "theme.tcss"),
    "black":      os.path.join(_STYLES, "black.tcss"),
    "red_velvet": os.path.join(_STYLES, "red_velvet.tcss"),
    "ocean":      os.path.join(_STYLES, "ocean.tcss"),
    "forest":     os.path.join(_STYLES, "forest.tcss"),
    "sunset":     os.path.join(_STYLES, "sunset.tcss"),
    "rose_gold":  os.path.join(_STYLES, "rose_gold.tcss"),
    "dracula":    os.path.join(_STYLES, "dracula.tcss"),
}

AVAILABLE_THEMES: list[str] = list(THEMES.keys())

# Default theme ID (falls back to cyberpunk if unset / invalid)
_DEFAULT = "cyberpunk"


def get_saved_theme() -> str:
    """Read the persisted theme name from .env (TUNECLI_THEME key)."""
    name = os.getenv("TUNECLI_THEME", _DEFAULT).strip().lower()
    return name if name in THEMES else _DEFAULT


def get_theme_path(name: str) -> str:
    """Return the absolute .tcss file path for the given theme name."""
    return THEMES.get(name, THEMES[_DEFAULT])


def get_theme_css(name: str) -> str:
    """Return the full CSS string for the given theme name."""
    path = get_theme_path(name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def save_theme(name: str) -> None:
    """Persist the chosen theme to .env so it survives restarts."""
    if name in THEMES:
        set_key(_ENV, "TUNECLI_THEME", name)
