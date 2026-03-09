"""
Config Loader — Runtime validation and loading of application configuration.
"""

import config
from utils.logger import logger


def validate_config() -> bool:
    """
    Check that required environment variables are set.
    Returns True if config is valid, False if missing critical values.
    """
    missing = []
    if not config.SPOTIFY_CLIENT_ID:
        missing.append("SPOTIFY_CLIENT_ID")
    if not config.SPOTIFY_CLIENT_SECRET:
        missing.append("SPOTIFY_CLIENT_SECRET")

    if missing:
        logger.warning(f"Missing configuration keys: {', '.join(missing)}")
        return False
    return True


def get_config_summary() -> dict:
    """Return a safe (non-secret) summary of current config."""
    return {
        "spotify_configured": bool(config.SPOTIFY_CLIENT_ID),
        "quality_thresholds": {
            "high": config.QUALITY_HIGH_THRESHOLD,
            "medium": config.QUALITY_MEDIUM_THRESHOLD,
        },
        "n_clusters": config.N_CLUSTERS,
        "moods_available": list(config.MOOD_MAP.keys()),
    }
