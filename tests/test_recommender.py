"""
Unit tests for the RecommenderEngine candidate persistence, ingestion, and ranking.
"""

import unittest
from unittest.mock import MagicMock, patch
from recommender.recommender_engine import RecommenderEngine


class TestRecommenderEngine(unittest.TestCase):
    def test_recommender_initialization_with_candidates(self):
        fake_candidates = [
            {"title": "Song A", "artist": "Artist 1", "tempo": 120.0, "energy": 0.8, "valence": 0.7},
            {"title": "Song B", "artist": "Artist 2", "tempo": 110.0, "energy": 0.3, "valence": 0.2},
            {"title": "Song C", "artist": "Artist 3", "tempo": 125.0, "energy": 0.85, "valence": 0.75},
            {"title": "Song D", "artist": "Artist 4", "tempo": 90.0, "energy": 0.4, "valence": 0.3},
            {"title": "Song E", "artist": "Artist 5", "tempo": 122.0, "energy": 0.78, "valence": 0.65},
        ]
        with patch.object(RecommenderEngine, '_load_persistent_candidates', return_value=None):
            engine = RecommenderEngine()
            engine.load_library(fake_candidates)

            self.assertEqual(len(engine._song_library), 5)
            self.assertTrue(engine._library_fitted)

            # Recommend based on upbeat song
            recs = engine.recommend("Song A", top_n=2)
            self.assertTrue(len(recs) <= 2)
            self.assertIn(recs[0]["title"], ["Song A", "Song C", "Song E"])

    def test_language_heuristics(self):
        engine = RecommenderEngine()
        self.assertEqual(engine.detect_language("நெஞ்சே ஏழ்"), "ta")
        self.assertEqual(engine.detect_language("Kuthu Fire Anirudh"), "ta")
        self.assertEqual(engine.detect_language("Arijit Singh Bollywood Tum Hi Ho"), "hi")
        self.assertEqual(engine.detect_language("Hello World"), "en")


if __name__ == '__main__':
    unittest.main()
