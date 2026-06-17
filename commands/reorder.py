"""Reorder command — safely shifts songs up or down in the queue."""

from player.playback_controller import get_controller

def reorder(args: list[str]) -> str:
    """M!reorder <from> <to> — shift songs within the queue."""
    if len(args) != 2:
        return "[bold red]✗  Usage:[/bold red] [dim]M!reorder <from_index> <to_index>[/dim]"

    try:
        from_idx = int(args[0])
        to_idx = int(args[1])
    except ValueError:
        return "[bold red]✗  Type Error:[/bold red] [dim]Indices must be integers (e.g., M!reorder 3 1)[/dim]"

    controller = get_controller()
    success, error_msg, song_title = controller.queue_manager.reorder_song(from_idx, to_idx)

    if not success:
        return f"[bold red]✗  Queue Error:[/bold red] [dim]{error_msg}[/dim]"

    return (
        f"  [bold reverse green] QUEUE.MOVED [/bold reverse green]  "
        f"Moved [bold]\"{song_title}\"[/bold] to position [bold cyan]{to_idx}[/bold cyan]."
    )
