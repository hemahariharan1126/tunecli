"""
Unit tests for PlaybackState state machine transitions in PlaybackController.
"""

import unittest
from unittest.mock import MagicMock, patch
from core.song import Song
from core.playback_state import PlaybackState
from player.playback_controller import PlaybackController


class TestPlaybackStateTransitions(unittest.TestCase):
    def setUp(self):
        with patch('player.playback_controller.get_player'), \
             patch('player.playback_controller.get_pre_downloader'), \
             patch('player.playback_controller.MediaKeyBridge'):
            self.controller = PlaybackController()
            self.mock_player = MagicMock()
            self.mock_player.is_available.return_value = True
            self.mock_player.is_playing.return_value = False
            self.mock_player.play.return_value = True
            self.controller.mpv_player = self.mock_player

    def test_initial_state_idle(self):
        self.assertEqual(self.controller.state, PlaybackState.IDLE)

    def test_transition_on_play_next(self):
        song = Song(title="Test Track", artist="Artist", video_id="vid1")
        self.controller.queue_manager.add_song(song)

        self.controller._play_next()
        self.assertEqual(self.controller.state, PlaybackState.PLAYING)
        self.assertEqual(self.controller._current_song, song)

    def test_transition_on_pause_and_resume(self):
        self.controller.state = PlaybackState.PLAYING
        self.controller.pause()
        self.assertEqual(self.controller.state, PlaybackState.PAUSED)

        self.controller.resume()
        self.assertEqual(self.controller.state, PlaybackState.PLAYING)

    def test_transition_on_stop(self):
        self.controller.state = PlaybackState.PLAYING
        self.controller.stop()
        self.assertEqual(self.controller.state, PlaybackState.STOPPED)
        self.assertEqual(self.controller.queue_manager.queue_length(), 0)

    def test_transition_on_empty_queue(self):
        self.controller.queue_manager.clear()
        self.controller._play_next()
        self.assertEqual(self.controller.state, PlaybackState.IDLE)


if __name__ == '__main__':
    unittest.main()
