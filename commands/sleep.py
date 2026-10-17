"""
M!sleep — Auto-stop playback after a given number of minutes (sleep timer).

Usage:
  M!sleep          → Show time remaining
  M!sleep 30       → Stop playback in 30 minutes
  M!sleep 1h       → Stop playback in 1 hour (60 minutes)
  M!sleep off      → Cancel active sleep timer
"""

import threading
import time
from player.playback_controller import get_controller

# Module-level timer state
_timer: threading.Timer | None = None
_stop_time: float | None = None   # Unix timestamp when playback will stop
_lock = threading.Lock()


def _execute_stop():
    """Called by the Timer thread when the sleep duration elapses."""
    global _timer, _stop_time
    with _lock:
        _timer = None
        _stop_time = None
    ctrl = get_controller()
    ctrl.stop()
    # Post a message to the TUI log if the callback is available
    log_cb = getattr(ctrl, "_app_log_callback", None)
    if log_cb:
        log_cb("[bold yellow]🌙 SLEEP TIMER:[/bold yellow] [dim]Playback stopped by sleep timer.[/dim]")


def _cancel():
    """Cancel any active sleep timer."""
    global _timer, _stop_time
    with _lock:
        if _timer:
            _timer.cancel()
            _timer = None
        _stop_time = None


def sleep(args: list[str]) -> str:
    global _timer, _stop_time

    # No args — show current state
    if not args:
        with _lock:
            if _stop_time is None:
                return (
                    "[dim]🌙 SLEEP TIMER: OFF[/dim]\n"
                    "  [dim]Usage: [bold]M!sleep 30[/bold] · [bold]M!sleep 1h[/bold] · "
                    "[bold]M!sleep off[/bold][/dim]"
                )
            remaining = max(0.0, _stop_time - time.time())
            rm, rs = divmod(int(remaining), 60)
            return (
                f"[bold yellow]🌙 SLEEP TIMER:[/bold yellow] "
                f"[white]{rm:02d}:{rs:02d}[/white] [dim]remaining[/dim]"
            )

    arg = args[0].lower()

    # Cancel timer
    if arg in ("off", "cancel", "stop", "none"):
        _cancel()
        return "[dim]🌙 SLEEP TIMER: CANCELLED[/dim]"

    # Parse duration: "30", "1h", "1h30", "90m"
    minutes = _parse_minutes(arg)
    if minutes is None:
        return (
            "[red]ERR: INVALID_DURATION[/red] [dim]Use: "
            "[bold]M!sleep 30[/bold] (minutes) or [bold]M!sleep 1h[/bold] (hours)[/dim]"
        )

    if minutes <= 0:
        return "[red]ERR: DURATION_MUST_BE_POSITIVE[/red]"

    # Cancel any existing timer
    _cancel()

    seconds = minutes * 60
    with _lock:
        _stop_time = time.time() + seconds
        _timer = threading.Timer(seconds, _execute_stop)
        _timer.daemon = True
        _timer.start()

    h, m = divmod(int(minutes), 60)
    if h > 0:
        dur_str = f"{h}h {m}m" if m else f"{h}h"
    else:
        dur_str = f"{m}m"

    return (
        f"[bold yellow]🌙 SLEEP TIMER:[/bold yellow] "
        f"[white]Playback will stop in {dur_str}[/white]  "
        f"[dim](Cancel: [bold]M!sleep off[/bold])[/dim]"
    )


def _parse_minutes(arg: str) -> float | None:
    """Parse '30', '1h', '1h30', '90m' → float minutes."""
    arg = arg.strip().lower()
    # e.g. "1h30" or "1h30m"
    if "h" in arg:
        parts = arg.split("h")
        try:
            hours = float(parts[0]) if parts[0] else 0
            mins = float(parts[1].replace("m", "")) if len(parts) > 1 and parts[1].replace("m", "") else 0
            return hours * 60 + mins
        except ValueError:
            return None
    # e.g. "90m" or "90"
    arg = arg.replace("m", "").replace("min", "")
    try:
        return float(arg)
    except ValueError:
        return None


def get_sleep_remaining() -> float | None:
    """Return remaining sleep seconds or None if no timer active."""
    with _lock:
        if _stop_time is None:
            return None
        return max(0.0, _stop_time - time.time())
