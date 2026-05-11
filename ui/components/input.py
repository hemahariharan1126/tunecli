"""
Input Component — Enhanced command line with suggester.
"""

from textual.widgets import Input
from textual.suggester import Suggester

class CommandSuggester(Suggester):
    """Suggests available M! commands."""
    
    def __init__(self, commands: list[str]):
        super().__init__()
        self.commands = commands

    async def get_suggestion(self, value: str) -> str | None:
        if value.startswith("M!"):
            cmd_part = value[2:].lower()
            for cmd in self.commands:
                if cmd.startswith(cmd_part):
                    return f"M!{cmd}"
        return None

class CommandInput(Input):
    """Specialized Input widget for TuneCLI commands."""
    pass
