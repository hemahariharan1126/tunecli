"""
Main entry point for TuneCLI — Terminal Music Player.
Featuring a beautiful reactive TUI.
"""

import os
import sys

# --- MPV & yt-dlp Loading Logic (Cross-Platform Setup) ---
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
    
    # Add Python Scripts folder and user site-scripts to PATH so MPV can find yt-dlp.exe
    search_script_dirs = [
        os.path.join(os.path.dirname(sys.executable), 'Scripts'),
        os.path.join(sys.prefix, 'Scripts'),
    ]
    try:
        import site
        if hasattr(site, 'getuserbase'):
            search_script_dirs.append(os.path.join(site.getuserbase(), 'Scripts'))
    except Exception:
        pass

    # Dynamically discover any Windows Store Python script locations
    local_app_data = os.environ.get('LOCALAPPDATA', '')
    if local_app_data:
        packages_dir = os.path.join(local_app_data, 'Packages')
        if os.path.isdir(packages_dir):
            try:
                for pkg in os.listdir(packages_dir):
                    if pkg.startswith('PythonSoftwareFoundation.Python.'):
                        py_sub = os.path.join(packages_dir, pkg, 'LocalCache', 'local-packages')
                        if os.path.isdir(py_sub):
                            for sub in os.listdir(py_sub):
                                scripts_candidate = os.path.join(py_sub, sub, 'Scripts')
                                if os.path.isdir(scripts_candidate):
                                    search_script_dirs.append(scripts_candidate)
            except Exception:
                pass
    
    for p in search_script_dirs:
        if os.path.isdir(p) and p not in os.environ['PATH']:
            os.environ['PATH'] = p + os.pathsep + os.environ['PATH']

elif sys.platform == 'darwin':
    # macOS Homebrew libmpv paths
    for p in ['/opt/homebrew/lib', '/usr/local/lib']:
        if os.path.isdir(p):
            current_dyld = os.environ.get('DYLD_LIBRARY_PATH', '')
            if p not in current_dyld:
                os.environ['DYLD_LIBRARY_PATH'] = f"{p}:{current_dyld}" if current_dyld else p
            if p not in os.environ['PATH']:
                os.environ['PATH'] = f"{p}:{os.environ['PATH']}"
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
        # Cleanup player and audio cache on exit
        controller = get_controller()
        if controller:
            controller.shutdown()  # Purge pre-downloaded audio cache
            if controller.mpv_player:
                controller.mpv_player.terminate()

if __name__ == "__main__":
    main()
