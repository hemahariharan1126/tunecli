"""
M!background — Dynamic ambient music visualizer / mood background art generator.
Integrates with npx ascii-magic-art or falls back to aesthetic built-in ANSI art collections
to keep the terminal vibrant and calm while listening to music.
"""

import random
import subprocess
import shutil

# Built-in fallback ambient ASCII art landscapes for instant offline display
AMBIENT_THEMES = {
    "cosmic": [
        r"""[bold magenta]
          .       *   .   .  .   .  *  .
     .     .  *     .   .  *   .   .
       .      .   .   *   .    .   .  .
   .       *    .    /\    .   *   .   .
    .   .     .     /  \   .     .   .
  *       .   .    /    \    .     *
.    .  *    .    /      \  .   .    .
       .        /________\    .    .
  .     .  *   [  TUNECLI ]  *    .   .
        [/bold magenta][dim cyan]~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~[/dim cyan]
        [bold bright_blue]   Ambient Vibe: Cosmic Calm[/bold bright_blue]"""
    ],
    "retro": [
        r"""[bold bright_yellow]
       .---.
      /     \
     | () () |     [bold red]♫ RETRO WAVE AUDIO ♫[/bold red]
      \  _  /
       '---'
    [cyan]=========================================[/cyan]
    [magenta]|||||||||||||||||||||||||||||||||||||||||[/magenta]
    [bold green]   Ambient Vibe: Synthwave Horizon[/bold green]"""
    ],
    "aurora": [
        r"""[bold bright_cyan]
    .-.   .-.   .-.   .-.   .-.   .-.   .-.
   (   ) (   ) (   ) (   ) (   ) (   ) (   )
    '-'   '-'   '-'   '-'   '-'   '-'   '-'
  [bright_blue]~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~[/bright_blue]
  [bright_green]   ~ ~ ~ ~ Aurora Borealis Flow ~ ~ ~ ~  [/bright_green]
  [cyan]~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~[/cyan]
  [bold bright_white]   Ambient Vibe: Northern Lights[/bold bright_white]"""
    ]
}


def background(args):
    """
    Renders ambient background ASCII art.
    Usage:
      M!background         -> Random ambient art
      M!background npx     -> Fetch from npx ascii-magic-art
    """
    mode = args[0].lower() if args else "auto"

    # Try npx if requested or available
    if mode == "npx" or (mode == "auto" and shutil.which("npx")):
        try:
            # Run with short timeout
            res = subprocess.run(
                ["npx", "--yes", "ascii-magic-art"],
                capture_output=True,
                text=True,
                timeout=4,
                shell=True
            )
            if res.returncode == 0 and res.stdout.strip():
                return f"[bold bright_magenta]✨ AMBIENT ASCII ART[/bold bright_magenta]\n{res.stdout.strip()}"
        except Exception:
            pass  # Fall back gracefully to built-in presets

    # Built-in ambient theme
    category = random.choice(list(AMBIENT_THEMES.keys()))
    art = random.choice(AMBIENT_THEMES[category])
    return f"[bold bright_cyan]✨ AMBIENT BACKGROUND ({category.upper()})[/bold bright_cyan]\n{art}"
