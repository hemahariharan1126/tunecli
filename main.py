"""
Main entry point for TuneCLI — Terminal Music Player.
Featuring a beautiful Rich-powered live UI.
"""

import os
import sys

# --- MPV & yt-dlp Loading Logic (Windows Portable Setup) ---
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_PATH = os.path.join(BASE_DIR, 'lib')

if sys.platform == 'win32':
    # Ensure lib path is absolute and added to PATH and DLL search
    if os.path.isdir(LIB_PATH):
        abs_lib_path = os.path.abspath(LIB_PATH)
        if abs_lib_path not in os.environ['PATH']:
            os.environ['PATH'] = abs_lib_path + os.pathsep + os.environ['PATH']
        if hasattr(os, 'add_dll_directory'):
            try:
                os.add_dll_directory(abs_lib_path)
            except Exception:
                pass # Already added or OS restriction
    
    # Add Python Scripts folder to PATH so MPV can find yt-dlp.exe
    scripts_path = os.path.join(os.path.dirname(sys.executable), 'Scripts')
    win_store_scripts = os.path.expandvars(r"%LOCALAPPDATA%\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\Scripts")
    
    for p in [scripts_path, win_store_scripts]:
        if os.path.isdir(p) and p not in os.environ['PATH']:
            os.environ['PATH'] = p + os.pathsep + os.environ['PATH']
# ------------------------------------------------------

import time
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import ProgressBar
from rich.layout import Layout
from rich.text import Text
from rich.table import Table

from parser.command_parser import parse_command
from utils.command_router import execute_command
import logging
logging.basicConfig(level=logging.CRITICAL)

from player.playback_controller import get_controller

console = Console()

def generate_header() -> Text:
    time_str = time.strftime("%H:%M:%S")
    return Text.assemble(
        (" ⚡ TUNE.CLI ", "bold reverse cyan"),
        (f" [{time_str}] ", "dim white"),
        ("─" * 40, "dim bright_black")
    )

def generate_np_minimal() -> Text:
    controller = get_controller()
    current = controller.queue_manager.now_playing()
    
    if not current:
        return Text("\n  [NO.TRACK_LOADING]\n  Ready for command...\n", style="dim italic white")
    
    # Get status
    duration = controller.mpv_player.get_duration() or current.duration or 1
    position = controller.mpv_player.get_position()
    volume = controller.mpv_player.get_volume()
    status = "RUN" if controller.mpv_player.is_playing() else "HLD"
    
    mins_c, secs_c = divmod(int(position), 60)
    mins_t, secs_t = divmod(int(duration), 60)
    
    # Minimalist bar
    percent = (position / duration)
    bar_width = 40
    filled = int(bar_width * percent)
    bar = Text.assemble(
        ("█" * filled, "cyan"),
        ("░" * (bar_width - filled), "bright_black")
    )
    
    res = Text.assemble(
        ("\n 🎧 ", "magenta"), (f"{current.title}", "bold white"), "\n",
        (" 👤 ", "cyan"), (f"{current.artist}", "dim"), "\n\n",
        (f" [{status}] ", "bold reverse magenta" if status == "RUN" else "bold reverse yellow"),
        (" "), bar, (" "), (f"{mins_c}:{secs_c:02d}/{mins_t}:{secs_t:02d}", "dim white"), "\n",
        (f" [VOL_{volume}%] ", "dim cyan")
    )
    return res

def main():
    # Initial startup message
    console.print("\n[bold cyan]⚡ TUNE.CLI [/bold cyan][dim]INITIALIZING.SYSTEM...[/dim]")
    
    # Fix: Ensure controller and player are ready before UI loop
    try:
        controller = get_controller()
        console.print("[dim]  > CORE.READY[/dim]")
    except Exception as e:
        console.print(f"[bold red]FATAL.ERROR: {e}[/bold red]")
        return

    time.sleep(0.5)
    console.clear()
    
    while True:
        try:
            # Persistent status line
            console.print(generate_header())
            console.print(generate_np_minimal())
            
            user_input = console.input("[bold magenta]λ [/bold magenta]")
            
            if not user_input.strip():
                console.clear()
                continue
                
            parsed = parse_command(user_input)
            if parsed:
                # Execute command
                execute_command(parsed)
                # Brief pause to let user see output if it's not a background action
                if parsed.name.lower() not in ['play', 'queue']:
                   time.sleep(0.5)
            else:
                console.print("[red]ERR: CMD_NOT_FOUND[/red]")
                time.sleep(1)
            
            console.clear()
                
        except KeyboardInterrupt:
            console.print("\n[bold reverse red] TERMINATED.BY.USER [/bold reverse red] [dim]Goodbye buddy! 🚀[/dim]")
            if controller.mpv_player:
                controller.mpv_player.terminate()
            break
        except Exception as e:
            console.print(f"[bold red]SYS.EXCEPTION: {e}[/bold red]")
            time.sleep(2)
            console.clear()

if __name__ == "__main__":
    main()