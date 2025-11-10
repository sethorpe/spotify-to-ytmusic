"""Unit tests for SpotifyService."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from spotipy.exceptions import SpotifyException
from spotify_to_ytmusic.services.spotify_service import SpotifyService
from spotify_to_ytmusic.models.track import Track, Playlist
from spotify_to_ytmusic.exceptions import (
    AuthenticationError,
    RateLimitError,
    NetworkError,
    APIError,
)


class TestSpotifyServiceInit:
    """Tests for SpotifyService initialization."""

    @patch("spotify_to_ytmusic.services.spotify_service.spotipy.Spotify")
    @patch("spotify_to_ytmusic.services.spotify_service.SpotifyOAuth")
    def test_initializes_with_credentials(self, mock_oauth, mock_spotify):
        """Should initialize with provided credentials."""
        service = SpotifyService(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8888/callback",
        )

        mock_oauth.assert_called_once_with(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8888/callback",
            scope="user-library-read playlist-read-private playlist-read-collaborative",
        )
        mock_spotify.assert_called_once()

    @patch("spotify_to_ytmusic.services.spotify_service.spotipy.Spotify")
    @patch("spotify_to_ytmusic.services.spotify_service.SpotifyOAuth")
    def test_raises_authentication_error_on_failure(self, mock_oauth, mock_spotify):
        """Should raise AuthenticationError if initialization fails."""
        mock_spotify.side_effect = Exception("Auth failed")

        with pytest.raises(AuthenticationError) as exc_info:
            SpotifyService("id", "secret", "redirect")

        assert "Spotify" in str(exc_info.value)
        assert "Auth failed" in str(exc_info.value)


class TestGetUserPlaylists:
    """Tests for get_user_playlists method."""

    @patch("spotify_to_ytmusic.services.spotify_service.spotipy.Spotify")
    @patch("spotify_to_ytmusic.services.spotify_service.SpotifyOAuth")
    def test_fetches_user_playlists(self, mock_oauth, mock_spotify):
        """Should fetch user playlists with pagination."""
        mock_sp_instance = Mock()
        mock_spotify.return_value = mock_sp_instance

        # Mock playlist list response
        mock_sp_instance.current_user_playlists.return_value = {
            "items": [{"id": "playlist1"}, {"id": "playlist2"}],
            "next": None,
        }

        # Mock playlist details
        mock_sp_instance.playlist.side_effect = [
            {
                "name": "Playlist 1",
                "description": "Description 1",
                "owner": {"display_name": "User"},
                "public": True,
            },
            {
                "name": "Playlist 2",
                "description": "Description 2",
                "owner": {"display_name": "User"},
                "public": False,
            },
        ]

        # Mock playlist tracks
        mock_sp_instance.playlist_tracks.side_effect = [
            {
                "items": [
                    {
                        "track": {
                            "name": "Track 1",
                            "artists": [{"name": "Artist 1"}],
                            "album": {"name": "Album 1"},
                            "duration_ms": 180000,
                            "id": "track1",
                            "external_ids": {"isrc": "USRC1234"},
                        }
                    }
                ],
                "next": None,
            },
            {"items": [], "next": None},
        ]

        service = SpotifyService("id", "secret", "redirect")
        playlists = service.get_user_playlists()

        assert len(playlists) == 2
        assert playlists[0].name == "Playlist 1"
        assert playlists[1].name == "Playlist 2"
        assert playlists[0].public is True
        assert playlists[1].public is False

    @patch("spotify_to_ytmusic.services.spotify_service.spotipy.Spotify")
    @patch("spotify_to_ytmusic.services.spotify_service.SpotifyOAuth")
    def test_handles_pagination(self, mock_oauth, mock_spotify):
        """Should handle pagination in playlist listing."""
        mock_sp_instance = Mock()
        mock_spotify.return_value = mock_sp_instance

        # First page
        first_page = {
            "items": [{"id": "playlist1"}],
            "next": "next_url",
        }

        # Second page
        second_page = {
            "items": [{"id": "playlist2"}],
            "next": None,
        }

        mock_sp_instance.current_user_playlists.return_value = first_page
        mock_sp_instance.next.return_value = second_page

        # Mock playlist details
        mock_sp_instance.playlist.side_effect = [
            {
                "name": "Playlist 1",
                "description": "",
                "owner": {"display_name": "User"},
                "public": True,
            },
            {
                "name": "Playlist 2",
                "description": "",
                "owner": {"display_name": "User"},
                "public": True,
            },
        ]

        # Mock empty tracks
        mock_sp_instance.playlist_tracks.return_value = {"items": [], "next": None}

        service = SpotifyService("id", "secret", "redirect")
        playlists = service.get_user_playlists()

        assert len(playlists) == 2
        mock_sp_instance.next.assert_called_once()

    @patch("spotify_to_ytmusic.services.spotify_service.spotipy.Spotify")
    @patch("spotify_to_ytmusic.services.spotify_service.SpotifyOAuth")
    def test_categorizes_spotify_exception(self, mock_oauth, mock_spotify):
        """Should categorize SpotifyException correctly and trigger retries."""
        mock_sp_instance = Mock()
        mock_spotify.return_value = mock_sp_instance
        mock_sp_instance.current_user_playlists.side_effect = SpotifyException(
            429, -1, "rate limit"
        )

        service = SpotifyService("id", "secret", "redirect")

        # The retry decorator will retry 3 times before raising MaxRetriesExceededError
        from spotify_to_ytmusic.exceptions import MaxRetriesExceededError

        with pytest.raises(MaxRetriesExceededError):
            service.get_user_playlists()

        # Verify it was called 3 times (max_attempts)
        assert mock_sp_instance.current_user_playlists.call_count == 3


class TestGetUserPlaylistsSummary:
    """Tests for get_user_playlists_summary method."""

    @patch("spotify_to_ytmusic.services.spotify_service.spotipy.Spotify")
    @patch("spotify_to_ytmusic.services.spotify_service.SpotifyOAuth")
    def test_fetches_summary_without_tracks(self, mock_oauth, mock_spotify):
        """Should fetch basic playlist info without loading tracks."""
        mock_sp_instance = Mock()
        mock_spotify.return_value = mock_sp_instance

        mock_sp_instance.current_user_playlists.return_value = {
            "items": [
                {
                    "name": "Playlist 1",
                    "tracks": {"total": 10},
                    "owner": {"display_name": "User"},
                    "public": True,
                    "id": "playlist1",
                },
                {
                    "name": "Playlist 2",
                    "tracks": {"total": 5},
                    "owner": {"display_name": "User"},
                    "public": False,
                    "id": "playlist2",
                },
            ],
            "next": None,
        }

        service = SpotifyService("id", "secret", "redirect")
        playlists = service.get_user_playlists_summary()

        assert len(playlists) == 2
        assert playlists[0]["name"] == "Playlist 1"
        assert playlists[0]["track_count"] == 10
        assert playlists[1]["name"] == "Playlist 2"
        assert playlists[1]["track_count"] == 5

        # Should not call playlist_tracks
        mock_sp_instance.playlist_tracks.assert_not_called()


class TestGetPlaylistByName:
    """Tests for get_playlist_by_name method."""

    @patch("spotify_to_ytmusic.services.spotify_service.spotipy.Spotify")
    @patch("spotify_to_ytmusic.services.spotify_service.SpotifyOAuth")
    def test_finds_playlist_by_name(self, mock_oauth, mock_spotify):
        """Should find playlist by name (case insensitive)."""
        mock_sp_instance = Mock()
        mock_spotify.return_value = mock_sp_instance

        mock_sp_instance.current_user_playlists.return_value = {
            "items": [{"id": "playlist1"}],
            "next": None,
        }

        mock_sp_instance.playlist.return_value = {
            "name": "My Playlist",
            "description": "Description",
            "owner": {"display_name": "User"},
            "public": True,
        }

        mock_sp_instance.playlist_tracks.return_value = {"items": [], "next": None}

        service = SpotifyService("id", "secret", "redirect")
        playlist = service.get_playlist_by_name("my playlist")

        assert playlist is not None
        assert playlist.name == "My Playlist"

    @patch("spotify_to_ytmusic.services.spotify_service.spotipy.Spotify")
    @patch("spotify_to_ytmusic.services.spotify_service.SpotifyOAuth")
    def test_returns_none_if_not_found(self, mock_oauth, mock_spotify):
        """Should return None if playlist not found."""
        mock_sp_instance = Mock()
        mock_spotify.return_value = mock_sp_instance

        mock_sp_instance.current_user_playlists.return_value = {
            "items": [{"id": "playlist1"}],
            "next": None,
        }

        mock_sp_instance.playlist.return_value = {
            "name": "Other Playlist",
            "description": "",
            "owner": {"display_name": "User"},
            "public": True,
        }

        mock_sp_instance.playlist_tracks.return_value = {"items": [], "next": None}

        service = SpotifyService("id", "secret", "redirect")
        playlist = service.get_playlist_by_name("Nonexistent Playlist")

        assert playlist is None


class TestParseTrack:
    """Tests for _parse_track method."""

    @patch("spotify_to_ytmusic.services.spotify_service.spotipy.Spotify")
    @patch("spotify_to_ytmusic.services.spotify_service.SpotifyOAuth")
    def test_parses_track_data(self, mock_oauth, mock_spotify):
        """Should parse track data correctly."""
        mock_spotify.return_value = Mock()

        service = SpotifyService("id", "secret", "redirect")

        track_data = {
            "name": "Track Name",
            "artists": [{"name": "Artist 1"}, {"name": "Artist 2"}],
            "album": {"name": "Album Name"},
            "duration_ms": 180000,
            "id": "track123",
            "external_ids": {"isrc": "USRC1234"},
        }

        track = service._parse_track(track_data)

        assert track.name == "Track Name"
        assert track.artists == ["Artist 1", "Artist 2"]
        assert track.album == "Album Name"
        assert track.duration_ms == 180000
        assert track.spotify_id == "track123"
        assert track.isrc == "USRC1234"

    @patch("spotify_to_ytmusic.services.spotify_service.spotipy.Spotify")
    @patch("spotify_to_ytmusic.services.spotify_service.SpotifyOAuth")
    def test_handles_missing_isrc(self, mock_oauth, mock_spotify):
        """Should handle missing ISRC code."""
        mock_spotify.return_value = Mock()

        service = SpotifyService("id", "secret", "redirect")

        track_data = {
            "name": "Track Name",
            "artists": [{"name": "Artist 1"}],
            "album": {"name": "Album Name"},
            "duration_ms": 180000,
            "id": "track123",
            "external_ids": {},
        }

        track = service._parse_track(track_data)

        assert track.isrc is None


class TestGetUserInfo:
    """Tests for get_user_info method."""

    @patch("spotify_to_ytmusic.services.spotify_service.spotipy.Spotify")
    @patch("spotify_to_ytmusic.services.spotify_service.SpotifyOAuth")
    def test_returns_user_info(self, mock_oauth, mock_spotify):
        """Should return user info from Spotify."""
        mock_sp_instance = Mock()
        mock_spotify.return_value = mock_sp_instance

        mock_sp_instance.current_user.return_value = {
            "display_name": "Test User",
            "id": "user123",
            "email": "test@example.com",
        }

        service = SpotifyService("id", "secret", "redirect")
        user_info = service.get_user_info()

        assert user_info["display_name"] == "Test User"
        assert user_info["id"] == "user123"
