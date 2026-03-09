"""
Theme — Color palette and style constants for TuneCLI TUI.
"""

from rich.theme import Theme

TUNECLI_THEME = Theme({
    "header":       "bold bright_cyan",
    "now_playing":  "bold bright_white",
    "artist":       "dim bright_white",
    "mood":         "bold magenta",
    "energy":       "bold yellow",
    "queue_title":  "bold bright_blue",
    "queue_item":   "dim white",
    "network":      "bold green",
    "quality":      "cyan",
    "command":      "bold bright_yellow",
    "error":        "bold red",
    "success":      "bold green",
    "border":       "bright_black",
})

APP_NAME = "M! TuneCLI"
BORDER_STYLE = "cyan"
