"""
StatusBar Component — Always-visible 1-line HUD for TuneCLI.
Shows: radio mode, queue count, volume, playback time, language lock.
"""

from textual.widgets import Static
from textual.reactive import reactive


class StatusBar(Static):
    """A compact top-of-screen HUD showing persistent system state."""

    status_text: reactive[str] = reactive("")

    def render(self) -> str:
        return self.status_text

    def update_state(self, controller) -> None:
        """Sync with controller state every tick."""
        # Radio badge
        radio = (
            "[bold magenta]📻 RADIO[/bold magenta][dim]:ON [/dim]"
            if controller.radio_mode
            else "[dim]📻 RADIO:OFF  [/dim]"
        )

        # Queue count
        q_len = len(controller.get_queue())
        queue = f"[bold cyan]🎵 QUEUE:[/bold cyan][white]{q_len:>2}[/white]  "

        # Volume
        vol = 0
        if controller.mpv_player:
            vol = controller.mpv_player.get_volume()
        vol_filled = int(vol / 10)
        vol_empty  = 10 - vol_filled
        vol_bar    = "[cyan]" + "█" * vol_filled + "[/cyan]" + "[bright_black]" + "░" * vol_empty + "[/bright_black]"
        volume_str = f"[bold cyan]🔊[/bold cyan] {vol_bar} [white]{vol:>3}%[/white]  "

        # Playback time
        time_str = "[dim]⏱ --:-- / --:--[/dim]"
        if controller.mpv_player:
            song = controller.queue_manager.now_playing()
            if song:
                dur = controller.mpv_player.get_duration() or getattr(song, "duration", 0) or 1
                pos = controller.mpv_player.get_position()
                mc, sc = divmod(int(pos), 60)
                mt, st = divmod(int(dur), 60)
                time_str = f"[dim]⏱[/dim] [white]{mc:02d}:{sc:02d}[/white][dim] / {mt:02d}:{st:02d}[/dim]"

        # Language lock badge
        lang_code = getattr(controller, "seed_language", None)
        if lang_code:
            lang_badge = f"[bold bright_cyan]🌐 {lang_code.upper()}[/bold bright_cyan]  "
        else:
            lang_badge = "[dim]🌐 —  [/dim]"

        # EQ engine badge
        eq_enabled = getattr(controller, "eq_enabled", False)
        eq_badge = (
            "[bold bright_cyan]⚡EQ:ON[/bold bright_cyan]"
            if eq_enabled
            else "[dim]⚡EQ:OFF[/dim]"
        )

        # Loop mode badge
        repeat_mode = getattr(controller.queue_manager, "repeat_mode", "none")
        if repeat_mode == "one":
            loop_badge = "  [bold bright_cyan]🔂 LOOP:ONE[/bold bright_cyan]"
        elif repeat_mode == "all":
            loop_badge = "  [bold bright_cyan]🔁 LOOP:ALL[/bold bright_cyan]"
        else:
            loop_badge = ""

        # Shuffle mode badge
        shuffle_badge = (
            "  [bold bright_cyan]🔀 SHUFFLE[/bold bright_cyan]"
            if getattr(controller.queue_manager, "shuffle_mode", False)
            else ""
        )

        # Speed badge (only if non-1.0x)
        speed = 1.0
        if controller.mpv_player and hasattr(controller.mpv_player, "get_speed"):
            speed = controller.mpv_player.get_speed()
        speed_badge = f"  [bold yellow]⚡{speed:.1f}×[/bold yellow]" if abs(speed - 1.0) > 0.05 else ""

        # Sleep timer badge
        sleep_badge = ""
        try:
            from commands.sleep import get_sleep_remaining
            rem = get_sleep_remaining()
            if rem and rem > 0:
                rm, _ = divmod(int(rem), 60)
                sleep_badge = f"  [bold yellow]🌙{rm}m[/bold yellow]"
        except Exception:
            pass

        # Crossfade badge
        cf = getattr(controller, "crossfade_seconds", 0)
        cf_badge = f"  [dim]〰{cf}s[/dim]" if cf > 0 else ""

        # App name branding
        brand = "[bold bright_cyan]⚡ M! TuneCLI[/bold bright_cyan]  [dim]│[/dim]  "

        self.status_text = (
            brand + radio + "  " + queue + volume_str + time_str
            + "  " + lang_badge + eq_badge + loop_badge + shuffle_badge
            + speed_badge + sleep_badge + cf_badge
        )
