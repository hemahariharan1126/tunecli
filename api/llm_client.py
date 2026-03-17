"""
Gemini LLM Client — Analyzes user stories to extract mood, tone, and song suggestions.
"""

import google.generativeai as genai
import json
import logging
from config import GEMINI_API_KEY, MOOD_MAP

class GeminiClient:
    def __init__(self):
        if not GEMINI_API_KEY:
            logging.warning("GEMINI_API_KEY not found in environment.")
            self.model = None
            return
            
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-3-flash-preview')

    def analyze_scenario(self, story: str) -> dict:
        """
        Analyze the user's story and return structured data for song recommendations.
        Attempts fallback to different models if quota is exceeded.
        """
        if not self.model:
            return {"error": "Gemini API key not configured."}

        # List of models to try in order of preference
        models_to_try = ['gemini-2.0-flash', 'gemini-3-flash-preview', 'gemini-1.5-flash-8b']
        
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

        last_error = ""
        for model_name in models_to_try:
            try:
                current_model = genai.GenerativeModel(model_name)
                response = current_model.generate_content(prompt)
                
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.endswith("```"):
                    text = text[:-3]
                
                return json.loads(text.strip())
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "quota" in error_msg.lower():
                    logging.warning(f"Quota exceeded for {model_name}. Trying fallback...")
                    last_error = "API Quota Exceeded. Please try again in a minute."
                    continue
                else:
                    logging.error(f"Gemini error with {model_name}: {e}")
                    last_error = error_msg
                    break # Don't retry for non-quota errors
        
        return {"error": last_error}

# Singleton instance
llm_client = GeminiClient()

def get_llm_client():
    return llm_client
