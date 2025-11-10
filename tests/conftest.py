"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import Mock, patch


@pytest.fixture
def mock_spotify_client():
    """Fixture for mocked Spotify client."""
    with patch("spotify_to_ytmusic.services.spotify_service.spotipy.Spotify") as mock_sp, \
         patch("spotify_to_ytmusic.services.spotify_service.SpotifyOAuth") as mock_oauth:
        mock_instance = Mock()
        mock_sp.return_value = mock_instance
        yield mock_instance, mock_sp, mock_oauth


@pytest.fixture
def mock_ytmusic_client():
    """Fixture for mocked YouTube Music client."""
    with patch("spotify_to_ytmusic.services.ytmusic_service.os.path.exists") as mock_exists, \
         patch("spotify_to_ytmusic.services.ytmusic_service.YTMusic") as mock_yt:
        mock_exists.return_value = True
        mock_instance = Mock()
        mock_yt.return_value = mock_instance
        yield mock_instance, mock_yt, mock_exists
