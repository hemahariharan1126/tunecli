from rich.table import Table
from rich.console import Console
from rich.text import Text

def help_command(args):
    """M!help — returns available commands as a Rich table."""
    table = Table(
        title=Text(" ⚡ SYSTEM.COMMANDS ", style="bold reverse magenta"),
        box=None,
        padding=(0, 1),
        header_style="bold magenta",
        title_justify="left",
        show_header=True
    )
    
    table.add_column("COMMAND", style="cyan")
    table.add_column("DESCRIPTION", style="dim white")
    
    commands = [
        ("M!play <song>",          "Search and play/queue a track"),
        ("M!pause / M!resume",     "Halt or continue playback"),
        ("M!skip / M!next",        "Jump to the next track"),
        ("M!prev",                 "Return to historical track"),
        ("M!stop",                 "Stop playback & clear queue"),
        ("M!ask <prompt>",         "Identify and play a song from a description/lyrics"),
        ("M!queue",                "Visualize current track sequence"),
        ("M!mood <type>",          "Bias search results by vibe"),
        ("M!recommend",            "Extract similar tracks via AI"),
        ("M!scenario <story>",     "Soundtrack your situation via LLM"),
        ("M!radio <on|off>",       "Toggle continuous radio stream"),
        ("M!find <song>",          "Search without playing"),
        ("M!reorder <from> <to>",  "Reorder the queue (e.g., M!reorder 3 1)"),
        ("M!volume <0-100>",       "Adjust audio gain"),
        ("M!theme <name>",         "Switch colour theme  [cyberpunk · black · red_velvet · ocean · forest · sunset · rose_gold · dracula]"),
        ("M!lang [code|reset]",    "View/override language lock  [ta · hi · te · ml · kn · en]  or reset for auto-detect"),
        ("M!eq [on|off|reset|info]","LLM-optimized per-song equalizer  [auto-applied on every track]"),
        ("M!loop [off|one|all]",   "Loop control — off, repeat one song, or loop entire queue"),
        ("M!source [yt|ytmusic]",  "Switch search backend — yt-dlp (default) or YouTube Music API"),
        ("M!help",                 "Display this interface"),
    ]
    
    for cmd, desc in commands:
        table.add_row(cmd, desc)
        
    return table