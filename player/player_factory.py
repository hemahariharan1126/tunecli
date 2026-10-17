"""
Player Factory — Automatically selects the optimal audio backend:
- On Android / Termux: MpvIpcPlayer (headless, zero C-dependencies, OpenSL ES)
- On Desktop with python-mpv: MPVPlayer (C-types libmpv)
- Fallback: MpvIpcPlayer (subprocess MPV IPC)
"""

import logging
import os
from player.ipc_player import MpvIpcPlayer, is_termux

_player_instance = None


def get_player():
    """Retrieve or initialize the platform-appropriate player singleton."""
    global _player_instance
    if _player_instance is not None:
        return _player_instance

    # 1. On Termux / Android, always use lightweight IPC player
    if is_termux():
        logging.info("PlayerFactory: Detected Termux/Android — Using MpvIpcPlayer.")
        _player_instance = MpvIpcPlayer()
        return _player_instance

    # 2. On Desktop, attempt to use python-mpv if available
    try:
        from player.mpv_player import MPVPlayer
        _player_instance = MPVPlayer()
        logging.info("PlayerFactory: Using native MPVPlayer (python-mpv).")
        return _player_instance
    except (ImportError, RuntimeError, OSError) as e:
        logging.warning(
            f"PlayerFactory: python-mpv initialization failed ({e}). "
            "Falling back to MpvIpcPlayer."
        )

    # 3. Fallback to MpvIpcPlayer for headless/Linux or missing libmpv
    _player_instance = MpvIpcPlayer()
    return _player_instance
