"""Logging configuration for the application."""

import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging for the application.

    Args:
        level: Logging level (default: INFO)
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr),
        ],
    )

    # Set third-party library loggers to WARNING to reduce noise
    logging.getLogger("spotipy").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("ytmusicapi").setLevel(logging.WARNING)
