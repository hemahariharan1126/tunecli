"""
EQ Command — M!eq [on|off|reset|info]
Controls the LLM-driven per-song equalizer optimization.
"""

from player.playback_controller import get_controller
from equalizer.eq_engine import EQEngine, BAND_LABELS, FLAT_EQ


def eq(args: list[str]) -> str:
    """
    M!eq              — show EQ status + current band bar chart
    M!eq on           — enable auto-EQ (default)
    M!eq off          — disable auto-EQ (flat for all songs)
    M!eq reset        — immediately apply flat EQ to current song
    M!eq info         — show cached EQ for the currently-playing song
    """
    controller = get_controller()
    engine: EQEngine = controller.eq_engine

    arg = args[0].strip().lower() if args else ""

    # ── on ────────────────────────────────────────────────────────────────────
    if arg == "on":
        controller.eq_enabled = True
        # Re-apply EQ for the current song if one is playing
        current = controller.queue_manager.now_playing()
        if current and controller.mpv_player:
            import threading
            threading.Thread(
                target=engine.apply_for_song_with_lang,
                args=(current, controller.mpv_player, controller.seed_language or "en"),
                daemon=True,
            ).start()
        return (
            "\n  [bold reverse cyan] EQ.ENGINE [/bold reverse cyan]  "
            "[bold bright_cyan]AUTO-EQ: ON[/bold bright_cyan]\n"
            "  [dim]LLM will optimize the equalizer for each song.[/dim]"
        )

    # ── off ───────────────────────────────────────────────────────────────────
    if arg == "off":
        controller.eq_enabled = False
        engine.reset(controller.mpv_player)
        return (
            "\n  [bold reverse yellow] EQ.ENGINE [/bold reverse yellow]  "
            "[bold yellow]AUTO-EQ: OFF[/bold yellow]\n"
            "  [dim]Flat EQ applied. Use [bold]M!eq on[/bold] to re-enable.[/dim]"
        )

    # ── reset ─────────────────────────────────────────────────────────────────
    if arg == "reset":
        engine.reset(controller.mpv_player)
        return (
            "\n  [bold reverse magenta] EQ.RESET [/bold reverse magenta]  "
            "[dim]Flat EQ applied to current track.[/dim]"
        )

    # ── info — show cached EQ for currently-playing song ─────────────────────
    if arg == "info":
        current = controller.queue_manager.now_playing()
        if not current:
            return "[yellow]⚠  No track currently playing.[/yellow]"
        cached = engine.get_cached_eq(current)
        if cached:
            chart = EQEngine.format_bar_chart(cached)
            return (
                f"\n  [bold reverse cyan] EQ.CACHED [/bold reverse cyan]  "
                f"[bold]{current.title}[/bold] [dim]by {current.artist}[/dim]\n"
                f"{chart}"
            )
        else:
            return (
                f"  [dim]No cached EQ for '[bold]{current.title}[/bold]'. "
                f"It will be generated when the song plays.[/dim]"
            )

    # ── default — show full status + current bands ────────────────────────────
    status_label = (
        "[bold bright_cyan]AUTO-EQ: ON ✓[/bold bright_cyan]"
        if controller.eq_enabled
        else "[bold yellow]AUTO-EQ: OFF[/bold yellow]"
    )
    cache_count = engine.cache_size()
    current_bands = engine.get_current_bands()

    header = (
        f"\n  [bold reverse cyan] EQ.ENGINE [/bold reverse cyan]  "
        f"{status_label}  [dim]│[/dim]  "
        f"[dim]Cache: [bold]{cache_count}[/bold] presets[/dim]\n"
    )

    # Check if EQ is flat
    is_flat = all(g == 0 for g in current_bands)
    if is_flat:
        chart = "  [dim]Flat EQ — no active bands. Play a song to generate an LLM preset.[/dim]"
    else:
        chart = EQEngine.format_bar_chart(current_bands)

    # Show current song label
    current = controller.queue_manager.now_playing()
    if current:
        song_line = (
            f"  [dim]Active preset for:[/dim] [bold]{current.title}[/bold] "
            f"[dim]by {current.artist}[/dim]\n"
        )
    else:
        song_line = "  [dim]No track playing.[/dim]\n"

    hints = (
        "\n  [dim]Commands: [bold]M!eq on[/bold] · [bold]M!eq off[/bold] · "
        "[bold]M!eq reset[/bold] · [bold]M!eq info[/bold][/dim]"
    )

    return header + song_line + chart + hints
