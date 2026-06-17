from player.playback_controller import get_controller

def remove(args: list[str]) -> str:
    """
    Remove a specific song from the upcoming queue using its index.
    Example: M!remove 2
    """
    if not args:
        return "[bold red]✗ ERR:[/bold red] [dim]You must provide the song index. Example: M!remove 2[/dim]"

    try:
        idx = int(args[0])
    except ValueError:
        return f"[bold red]✗ ERR:[/bold red] [dim]'{args[0]}' is not a valid number.[/dim]"

    controller = get_controller()
    success, error_msg, title = controller.queue_manager.remove_song(idx)
    
    if not success:
        return f"[bold red]✗ ERR:[/bold red] [dim]{error_msg}[/dim]"

    return f"[bold bright_red]✕ Removed:[/bold bright_red] [cyan]{title}[/cyan]"
