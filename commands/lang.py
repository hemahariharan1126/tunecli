"""
Lang Command — M!lang [code|reset]
View, override, or reset the active language context for recommend & radio.
"""

from player.playback_controller import get_controller

# Supported language codes and their display names
SUPPORTED_LANGS: dict[str, str] = {
    "ta": "Tamil 🎵",
    "hi": "Hindi 🎵",
    "te": "Telugu 🎵",
    "ml": "Malayalam 🎵",
    "kn": "Kannada 🎵",
    "en": "English 🎵",
}


def lang(args: list[str]) -> str:
    """
    M!lang              — show current language context
    M!lang <code>       — manually override (ta, hi, te, ml, kn, en)
    M!lang reset        — clear lock; next M!play will re-detect
    """
    controller = get_controller()

    # ── No args → show current context ──────────────────────────────────────
    if not args:
        current = controller.seed_language
        if current:
            lang_name = SUPPORTED_LANGS.get(current, current.upper())
            source = "[dim](auto-detected)[/dim]" if not getattr(controller, "_lang_overridden", False) else "[dim](manual override)[/dim]"
            return (
                f"\n  [bold reverse cyan] LANG.CONTEXT [/bold reverse cyan]  "
                f"[bold bright_cyan]{lang_name}[/bold bright_cyan]  {source}\n"
                f"  [dim]recommend & radio will stay in this language.[/dim]\n"
                f"  [dim]Use [bold]M!lang reset[/bold] to clear, or [bold]M!lang <code>[/bold] to override.[/dim]"
            )
        else:
            return (
                "\n  [bold reverse yellow] LANG.CONTEXT [/bold reverse yellow]  "
                "[dim]Not set — will auto-detect on next [bold]M!play[/bold].[/dim]"
            )

    arg = args[0].strip().lower()

    # ── Reset ────────────────────────────────────────────────────────────────
    if arg == "reset":
        controller.seed_language = None
        controller._lang_overridden = False
        return (
            "\n  [bold reverse yellow] LANG.RESET [/bold reverse yellow]  "
            "[dim]Language context cleared.[/dim]\n"
            "  [dim]TuneCLI will auto-detect on your next [bold]M!play[/bold].[/dim]"
        )

    # ── Override ─────────────────────────────────────────────────────────────
    if arg not in SUPPORTED_LANGS:
        codes = "  ".join(
            f"[bold cyan]{code}[/bold cyan] [dim]{name}[/dim]"
            for code, name in SUPPORTED_LANGS.items()
        )
        return (
            f"[bold red]✗[/bold red] Unknown language code [bold]{arg}[/bold].\n"
            f"  Supported: {codes}"
        )

    controller.seed_language = arg
    controller._lang_overridden = True
    lang_name = SUPPORTED_LANGS[arg]
    return (
        f"\n  [bold reverse cyan] LANG.OVERRIDE [/bold reverse cyan]  "
        f"[bold bright_cyan]{lang_name}[/bold bright_cyan]\n"
        f"  [dim]recommend & radio will now search in [bold]{lang_name}[/bold].[/dim]"
    )
