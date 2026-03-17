"""
Command Router — Dispatches parsed commands to the correct handler.
"""

from commands.play import play
from commands.pause import pause
from commands.resume import resume
from commands.skip import skip
from commands.stop import stop
from commands.queue import show_queue
from commands.mood import mood
from commands.recommend import recommend
from commands.volume import volume
from commands.help import help_command
from commands.next import next_command
from commands.prev import prev
from commands.radio import radio
from commands.find import find
from commands.scenario import scenario


COMMAND_MAP = {
    "play": play,
    "pause": pause,
    "resume": resume,
    "skip": skip,
    "stop": stop,
    "queue": show_queue,
    "mood": mood,
    "recommend": recommend,
    "volume": volume,
    "help": help_command,
    "next": next_command,
    "prev": prev,
    "radio": radio,
    "find": find,
    "scenario": scenario,
}


def execute_command(parsed_command):

    command_name = parsed_command.name
    args = parsed_command.args

    if command_name not in COMMAND_MAP:
        print("Unknown command")
        return

    handler = COMMAND_MAP[command_name]

    handler(args)