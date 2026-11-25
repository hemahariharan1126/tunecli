"""
Theme Command — M!theme <name>
Switches the TUI colour theme at runtime and persists the choice.
"""

from ui import themes
from ui.themes import validate_theme_css


def theme(args: list[str]) -> dict | str:
    """
    M!theme <name>
    Switch the active TUI theme. Available: cyberpunk, black, etc.
    The selection is persisted to .env only after successful CSS application.
    """
    available = list(themes.THEMES.keys())
    if not args:
        options = "  ".join(f"[bold cyan]{t}[/bold cyan]" for t in available)
        return (
            f"[bold yellow]⚠  Usage:[/bold yellow] [dim]M!theme <name>[/dim]\n"
            f"  Available themes: {options}"
        )

    name = args[0].strip().lower()

    if name not in themes.THEMES:
        options = ", ".join(available)
        return (
            f"[bold red]✗[/bold red] Unknown theme [bold]{name}[/bold]. "
            f"Choose from: [cyan]{options}[/cyan]"
        )

    try:
        validate_theme_css(name)
    except Exception as e:
        return f"[bold red]✗  THEME ERR:[/bold red] [dim]{e}[/dim]"

    # Return a structured dict — app.py applies and persists on the main thread
    return {"type": "theme_switch", "theme": name}
