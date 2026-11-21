"""
Unit tests for command_parser.
"""

import unittest
from parser.command_parser import parse_command, ParsedCommand


class TestCommandParser(unittest.TestCase):
    def test_parse_valid_command(self):
        cmd = parse_command("M!play Hello World")
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.name, "play")
        self.assertEqual(cmd.args, ["Hello", "World"])

    def test_parse_quoted_args(self):
        cmd = parse_command('M!play "Jocelyn Flores" 320')
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.name, "play")
        self.assertEqual(cmd.args, ["Jocelyn Flores", "320"])

    def test_invalid_prefix(self):
        cmd = parse_command("play Hello")
        self.assertIsNone(cmd)

    def test_unknown_command(self):
        cmd = parse_command("M!nonexistentcommand")
        self.assertIsNone(cmd)

    def test_empty_command(self):
        self.assertIsNone(parse_command(""))
        self.assertIsNone(parse_command("M!"))


if __name__ == '__main__':
    unittest.main()
