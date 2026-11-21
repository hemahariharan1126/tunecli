"""
Unit tests for PreDownloader thread safety, atomic file creation, and LRU eviction.
"""

import os
import tempfile
import unittest
from unittest.mock import patch
from player.pre_downloader import PreDownloader
from core.song import Song


class TestPreDownloader(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        with patch('player.pre_downloader.AUDIO_CACHE_DIR', self.temp_dir.name), \
             patch('player.pre_downloader.MAX_AUDIO_CACHE_FILES', 3):
            self.downloader = PreDownloader(max_workers=2)

    def tearDown(self):
        self.downloader.shutdown()
        self.temp_dir.cleanup()

    def test_lru_cache_eviction(self):
        """PreDownloader should strictly enforce MAX_AUDIO_CACHE_FILES."""
        with patch('player.pre_downloader.MAX_AUDIO_CACHE_FILES', 3):
            with self.downloader._lock:
                # Simulate 4 downloaded files with max limit of 3
                for i in range(4):
                    vid = f"vid_{i}"
                    fake_file = os.path.join(self.temp_dir.name, f"{vid}.webm")
                    with open(fake_file, "w") as f:
                        f.write("audio_data")
                    self.downloader._downloaded[vid] = fake_file
                    self.downloader._downloaded.move_to_end(vid)
                    self.downloader._enforce_cache_limit()

                # Oldest (vid_0) should have been evicted
                self.assertEqual(len(self.downloader._downloaded), 3)
                self.assertNotIn("vid_0", self.downloader._downloaded)
                self.assertIn("vid_3", self.downloader._downloaded)

    def test_get_local_path_thread_safe(self):
        fake_file = os.path.join(self.temp_dir.name, "song1.webm")
        with open(fake_file, "w") as f:
            f.write("content")

        with self.downloader._lock:
            self.downloader._downloaded["song1"] = fake_file

        path = self.downloader.get_local_path("song1")
        self.assertEqual(path, fake_file)

        # Nonexistent returns None
        self.assertIsNone(self.downloader.get_local_path("nonexistent"))


if __name__ == '__main__':
    unittest.main()
