"""
Unit tests for application shutdown and controller accessor safety.
"""

import unittest
from unittest.mock import patch
import player.playback_controller as pc


class TestShutdownSafety(unittest.TestCase):
    def setUp(self):
        # Reset controller singleton for isolated test
        pc._controller_instance = None

    def tearDown(self):
        pc._controller_instance = None

    def test_get_existing_controller_does_not_create(self):
        """get_existing_controller must return None and NOT instantiate a new controller."""
        self.assertIsNone(pc.get_existing_controller())
        self.assertIsNone(pc._controller_instance)

    def test_get_controller_creates_singleton(self):
        """get_controller creates instance once and returns the same on subsequent calls."""
        with patch('player.playback_controller.get_player'), \
             patch('player.playback_controller.get_pre_downloader'), \
             patch('player.playback_controller.MediaKeyBridge'):
            c1 = pc.get_controller()
            self.assertIsNotNone(c1)
            self.assertIs(pc.get_existing_controller(), c1)
            c2 = pc.get_controller()
            self.assertIs(c1, c2)


if __name__ == '__main__':
    unittest.main()
