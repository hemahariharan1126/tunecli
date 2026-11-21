"""
Unit tests for API resilience (Spotify degradation & LLM client).
"""

import unittest
from unittest.mock import MagicMock, patch
from api.spotify_client import SpotifyClient
from api.llm_client import RecommendationLLMClient


class TestAPIResilience(unittest.TestCase):
    def test_spotify_missing_credentials_graceful(self):
        """When credentials are empty, SpotifyClient should mark is_available False without raising."""
        with patch('api.spotify_client.SPOTIFY_CLIENT_ID', ''), \
             patch('api.spotify_client.SPOTIFY_CLIENT_SECRET', ''):
            client = SpotifyClient()
            self.assertFalse(client.is_available())
            self.assertIsNone(client.search_song("Beatles"))
            self.assertIsNone(client.get_audio_features("track123"))
            self.assertEqual(client.get_recommendations(["seed1"]), [])

    def test_spotify_403_degradation(self):
        """When Spotify returns 403 Forbidden, client should disable itself safely."""
        with patch('api.spotify_client.SPOTIFY_CLIENT_ID', 'test_id'), \
             patch('api.spotify_client.SPOTIFY_CLIENT_SECRET', 'test_secret'):
            client = SpotifyClient()
            client._is_active = True
            mock_sp = MagicMock()
            mock_sp.search.side_effect = Exception("HTTP 403 Forbidden: Developer restriction")
            client._sp = mock_sp

            result = client.search_song("Song")
            self.assertIsNone(result)
            self.assertFalse(client.is_available())

    def test_llm_client_missing_keys(self):
        """LLM Client should return error dict when no API keys are provided."""
        with patch('api.llm_client.GEMINI_API_KEY', ''), \
             patch('api.llm_client.OLLAMA_API_KEY', ''):
            client = RecommendationLLMClient()
            res = client.analyze_scenario("Coding late at night")
            self.assertIn("error", res)


if __name__ == '__main__':
    unittest.main()
