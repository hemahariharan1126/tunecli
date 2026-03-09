"""
Progress Bar — Rich-based progress bar component for song playback.
"""

from rich.progress import Progress, BarColumn, TimeRemainingColumn, TextColumn


def make_progress() -> Progress:
    """Create a styled Rich Progress bar for song playback."""
    return Progress(
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=40, style="cyan", complete_style="bright_cyan"),
        TextColumn("[bright_white]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        transient=True,
    )
