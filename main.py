"""
Main entry point for TuneCLI — Terminal Music Player.
Featuring a beautiful reactive TUI.
"""

import os
import sys

# --- MPV & yt-dlp Loading Logic (Windows Portable Setup) ---
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

import logging
from ui.app import TuneCLIApp

# Suppress all logging except critical errors to keep TUI clean
logging.basicConfig(level=logging.CRITICAL)

def main():
    """Launch the reactive TuneCLI Terminal Application."""
    # Import AFTER PATH is set so libmpv-2.dll is discoverable
    from player.playback_controller import get_controller

    app = TuneCLIApp()
    try:
        app.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"FATAL.ERROR: {e}")
    finally:
        # Cleanup player on exit
        controller = get_controller()
        if controller and controller.mpv_player:
            controller.mpv_player.terminate()

if __name__ == "__main__":
    main()
