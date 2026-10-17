"""
Media Key Bridge — Global listener for hardware media keys and Bluetooth headset buttons.

Uses pynput (pre-built universal wheel, zero MSVC compilation) to intercept
OS-level media key events and route them into TuneCLI's PlaybackController.

Handles:
  - Keyboard media keys (Play/Pause, Next, Prev, Stop, Vol Up/Down)
  - Bluetooth headset media buttons (they appear as the same virtual key codes)
  - Volume Up/Down hardware keys routed through TuneCLI's volume system

pynput works on Windows, macOS, and Linux without modification.
"""

import logging
import platform
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player.playback_controller import PlaybackController


class MediaKeyBridge:
    """
    Daemon thread that listens for global media key events using pynput
    and dispatches them to the PlaybackController.
    """

    def __init__(self, controller: "PlaybackController"):
        self._controller = controller
        self._listener = None
        self._ready = False

        try:
            from pynput import keyboard
            self._Key = keyboard.Key
            self._listener = keyboard.Listener(
                on_press=self._on_key_press,
                suppress=False,   # Never suppress — only listen
            )
            self._listener.daemon = True
            self._listener.start()
            self._ready = True
            logging.info("MediaKeyBridge: Global media key listener active.")
        except ImportError:
            logging.warning(
                "MediaKeyBridge: pynput not installed — run: pip install pynput"
            )
        except Exception as e:
            logging.warning(f"MediaKeyBridge: Failed to start listener: {e}")

    def _on_key_press(self, key):
        """
        Callback fired when any key is pressed globally.
        Only acts on media key codes — all other keys are ignored.
        """
        try:
            Key = self._Key
            ctrl = self._controller

            if key == Key.media_play_pause:
                # Toggle: pause if playing, resume if paused
                if ctrl.mpv_player and ctrl.mpv_player.is_playing():
                    ctrl.pause()
                else:
                    ctrl.resume()

            elif key == Key.media_next:
                ctrl.skip()

            elif key == Key.media_previous:
                ctrl.prev()

            elif key == Key.media_volume_up:
                if ctrl.mpv_player:
                    vol = ctrl.mpv_player.get_volume()
                    ctrl.set_volume(min(vol + 5, 100))

            elif key == Key.media_volume_down:
                if ctrl.mpv_player:
                    vol = ctrl.mpv_player.get_volume()
                    ctrl.set_volume(max(vol - 5, 0))

            elif key == Key.media_volume_mute:
                if ctrl.mpv_player:
                    vol = ctrl.mpv_player.get_volume()
                    # Toggle mute: set to 0 if above 0, or restore to 50 if already muted
                    ctrl.set_volume(0 if vol > 0 else 50)

        except Exception as e:
            logging.debug(f"MediaKeyBridge: Key handler error: {e}")

    def stop(self):
        """Stop the global listener on app exit."""
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
        self._ready = False
