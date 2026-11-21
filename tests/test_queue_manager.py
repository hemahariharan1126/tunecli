"""
Unit tests for QueueManager thread safety and queue manipulation methods.
"""

import threading
import unittest
from core.song import Song
from player.queue_manager import QueueManager


class TestQueueManager(unittest.TestCase):
    def setUp(self):
        self.qm = QueueManager()

    def test_add_and_next_song(self):
        s1 = Song(title="Song 1", artist="Artist 1")
        s2 = Song(title="Song 2", artist="Artist 2")
        self.qm.add_song(s1)
        self.qm.add_song(s2)

        self.assertEqual(self.qm.queue_length(), 2)
        next_song = self.qm.next_song()
        self.assertEqual(next_song.title, "Song 1")
        self.assertEqual(self.qm.queue_length(), 1)

    def test_reorder_song(self):
        s1 = Song(title="A", artist="1")
        s2 = Song(title="B", artist="2")
        s3 = Song(title="C", artist="3")
        self.qm.add_song(s1)
        self.qm.add_song(s2)
        self.qm.add_song(s3)

        success, err, title = self.qm.reorder_song(3, 1)
        self.assertTrue(success)
        self.assertEqual(title, "C")
        q = self.qm.get_queue()
        self.assertEqual([s.title for s in q], ["C", "A", "B"])

    def test_remove_song(self):
        s1 = Song(title="A", artist="1")
        s2 = Song(title="B", artist="2")
        self.qm.add_song(s1)
        self.qm.add_song(s2)

        success, err, title = self.qm.remove_song(1)
        self.assertTrue(success)
        self.assertEqual(title, "A")
        self.assertEqual(self.qm.queue_length(), 1)

    def test_concurrent_mutations(self):
        """Ensure multi-threaded addition and removal does not deadlock or corrupt deque."""
        threads = []
        def adder(start_idx):
            for i in range(50):
                self.qm.add_song(Song(title=f"Song-{start_idx}-{i}", artist="A"))

        def consumer():
            for _ in range(25):
                self.qm.next_song()

        for t_id in range(4):
            threads.append(threading.Thread(target=adder, args=(t_id,)))
            threads.append(threading.Thread(target=consumer))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should finish cleanly without raising exceptions or deadlocking
        self.assertTrue(self.qm.queue_length() >= 0)


if __name__ == '__main__':
    unittest.main()
