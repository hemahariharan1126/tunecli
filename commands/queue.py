"""Queue command — displays the current song queue using Rich."""
from player.playback_controller import get_controller
from rich.table import Table
from rich.console import Console
from rich.text import Text

console = Console()

def show_queue(args):
    """M!queue — displays the current song queue."""
    controller = get_controller()
    queue = controller.get_queue()
    current = controller.queue_manager.now_playing()

    if not queue and not current:
        console.print("[dim]Queue is empty.[/dim]")
        return

    # Cyber-minimalist table design
    table = Table(
        title=Text(" ⚡ QUEUE.DATA ", style="bold reverse magenta"),
        box=None,
        padding=(0, 1),
        header_style="bold magenta",
        title_justify="left",
    )
    
    table.add_column("IDX", style="dim", width=4)
    table.add_column("TITLE", style="white")
    table.add_column("ARTIST", style="cyan")
    table.add_column("DUR", justify="right", style="dim white")

    if current:
        mins, secs = divmod(current.duration or 0, 60)
        table.add_row(
            "[bold cyan]▶[/bold cyan]", 
            f"[bold]{current.title}[/bold]", 
            current.artist, 
            f"{mins}:{secs:02d}", 
            style="bold cyan"
        )

    for i, song in enumerate(queue, 1):
        mins, secs = divmod(song.duration or 0, 60)
        table.add_row(str(i), song.title, song.artist, f"{mins}:{secs:02d}")

    # Separator line matching header
    console.print("\n" + "─" * 60, style="dim bright_black")
    console.print(table)
    console.print("─" * 60, style="dim bright_black")
