"""
Visualizer — ASCII/Unicode audio visualizer stub for TuneCLI.
Generates a simple animated bar that can be embedded in the TUI.
"""

import random


def get_visualizer_frame(width: int = 20) -> str:
    """
    Return a single-frame ASCII bar visualizer string.
    (Placeholder — can be replaced with real FFT data from mpv IPC.)
    """
    bars = [random.choice("▁▂▃▄▅▆▇█") for _ in range(width)]
    return "[cyan]" + "".join(bars) + "[/cyan]"
