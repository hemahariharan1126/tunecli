from rich.table import Table
from rich.console import Console
from rich.text import Text

console = Console()

def help_command(args):
    """M!help — displays available commands."""
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
        ("M!play <song>", "Search and play/queue a track"),
        ("M!pause / M!resume", "Halt or continue playback"),
        ("M!skip / M!next", "Jump to the next track"),
        ("M!prev", "Return to historical track"),
        ("M!stop", "Cease all playback and clear queue"),
        ("M!queue", "Visualize current track sequence"),
        ("M!mood <type>", "Bias search results by vibe"),
        ("M!recommend", "Extract similar tracks via AI"),
        ("M!volume <0-100>", "Adjust audio gain"),
        ("M!help", "Display this interface")
    ]
    
    for cmd, desc in commands:
        table.add_row(cmd, desc)
        
    console.print("\n" + "─" * 60, style="dim bright_black")
    console.print(table)
    console.print("─" * 60, style="dim bright_black")