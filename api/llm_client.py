"""
Multi-LLM Recommendation Client — Routes scenario analysis through Ollama Cloud or Gemini.
"""

import google.generativeai as genai
import json
import logging
import requests
from config import GEMINI_API_KEY, MOOD_MAP, OLLAMA_API_KEY, OLLAMA_MODEL, OLLAMA_BASE_URL, USE_OLLAMA_FOR_SCENARIO

class RecommendationLLMClient:
    def __init__(self):
        self.gemini_configured = bool(GEMINI_API_KEY)
        if self.gemini_configured:
            genai.configure(api_key=GEMINI_API_KEY)

    def _call_ollama(self, prompt: str) -> dict | None:
        """Call the Ollama Cloud (OpenAI-compatible chat completion) endpoint."""
        try:
            logging.info(f"LLMClient: Routing scenario to Ollama ({OLLAMA_MODEL})")
            headers = {
                "Authorization": f"Bearer {OLLAMA_API_KEY}",
                "Content-Type": "application/json"
            }
            # Assuming an OpenAI-compatible /v1/chat/completions endpoint
            payload = {
                "model": OLLAMA_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "response_format": {"type": "json_object"}
            }
            
            response = requests.post(OLLAMA_BASE_URL, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            # Parse OpenAI-style format
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                return self._parse_json(content)
            else:
                logging.warning("LLMClient: Ollama response missing 'choices'")
                return None
        except Exception as e:
            logging.error(f"LLMClient: Ollama request failed: {e}")
            return None

    def _call_gemini(self, prompt: str) -> dict:
        """Fallback to the Gemini rotating model pipeline."""
        if not self.gemini_configured:
            return {"error": "Both Ollama and Gemini failed. No API keys configured."}

        models_to_try = [
            'gemini-2.5-flash',
            'gemini-2.0-flash',
            'gemini-3-flash-preview',
            'gemini-2.0-flash-lite',
        ]
        
        last_error = ""
        for model_name in models_to_try:
            try:
                current_model = genai.GenerativeModel(model_name)
                logging.info(f"LLMClient: Routing scenario to Gemini ({model_name})")
                response = current_model.generate_content(prompt)
                
                parsed = self._parse_json(response.text)
                if parsed:
                    return parsed
                else:
                    last_error = "Failed to parse Gemini JSON output."
                    break
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "quota" in error_msg.lower():
                    logging.warning(f"Quota exceeded for {model_name}. Trying fallback...")
                    last_error = "Gemini API Quota Exceeded."
                    continue
                else:
                    logging.error(f"Gemini error with {model_name}: {e}")
                    last_error = error_msg
                    break
        
        return {"error": last_error}

    def _parse_json(self, text: str) -> dict | None:
        """Helper to cleanly extract JSON from markdown fences."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError as e:
            logging.error(f"LLMClient: JSON Parse Error: {e} \nRaw: {text}")
            return None

    def analyze_scenario(self, story: str) -> dict:
        """
        Analyze the user's story and return structured data for song recommendations.
        Attempts Ollama first (if configured), falls back to Gemini if quota/server fails.
        """
        prompt = f"""
        Analyze the following user story and suggest 5 songs that match the mood, tone, and language of the situation.
        Return the response in STRICT JSON format.
        
        Available mood categories: {list(MOOD_MAP.keys())}
        
        JSON Structure:
        {{
            "mood": "string",
            "tone": "string",
            "language": "string (ISO code like 'en', 'ta', 'hi')",
            "reasoning": "brief explanation",
            "queries": ["song 1 by artist", "song 2 by artist", ...]
        }}
        
        User Story: "{story}"
        """

        # 1. Try Ollama if enabled
        if USE_OLLAMA_FOR_SCENARIO and OLLAMA_API_KEY:
            ollama_result = self._call_ollama(prompt)
            if ollama_result and "error" not in ollama_result:
                return ollama_result
            logging.warning("LLMClient: Ollama failed or returned invalid data. Falling back to Gemini...")

        # 2. Fall back to Gemini
        return self._call_gemini(prompt)

    def identify_song(self, user_prompt: str) -> dict:
        """
        Uses strictly the Ollama API to deduce a specific song from a user's prompt or lyrics.
        """
        prompt = f"""
        Identify the exact song the user is referring to based on this prompt: '{user_prompt}'.
        Return the response in STRICT JSON format.
        
        JSON Structure:
        {{
            "title": "Exact Song Title",
            "artist": "Artist Name",
            "reasoning": "A short 1-sentence explanation of how you identified it."
        }}
        """
        
        if not (USE_OLLAMA_FOR_SCENARIO and OLLAMA_API_KEY):
            return {"error": "Ollama is not configured in .env. M!ask requires Ollama."}
            
        result = self._call_ollama(prompt)
        if not result or "error" in result:
            return {"error": "Ollama Cloud request failed or returned invalid data."}
            
        return result

    def get_similar_songs(self, seed_query: str, target_lang: str | None, limit: int = 5) -> list[dict]:
        """
        AI Fallback Recommender: Asks the LLM for similar songs when Spotify/YTMusic fail.
        Uses the multi-LLM engine (Ollama with Gemini fallback).
        """
        lang_instruction = f"The recommended songs MUST primarily be in this language code: '{target_lang}'." if target_lang else "The recommended songs should ideally match the language of the seed song."
        
        prompt = f"""
        Act as an expert music recommendation engine. 
        I am giving you a seed song/artist: '{seed_query}'.
        Please suggest exactly {limit} real, popular songs that sound musically similar in terms of genre, tempo, and vibe.
        {lang_instruction}
        
        Return the response in STRICT JSON format with a 'recommendations' array containing objects with 'title' and 'artist' keys.
        
        JSON Structure:
        {{
            "recommendations": [
                {{"title": "Song Title", "artist": "Artist Name"}}
            ]
        }}
        """

        # 1. Try Ollama if enabled
        if USE_OLLAMA_FOR_SCENARIO and OLLAMA_API_KEY:
            ollama_result = self._call_ollama(prompt)
            if ollama_result and "recommendations" in ollama_result:
                return ollama_result["recommendations"]
            logging.warning("LLMClient: Ollama failed to generate recommendations. Falling back to Gemini...")

        # 2. Fall back to Gemini
        gemini_result = self._call_gemini(prompt)
        if gemini_result and "recommendations" in gemini_result:
            return gemini_result["recommendations"]
            
        return []

    def extract_song_metadata(self, messy_query: str) -> str | None:
        """
        AI Search Corrector: Asks the LLM to identify the actual song from a messy, 
        misspelled, or descriptive query.
        Returns the corrected search string: 'Title by Artist'.
        """
        prompt = f"""
        Act as an expert music identifier.
        The user typed a messy or descriptive query: '{messy_query}'.
        Identify the real song they are looking for. Fix all spelling errors.
        
        Return the response in STRICT JSON format with a single key 'search_string' containing exactly "Song Title by Artist Name".
        If you absolutely cannot identify it, return an empty string.
        
        JSON Structure:
        {{
            "search_string": "Billie Jean by Michael Jackson"
        }}
        """

        if USE_OLLAMA_FOR_SCENARIO and OLLAMA_API_KEY:
            ollama_result = self._call_ollama(prompt)
            if ollama_result and "search_string" in ollama_result:
                return ollama_result["search_string"]

        gemini_result = self._call_gemini(prompt)
        if gemini_result and "search_string" in gemini_result:
            return gemini_result["search_string"]
            
        return None

# Singleton instance
llm_client = RecommendationLLMClient()

def get_llm_client():
    return llm_client
