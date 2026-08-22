"""Update command — Pulls the latest updates from the Git repository."""
import subprocess
import os

def update_command(args):
    """Run git pull to fetch and merge updates."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # Run git pull
        result = subprocess.run(
            ["git", "pull", "origin", "master"],
            cwd=base_dir,
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            if "Already up to date." in result.stdout:
                return "[bold bright_green]✔ ALREADY UP TO DATE[/bold bright_green] No new updates found."
            return (
                f"[bold bright_green]✔ UPDATES INSTALLED SUCCESSFULLY![/bold bright_green]\n"
                f"[dim]{result.stdout.strip()}[/dim]\n\n"
                f"[bold white]Please type [magenta]M!exit[/magenta] and restart TuneCLI to apply changes.[/bold white]"
            )
        else:
            return (
                f"[bold yellow]⚠ UPDATE SKIPPED[/bold yellow] Git encountered an issue (maybe local changes?).\n"
                f"[dim]{result.stderr.strip()}[/dim]\n"
                f"[white]App is running safely. Please pull manually via terminal.[/white]"
            )
    except Exception as e:
        return f"[bold red]✗ UPDATE FAILED[/bold red] Git is unavailable or network error: {e}"
