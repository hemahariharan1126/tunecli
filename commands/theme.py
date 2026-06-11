"""
Theme Command — M!theme <name>
Switches the TUI colour theme at runtime and persists the choice.
"""

from ui.themes import AVAILABLE_THEMES, save_theme


def theme(args: list[str]) -> dict | str:
    """
    M!theme <name>
    Switch the active TUI theme. Available: cyberpunk, black.
    The selection is saved to .env and restored on next launch.
    """
    if not args:
        options = "  ".join(f"[bold cyan]{t}[/bold cyan]" for t in AVAILABLE_THEMES)
        return (
            f"[bold yellow]⚠  Usage:[/bold yellow] [dim]M!theme <name>[/dim]\n"
            f"  Available themes: {options}"
        )

    name = args[0].strip().lower()

    if name not in AVAILABLE_THEMES:
        options = ", ".join(AVAILABLE_THEMES)
        return (
            f"[bold red]✗[/bold red] Unknown theme [bold]{name}[/bold]. "
            f"Choose from: [cyan]{options}[/cyan]"
        )

    # Persist the selection to .env
    save_theme(name)

    # Return a structured dict — app.py handles theme switching on the main thread
    return {"type": "theme_switch", "theme": name}
