"""Unit tests for logging configuration."""

import logging
import sys
import pytest
from unittest.mock import patch, MagicMock
from spotify_to_ytmusic.logging_config import setup_logging


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_configures_basic_config(self):
        """Should configure logging with basicConfig."""
        with patch("logging.basicConfig") as mock_basic_config:
            setup_logging()

            mock_basic_config.assert_called_once()
            call_kwargs = mock_basic_config.call_args[1]
            assert call_kwargs["level"] == logging.INFO
            assert "%(asctime)s" in call_kwargs["format"]
            assert "%(name)s" in call_kwargs["format"]
            assert "%(levelname)s" in call_kwargs["format"]
            assert "%(message)s" in call_kwargs["format"]

    def test_uses_custom_log_level(self):
        """Should accept custom log level."""
        with patch("logging.basicConfig") as mock_basic_config:
            setup_logging(level=logging.DEBUG)

            call_kwargs = mock_basic_config.call_args[1]
            assert call_kwargs["level"] == logging.DEBUG

    def test_configures_stderr_handler(self):
        """Should configure StreamHandler to stderr."""
        with patch("logging.basicConfig") as mock_basic_config:
            setup_logging()

            call_kwargs = mock_basic_config.call_args[1]
            handlers = call_kwargs["handlers"]
            assert len(handlers) == 1
            assert isinstance(handlers[0], logging.StreamHandler)
            assert handlers[0].stream == sys.stderr

    def test_sets_third_party_loggers_to_warning(self):
        """Should set third-party library loggers to WARNING."""
        with patch("logging.basicConfig"):
            with patch("logging.getLogger") as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger

                setup_logging()

                # Should be called for spotipy, urllib3, and ytmusicapi
                assert mock_get_logger.call_count == 3
                mock_get_logger.assert_any_call("spotipy")
                mock_get_logger.assert_any_call("urllib3")
                mock_get_logger.assert_any_call("ytmusicapi")

                # Each logger should be set to WARNING
                assert mock_logger.setLevel.call_count == 3
                for call in mock_logger.setLevel.call_args_list:
                    assert call[0][0] == logging.WARNING

    def test_default_level_is_info(self):
        """Should default to INFO level."""
        with patch("logging.basicConfig") as mock_basic_config:
            setup_logging()

            call_kwargs = mock_basic_config.call_args[1]
            assert call_kwargs["level"] == logging.INFO
