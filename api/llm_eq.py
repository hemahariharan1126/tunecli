"""
LLM EQ Client — Ultra-compact Gemini client for per-song EQ inference.

Token-optimization design:
  - System prompt: ~120 tokens, amortized over the full session
  - User message:  ~15-25 tokens  ("title|artist|lang|mood")
  - Response:      ~20 tokens     ([2,4,3,1,0,-1,-2,1,2,-1])
  - Same-song:     0 tokens       (disk cache hit in EQEngine)

Total saving vs naive approach: ~85-90% token reduction per request.
"""

import json
import logging
from google import genai
from google.genai import types

from config import GEMINI_API_KEY

# ── EQ band frequencies (10-band) ─────────────────────────────────────────────
BANDS = [32, 64, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]

# ── Compact system prompt (~120 tokens) ──────────────────────────────────────
_SYSTEM = (
    "You are an audio engineer. Given a song fingerprint 'title|artist|lang|mood', "
    "return ONLY a JSON array of exactly 10 integers (dB gains, -12 to 12) for these "
    "10 EQ bands: [32Hz,64Hz,125Hz,250Hz,500Hz,1kHz,2kHz,4kHz,8kHz,16kHz]. "
    "No text. No keys. No explanation. Example: [2,4,1,0,-1,-2,1,3,2,-1]\n"
    "Rules:\n"
    "- Bass/kuthu/edm/rap: 32Hz+4,64Hz+5\n"
    "- Emotional/vocals: 1kHz+2,2kHz+2\n"
    "- Classical/acoustic: flat bass, 4kHz+2,8kHz+2\n"
    "- Lofi/chill: 8kHz-2,16kHz-3\n"
    "- Tamil film: 32Hz+3,64Hz+4\n"
    "- Pop: 2kHz+1,4kHz+1\n"
    "- Rock: 64Hz+3,2kHz+2\n"
    "- Jazz: 250Hz+2,4kHz+1\n"
    "Clamp each value to [-12,12]."
)

# ── Fallback presets (offline / API error) ────────────────────────────────────
FALLBACK_PRESETS: dict[str, list[int]] = {
    "kuthu":     [ 4,  5,  3,  2,  1,  0, -1, -1,  0,  0],
    "emotional": [ 1,  2,  2,  1,  0,  2,  2,  1,  0, -1],
    "classical": [ 0,  0,  1,  1,  0,  0,  1,  2,  2,  1],
    "lofi":      [ 2,  3,  2,  1,  0, -1, -1, -2, -2, -3],
    "chill":     [ 1,  2,  1,  0,  0,  0,  0, -1, -2, -3],
    "edm":       [ 4,  4,  2,  0, -1,  0,  1,  2,  3,  3],
    "party":     [ 3,  4,  2,  1,  0,  0,  1,  2,  2,  2],
    "sad":       [ 0,  1,  2,  1,  0,  1,  2,  1,  0, -1],
    "focus":     [ 0,  1,  1,  0,  0,  0,  0,  1,  1,  0],
    "rock":      [ 2,  3,  1,  0,  0,  2,  2,  1,  0,  0],
    "pop":       [ 1,  2,  1,  0,  0,  0,  1,  2,  2,  1],
    "jazz":      [ 0,  0,  2,  2,  1,  0,  0,  1,  1,  0],
    "default":   [ 0,  2,  1,  0,  0,  0,  0,  1,  1,  0],
}

MODELS_TO_TRY = ["gemini-2.0-flash", "gemini-1.5-flash-8b"]


class LLMEQClient:
    """
    Token-optimized Gemini client that infers a 10-band EQ for a song.

    User message format:  "title|artist|lang_code|mood"
    Response format:      [int, int, int, int, int, int, int, int, int, int]
    """

    def __init__(self):
        self._ready = False
        if not GEMINI_API_KEY:
            logging.warning("LLMEQClient: GEMINI_API_KEY not set — will use fallback presets.")
            return
        try:
            self._client = genai.Client(api_key=GEMINI_API_KEY)
            self._ready = True
            logging.info("LLMEQClient: Gemini EQ client ready.")
        except Exception as e:
            logging.warning(f"LLMEQClient: Init failed ({e}) — will use fallback presets.")

    def get_eq(self, title: str, artist: str, lang: str = "en", mood: str = "") -> list[int]:
        """
        Infer 10-band EQ gains for a song. Returns a list of 10 ints in [-12, 12].

        Tries Gemini API first; falls back to hardcoded genre presets on failure.
        """
        if not self._ready:
            return self._fallback(mood)

        # Compact fingerprint — ~15-25 tokens
        fingerprint = f"{title}|{artist}|{lang}|{mood or 'general'}"

        last_err = ""
        for model_id in MODELS_TO_TRY:
            try:
                response = self._client.models.generate_content(
                    model=model_id,
                    contents=[fingerprint],
                    config=types.GenerateContentConfig(
                        system_instruction=_SYSTEM,
                        response_mime_type="application/json",
                        temperature=0.2,         # Low temp = consistent, predictable EQ
                        max_output_tokens=60,    # 10 integers + brackets + commas = ~30 tokens max
                    ),
                )
                raw = response.text.strip()
                bands = self._parse(raw)
                if bands:
                    logging.info(f"LLMEQClient: EQ for '{title}': {bands}")
                    return bands
            except Exception as e:
                last_err = str(e)
                if "429" in last_err or "quota" in last_err.lower():
                    logging.warning(f"LLMEQClient: Quota hit on {model_id}, trying fallback model.")
                    continue
                logging.warning(f"LLMEQClient: {model_id} error — {e}")
                break

        logging.warning(f"LLMEQClient: All models failed ({last_err}). Using preset fallback.")
        return self._fallback(mood)

    def _parse(self, raw: str) -> list[int] | None:
        """Parse and validate a 10-integer JSON array from the LLM response."""
        try:
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw.strip())
            if isinstance(data, list) and len(data) == 10:
                clamped = [max(-12, min(12, int(v))) for v in data]
                return clamped
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logging.warning(f"LLMEQClient: Parse failed ({e}) on: {raw!r}")
        return None

    def _fallback(self, mood: str) -> list[int]:
        """Return a hardcoded preset matched to the song's mood."""
        key = (mood or "").lower().strip()
        preset = FALLBACK_PRESETS.get(key, FALLBACK_PRESETS["default"])
        logging.info(f"LLMEQClient: Using fallback preset for mood='{key}': {preset}")
        return preset


# ── Singleton ─────────────────────────────────────────────────────────────────
_llm_eq_client: LLMEQClient | None = None


def get_llm_eq_client() -> LLMEQClient:
    global _llm_eq_client
    if _llm_eq_client is None:
        _llm_eq_client = LLMEQClient()
    return _llm_eq_client
