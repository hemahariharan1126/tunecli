"""
Visualizer — Multi-color gradient ASCII audio visualizer for TuneCLI.
Generates animated bars with a cyan → purple → pink gradient when playing,
and a flat idle line when paused or stopped.
"""

import random
import math

# Gradient color bands: (start_ratio, end_ratio, color)
_BANDS = [
    (0.0,  0.35, "cyan"),
    (0.35, 0.65, "magenta"),
    (0.65, 1.0,  "bright_magenta"),
]

_BAR_CHARS = "▁▂▃▄▅▆▇█"
_IDLE_CHAR = "▁"
_PEAK_CHAR = "█"


def _color_for_position(ratio: float) -> str:
    """Return the Rich color tag for a horizontal position ratio (0.0–1.0)."""
    for start, end, color in _BANDS:
        if start <= ratio < end:
            return color
    return "bright_magenta"


def get_visualizer_frame(width: int = 36, is_playing: bool = True) -> str:
    """
    Return a single-frame visualizer string.

    Args:
        width:      Number of bars to render.
        is_playing: If False, renders a flat idle line instead of animated bars.
    """
    if not is_playing:
        # Flat idle state with muted styling
        return "[bright_black]" + (_IDLE_CHAR * width) + "[/bright_black]"

    # Generate heights with a bell-curve bias (taller in the middle)
    result_parts = []
    for i in range(width):
        # Bell-curve weight: center bars are taller on average
        center_bias = math.exp(-0.5 * ((i / width - 0.5) / 0.25) ** 2)
        weighted_max = max(1, int(len(_BAR_CHARS) * (0.3 + 0.7 * center_bias)))
        bar_char = random.choice(_BAR_CHARS[:weighted_max])
        color = _color_for_position(i / width)
        result_parts.append(f"[{color}]{bar_char}[/{color}]")

    return "".join(result_parts)
