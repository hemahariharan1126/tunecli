"""
Unit tests for MPVPlayer lifecycle, lazy loading, and error handling.
"""

import unittest
from unittest.mock import MagicMock, patch
from core.song import Song
from player.mpv_player import MPVPlayer


class TestMPVPlayerLifecycle(unittest.TestCase):
    def test_uninitialized_state_safety(self):
        """Player with failed/absent MPV backend should fail gracefully without crashing."""
        with patch.object(MPVPlayer, '_initialize', return_value=None):
            player = MPVPlayer()
            player.player = None
            player._init_error = "Mock missing MPV"

            self.assertFalse(player.is_available())
            self.assertEqual(player.get_init_error(), "Mock missing MPV")

            # All playback operations must return cleanly without throwing exceptions
            song = Song(title="Test Song", stream_url="http://example.com/audio.mp3")
            self.assertFalse(player.play(song))
            self.assertFalse(player.play_local(song, "/tmp/fake.webm"))
            self.assertEqual(player.get_position(), 0.0)
            self.assertEqual(player.get_duration(), 0.0)
            self.assertFalse(player.is_playing())
            self.assertFalse(player.is_paused())

            # Control operations must safely no-op
            player.pause()
            player.resume()
            player.seek_to(10.0)
            player.seek_relative(5.0)
            player.set_volume(80)
            self.assertEqual(player.get_volume(), 100)
            player.stop()
            player.terminate()
            # Idempotent termination
            player.terminate()

    def test_mock_successful_playback(self):
        """Test playback and volume controls when MPV mock is active."""
        with patch.object(MPVPlayer, '_initialize', return_value=None):
            player = MPVPlayer()
            mock_mpv = MagicMock()
            mock_mpv.pause = False
            mock_mpv.volume = 85
            mock_mpv.time_pos = 42.5
            mock_mpv.duration = 180.0
            player.player = mock_mpv

            self.assertTrue(player.is_available())
            song = Song(title="Active Song", video_id="abc123xyz")
            self.assertTrue(player.play(song))
            self.assertTrue(player.playing)
            self.assertEqual(player.get_position(), 42.5)
            self.assertEqual(player.get_duration(), 180.0)

            player.pause()
            self.assertTrue(mock_mpv.pause)
            player.resume()
            self.assertFalse(mock_mpv.pause)

            player.set_volume(50)
            self.assertEqual(mock_mpv.volume, 50)
            self.assertEqual(player.get_volume(), 50)


if __name__ == '__main__':
    unittest.main()
