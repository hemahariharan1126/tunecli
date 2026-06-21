"""
M!source — Switch the active search backend at runtime.
Usage: M!source yt | M!source ytmusic
"""
import os
import re
from pathlib import Path


VALID_BACKENDS = {"yt", "ytmusic"}

BACKEND_LABELS = {
    "yt":      "[bold cyan]yt-dlp[/bold cyan] [dim](4-Stage Fallback · Max Recall)[/dim]",
    "ytmusic": "[bold bright_green]YouTube Music API[/bold bright_green] [dim](Official Catalog · Max Precision)[/dim]",
}


def _update_env_file(key: str, value: str) -> None:
    """Persist a key=value pair to the .env file."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    content = env_path.read_text(encoding="utf-8") if env_path.exists() else ""

    pattern = re.compile(rf"^{re.escape(key)}=.*$", re.MULTILINE)
    new_line = f"{key}={value}"

    if pattern.search(content):
        content = pattern.sub(new_line, content)
    else:
        content = content.rstrip("\n") + f"\n{new_line}\n"

    env_path.write_text(content, encoding="utf-8")


def source(args: list[str]) -> str:
    """Switch the active search backend."""
    if not args:
        from config import SEARCH_BACKEND
        current_label = BACKEND_LABELS.get(SEARCH_BACKEND, SEARCH_BACKEND)
        return (
            f"[bold]Active Search Backend:[/bold] {current_label}\n"
            f"  [dim]Switch with: [bold]M!source yt[/bold] or [bold]M!source ytmusic[/bold][/dim]"
        )

    backend = args[0].lower()
    if backend not in VALID_BACKENDS:
        return (
            f"[bold red]ERR:[/bold red] [dim]Unknown backend '[bold]{args[0]}[/bold]'. "
            f"Valid options: [bold]yt[/bold], [bold]ytmusic[/bold][/dim]"
        )

    # Persist to .env so it survives restarts
    _update_env_file("SEARCH_BACKEND", backend)

    # Hot-reload in the current process without restarting
    os.environ["SEARCH_BACKEND"] = backend

    # Force config module to re-read the variable
    import config
    config.SEARCH_BACKEND = backend

    label = BACKEND_LABELS[backend]
    return (
        f"[bold bright_cyan]SEARCH.SOURCE[/bold bright_cyan] "
        f"[dim]switched to[/dim] {label}"
    )
