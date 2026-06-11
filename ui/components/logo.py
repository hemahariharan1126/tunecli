"""
LogoPanel Component — Glowing block-character banner for TuneCLI TUI.
Reads logo.txt from project root and renders it in cyberpunk cyan.
"""

import os
from textual.widgets import Static

# ── Load logo from file at import time ──────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_LOGO_FILE = os.path.join(_ROOT, "logo.txt")

try:
    with open(_LOGO_FILE, "r", encoding="utf-8") as _f:
        _RAW_LOGO = _f.read().rstrip("\n")
except FileNotFoundError:
    _RAW_LOGO = "M! TuneCLI"


def _build_logo_markup() -> str:
    """Wrap each logo line in bright-cyan bold markup for a glowing effect."""
    lines = _RAW_LOGO.splitlines()
    colored = "\n".join(
        f"[bold bright_cyan]{line}[/bold bright_cyan]" for line in lines
    )
    tagline = "  [dim]⚡ Terminal Music Player[/dim]"
    return colored + "\n" + tagline


_LOGO_MARKUP = _build_logo_markup()


class LogoPanel(Static):
    """Displays the TuneCLI logo banner at the top of the TUI."""

    def render(self) -> str:
        return _LOGO_MARKUP
