"""
Logger — Configures Loguru for application-wide logging.
"""

import sys
from loguru import logger

# Remove default handler and add a styled file + stderr handler
logger.remove()
logger.add(
    "tunecli.log",
    rotation="5 MB",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{line} | {message}",
)
logger.add(
    sys.stderr,
    level="ERROR",
    colorize=True,
    format="<red>{time:HH:mm:ss}</red> | <level>{level}</level> | {message}",
)

__all__ = ["logger"]
