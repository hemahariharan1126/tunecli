"""
IPC MPV Player — Lightweight, pure-Python MPV controller via JSON IPC.
Designed specifically for Android (Termux) and headless environments.
Requires NO python-mpv C-bindings or compilation.
"""

import json
import logging
import os
import platform
import socket
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any, Callable, Optional

from core.song import Song


def is_termux() -> bool:
    """Return True if running inside Termux on Android."""
    return "ANDROID_ROOT" in os.environ or os.path.exists("/data/data/com.termux")


def get_default_ipc_path() -> str:
    """Return a suitable IPC socket or named pipe path for the current OS."""
    if platform.system() == "Windows":
        return r"\\.\pipe\tunecli_mpv_pipe"
    if is_termux():
        termux_tmp = "/data/data/com.termux/files/usr/tmp"
        if os.path.isdir(termux_tmp):
            return os.path.join(termux_tmp, "tunecli_mpv.sock")
    return os.path.join(tempfile.gettempdir(), "tunecli_mpv.sock")


class MpvIpcPlayer:
    """
    Subprocess-driven MPV Player communicating via JSON IPC.
    Features 100% parity with MPVPlayer interface without C-extension dependencies.
    """

    def __init__(self, ipc_path: Optional[str] = None):
        self.ipc_path = ipc_path or get_default_ipc_path()
        self.process: Optional[subprocess.Popen] = None
        self._sock: Optional[socket.socket] = None
        self._win_pipe = None  # Handle for Windows named pipe
        self._is_windows = platform.system() == "Windows"
        
        self.playing = False
        self._is_paused = False
        self._current_song: Optional[Song] = None
        self._eof_callback: Optional[Callable] = None
        
        self._lock = threading.Lock()
        self._req_counter = 0
        self._responses: dict[int, Any] = {}
        self._response_events: dict[int, threading.Event] = {}
        self._listener_thread: Optional[threading.Thread] = None
        self._running = False
        
        # Cached values to prevent blocking TUI loop
        self._cached_pos = 0.0
        self._cached_duration = 0.0
        self._cached_volume = 100

        self._start_mpv_process()
        self._connect_ipc()

    def _start_mpv_process(self):
        """Spawn headless mpv daemon process with IPC enabled."""
        # Clean up stale Unix socket if present
        if not self._is_windows and os.path.exists(self.ipc_path):
            try:
                os.remove(self.ipc_path)
            except OSError:
                pass

        cmd = [
            "mpv",
            "--idle=yes",
            "--no-video",
            "--ytdl-format=bestaudio/best",
            "--demuxer-max-bytes=20M",
            "--demuxer-max-back-bytes=10M",
            "--network-timeout=15",
            f"--input-ipc-server={self.ipc_path}",
        ]

        if is_termux():
            # OpenSL ES is the native, lowest-overhead audio driver for Android
            cmd.extend(["--ao=opensles"])

        logging.info(f"MpvIpcPlayer: Launching daemon: {' '.join(cmd)}")
        try:
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "MPV executable not found. On Termux, run: pkg install mpv"
            )

    def _connect_ipc(self, timeout_sec: float = 4.0):
        """Establish connection to MPV IPC socket/pipe."""
        start = time.time()
        while time.time() - start < timeout_sec:
            try:
                if self._is_windows:
                    import msvcrt
                    # Connect to Windows named pipe
                    import win32file
                    import win32pipe
                    handle = win32file.CreateFile(
                        self.ipc_path,
                        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                        0,
                        None,
                        win32file.OPEN_EXISTING,
                        0,
                        None,
                    )
                    self._win_pipe = handle
                    break
                else:
                    if os.path.exists(self.ipc_path):
                        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                        sock.connect(self.ipc_path)
                        self._sock = sock
                        break
            except Exception:
                time.sleep(0.1)

        self._running = True
        self._listener_thread = threading.Thread(
            target=self._ipc_listener_loop, daemon=True, name="TuneCLI-MPV-IPC"
        )
        self._listener_thread.start()
        logging.info("MpvIpcPlayer: Successfully connected to MPV IPC.")

    def _ipc_listener_loop(self):
        """Background thread reading events and replies from MPV IPC."""
        buffer = ""
        while self._running:
            try:
                if self._is_windows and self._win_pipe:
                    import win32file
                    hr, data = win32file.ReadFile(self._win_pipe, 4096)
                    chunk = data.decode("utf-8", errors="ignore")
                elif self._sock:
                    raw = self._sock.recv(4096)
                    if not raw:
                        break
                    chunk = raw.decode("utf-8", errors="ignore")
                else:
                    break

                buffer += chunk
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        self._handle_ipc_message(line)
            except Exception as e:
                if self._running:
                    logging.debug(f"MpvIpcPlayer: Listener error: {e}")
                break

    def _handle_ipc_message(self, message: str):
        """Parse incoming JSON IPC messages."""
        try:
            msg = json.loads(message)
        except json.JSONDecodeError:
            return

        # Handle event messages
        if "event" in msg:
            event_name = msg.get("event")
            if event_name == "end-file":
                self.playing = False
                if self._eof_callback:
                    try:
                        self._eof_callback(msg)
                    except Exception as e:
                        logging.error(f"Error in EOF callback: {e}")
            elif event_name == "property-change":
                prop = msg.get("name")
                val = msg.get("data")
                if prop == "time-pos" and val is not None:
                    self._cached_pos = float(val)
                elif prop == "duration" and val is not None:
                    self._cached_duration = float(val)
                elif prop == "pause" and val is not None:
                    self._is_paused = bool(val)
                    self.playing = not self._is_paused
                elif prop == "volume" and val is not None:
                    self._cached_volume = int(val)

        # Handle command replies
        if "request_id" in msg:
            req_id = msg["request_id"]
            with self._lock:
                self._responses[req_id] = msg
                event = self._response_events.get(req_id)
                if event:
                    event.set()

    def _send_command(self, command: list[Any], timeout: float = 0.5) -> Optional[Any]:
        """Send a JSON IPC command and optionally await response."""
        with self._lock:
            self._req_counter += 1
            req_id = self._req_counter
            event = threading.Event()
            self._response_events[req_id] = event

        payload = json.dumps({"command": command, "request_id": req_id}) + "\n"
        try:
            if self._is_windows and self._win_pipe:
                import win32file
                win32file.WriteFile(self._win_pipe, payload.encode("utf-8"))
            elif self._sock:
                self._sock.sendall(payload.encode("utf-8"))
        except Exception as e:
            logging.warning(f"MpvIpcPlayer: Failed to send command {command}: {e}")
            return None

        if event.wait(timeout):
            with self._lock:
                resp = self._responses.pop(req_id, None)
                self._response_events.pop(req_id, None)
                if resp and resp.get("error") == "success":
                    return resp.get("data")
        else:
            with self._lock:
                self._response_events.pop(req_id, None)
                self._responses.pop(req_id, None)
        return None

    # ── Public Controller API (Parity with MPVPlayer) ──────────────────────────

    def set_eof_callback(self, callback: Callable):
        """Set a function to be called when a song ends playback."""
        self._eof_callback = callback

    def play(self, song: Song):
        """Stream a song using its YouTube Watch URL or direct stream URL."""
        url = f"https://www.youtube.com/watch?v={song.video_id}" if song.video_id else song.stream_url
        if not url:
            logging.error("No valid URL or Video ID to play.")
            return

        logging.info(f"[MpvIpcPlayer] Streaming: {url}")
        self._current_song = song
        self._send_command(["loadfile", url, "replace"])
        self.playing = True
        self._is_paused = False

    def play_local(self, song: Song, local_path: str):
        """Play a pre-downloaded local audio file."""
        if not local_path or not os.path.exists(local_path):
            self.play(song)
            return

        logging.info(f"[MpvIpcPlayer] Playing local file: {local_path}")
        self._current_song = song
        self._send_command(["loadfile", local_path, "replace"])
        self.playing = True
        self._is_paused = False

    def seek_to(self, position: float) -> None:
        """Seek to a specific position in seconds."""
        self._send_command(["seek", position, "absolute"])
        self._cached_pos = position

    def seek_relative(self, offset: float) -> None:
        """Seek relatively by offset in seconds."""
        self._send_command(["seek", offset, "relative"])

    def pause(self):
        """Pause playback."""
        self._send_command(["set_property", "pause", True])
        self.playing = False
        self._is_paused = True

    def resume(self):
        """Resume playback."""
        self._send_command(["set_property", "pause", False])
        self.playing = True
        self._is_paused = False

    def stop(self):
        """Stop playback completely."""
        self._send_command(["stop"])
        self.playing = False
        self._is_paused = False
        self._current_song = None

    def skip(self):
        """Skip current song."""
        self.stop()

    def set_volume(self, volume: int):
        """Set volume (0-100)."""
        vol = max(0, min(100, volume))
        self._send_command(["set_property", "volume", vol])
        self._cached_volume = vol

    def get_volume(self) -> int:
        """Get current volume."""
        data = self._send_command(["get_property", "volume"], timeout=0.1)
        if data is not None:
            self._cached_volume = int(data)
        return self._cached_volume

    def is_playing(self) -> bool:
        """Check if playing and not paused."""
        return self.playing and not self._is_paused

    def get_position(self) -> float:
        """Get current playback position in seconds."""
        data = self._send_command(["get_property", "time-pos"], timeout=0.08)
        if data is not None:
            self._cached_pos = float(data)
        return self._cached_pos

    def get_duration(self) -> float:
        """Get current song duration in seconds."""
        data = self._send_command(["get_property", "duration"], timeout=0.08)
        if data is not None:
            self._cached_duration = float(data)
        return self._cached_duration

    def set_eq(self, bands: list[int]) -> None:
        """
        Apply a 10-band equalizer using MPV's lavfi audio filter via IPC.
        Args:
            bands: List of 10 gain values in dB (-12 to +12).
        """
        freqs = [32, 64, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
        active = [
            f"equalizer=f={f}:width_type=o:w=2:g={g}"
            for f, g in zip(freqs, bands)
            if g != 0
        ]
        af_str = f"lavfi=[{','.join(active)}]" if active else ""
        self._send_command(["set_property", "af", af_str])
        logging.info(f"MpvIpcPlayer: Applied EQ: {bands}")

    def reset_eq(self) -> None:
        """Remove all audio filters (flat EQ)."""
        self._send_command(["set_property", "af", ""])

    def terminate(self):
        """Cleanup MPV process and IPC socket."""
        self._running = False
        try:
            self._send_command(["quit"], timeout=0.1)
        except Exception:
            pass

        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass

        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=1.0)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None

        if not self._is_windows and os.path.exists(self.ipc_path):
            try:
                os.remove(self.ipc_path)
            except OSError:
                pass
