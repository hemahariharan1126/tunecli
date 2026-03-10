"""
Command Parser — Parses M! prefixed commands from user input.
Supports quoted arguments using shlex.
"""

import shlex
from typing import Optional, List


COMMAND_PREFIX = "M!"

KNOWN_COMMANDS = {
    "play", "pause", "resume", "skip", "stop",
    "queue", "mood", "recommend", "volume", "help",
    "next", "prev", "radio", "find",
}


class ParsedCommand:
    def __init__(self, name: str, args: List[str]):
        self.name = name
        self.args = args

    def __repr__(self):
        return f"ParsedCommand(name={self.name!r}, args={self.args!r})"


def parse_command(raw_input: str) -> Optional[ParsedCommand]:
    """
    Parse a raw command string into ParsedCommand.

    Example:
        M!play "Jocelyn Flores"
        M!pause
    """

    raw_input = raw_input.strip()

    # Check prefix
    if not raw_input.startswith(COMMAND_PREFIX):
        return None

    # Remove prefix
    body = raw_input[len(COMMAND_PREFIX):].strip()

    if not body:
        return None

    try:
        tokens = shlex.split(body)
    except ValueError:
        return None

    cmd_name = tokens[0].lower()

    if cmd_name not in KNOWN_COMMANDS:
        return None

    args = tokens[1:]

    return ParsedCommand(cmd_name, args)