"""Unit tests for YouTubeMusicService."""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from spotify_to_ytmusic.services.ytmusic_service import YouTubeMusicService
from spotify_to_ytmusic.models.track import Track, Playlist, MigrationResult
from spotify_to_ytmusic.exceptions import (
    ConfigurationError,
    RateLimitError,
    NetworkError,
    APIError,
)


class TestYouTubeMusicServiceInit:
    """Tests for YouTubeMusicService initialization."""

    @patch("spotify_to_ytmusic.services.ytmusic_service.os.path.exists")
    @patch("spotify_to_ytmusic.services.ytmusic_service.YTMusic")
    def test_initializes_with_headers_file(self, mock_ytmusic, mock_exists):
        """Should initialize with existing headers file."""
        mock_exists.return_value = True

        service = YouTubeMusicService("headers_auth.json")

        mock_ytmusic.assert_called_once_with("headers_auth.json")
        assert service.ytmusic is not None

    @patch("spotify_to_ytmusic.services.ytmusic_service.os.path.exists")
    @patch("spotify_to_ytmusic.services.ytmusic_service.os.getenv")
    @patch("spotify_to_ytmusic.services.ytmusic_service.YTMusic")
    def test_uses_default_headers_file(self, mock_ytmusic, mock_getenv, mock_exists):
        """Should use default headers file if none provided."""
        mock_exists.return_value = True
        mock_getenv.return_value = "headers_auth.json"

        service = YouTubeMusicService()

        mock_ytmusic.assert_called_once_with("headers_auth.json")

    @patch("spotify_to_ytmusic.services.ytmusic_service.os.path.exists")
    def test_raises_config_error_if_file_not_found(self, mock_exists):
        """Should raise ConfigurationError if headers file doesn't exist."""
        mock_exists.return_value = False

        with pytest.raises(ConfigurationError) as exc_info:
            YouTubeMusicService("missing_file.json")

        assert "not found" in str(exc_info.value)
        assert "setup-ytmusic" in str(exc_info.value)

    @patch("spotify_to_ytmusic.services.ytmusic_service.os.path.exists")
    @patch("spotify_to_ytmusic.services.ytmusic_service.YTMusic")
    def test_raises_config_error_on_init_failure(self, mock_ytmusic, mock_exists):
        """Should raise ConfigurationError if YTMusic initialization fails."""
        mock_exists.return_value = True
        mock_ytmusic.side_effect = Exception("Invalid headers")

        with pytest.raises(ConfigurationError) as exc_info:
            YouTubeMusicService("headers_auth.json")

        assert "Failed to initialize" in str(exc_info.value)
        assert "corrupted or expired" in str(exc_info.value)


class TestSearchTrack:
    """Tests for search_track method."""

    @patch("spotify_to_ytmusic.services.ytmusic_service.os.path.exists")
    @patch("spotify_to_ytmusic.services.ytmusic_service.YTMusic")
    def test_searches_by_isrc_first(self, mock_ytmusic_class, mock_exists):
        """Should search by ISRC code first if available."""
        mock_exists.return_value = True
        mock_ytmusic_instance = Mock()
        mock_ytmusic_class.return_value = mock_ytmusic_instance

        # Mock ISRC search result
        mock_ytmusic_instance.search.return_value = [
            {
                "videoId": "video123",
                "title": "Song Title",
                "artists": [{"name": "Artist 1"}],
            }
        ]

        service = YouTubeMusicService()
        track = Track(
            name="Song Title",
            artists=["Artist 1"],
            album="Album",
            duration_ms=180000,
            isrc="USRC1234",
        )

        video_id = service.search_track(track)

        assert video_id == "video123"
        # First call should be ISRC search
        first_call = mock_ytmusic_instance.search.call_args_list[0]
        assert "USRC1234" in first_call[0]

    @patch("spotify_to_ytmusic.services.ytmusic_service.os.path.exists")
    @patch("spotify_to_ytmusic.services.ytmusic_service.YTMusic")
    def test_falls_back_to_name_search(self, mock_ytmusic_class, mock_exists):
        """Should fall back to name search if ISRC fails."""
        mock_exists.return_value = True
        mock_ytmusic_instance = Mock()
        mock_ytmusic_class.return_value = mock_ytmusic_instance

        # ISRC search returns empty, name search returns results
        mock_ytmusic_instance.search.side_effect = [
            [],  # ISRC search
            [
                {
                    "videoId": "video123",
                    "title": "Song Title",
                    "artists": [{"name": "Artist 1"}],
                }
            ],  # Name search
        ]

        service = YouTubeMusicService()
        track = Track(
            name="Song Title",
            artists=["Artist 1"],
            album="Album",
            duration_ms=180000,
            isrc="USRC1234",
        )

        video_id = service.search_track(track)

        assert video_id == "video123"
        assert mock_ytmusic_instance.search.call_count == 2

    @patch("spotify_to_ytmusic.services.ytmusic_service.os.path.exists")
    @patch("spotify_to_ytmusic.services.ytmusic_service.YTMusic")
    def test_validates_artist_match(self, mock_ytmusic_class, mock_exists):
        """Should validate that artist matches in ISRC results."""
        mock_exists.return_value = True
        mock_ytmusic_instance = Mock()
        mock_ytmusic_class.return_value = mock_ytmusic_instance

        # ISRC returns wrong artist, should fall back to name search
        mock_ytmusic_instance.search.side_effect = [
            [
                {
                    "videoId": "wrong_video",
                    "title": "Song Title",
                    "artists": [{"name": "Wrong Artist"}],
                }
            ],  # ISRC with wrong artist
            [
                {
                    "videoId": "correct_video",
                    "title": "Song Title",
                    "artists": [{"name": "Correct Artist"}],
                }
            ],  # Name search
        ]

        service = YouTubeMusicService()
        track = Track(
            name="Song Title",
            artists=["Correct Artist"],
            album="Album",
            duration_ms=180000,
            isrc="USRC1234",
        )

        video_id = service.search_track(track)

        assert video_id == "correct_video"

    @patch("spotify_to_ytmusic.services.ytmusic_service.os.path.exists")
    @patch("spotify_to_ytmusic.services.ytmusic_service.YTMusic")
    def test_returns_none_if_not_found(self, mock_ytmusic_class, mock_exists):
        """Should return None if track not found."""
        mock_exists.return_value = True
        mock_ytmusic_instance = Mock()
        mock_ytmusic_class.return_value = mock_ytmusic_instance

        mock_ytmusic_instance.search.return_value = []

        service = YouTubeMusicService()
        track = Track(
            name="Nonexistent Song",
            artists=["Unknown Artist"],
            album="Album",
            duration_ms=180000,
        )

        video_id = service.search_track(track)

        assert video_id is None


class TestCreatePlaylist:
    """Tests for create_playlist method."""

    @patch("spotify_to_ytmusic.services.ytmusic_service.os.path.exists")
    @patch("spotify_to_ytmusic.services.ytmusic_service.YTMusic")
    def test_creates_playlist(self, mock_ytmusic_class, mock_exists):
        """Should create a playlist on YouTube Music."""
        mock_exists.return_value = True
        mock_ytmusic_instance = Mock()
        mock_ytmusic_class.return_value = mock_ytmusic_instance

        mock_ytmusic_instance.create_playlist.return_value = "playlist123"

        service = YouTubeMusicService()
        playlist_id = service.create_playlist(
            name="My Playlist",
            description="Description",
            privacy="PRIVATE",
        )

        assert playlist_id == "playlist123"
        mock_ytmusic_instance.create_playlist.assert_called_once_with(
            title="My Playlist",
            description="Description",
            privacy_status="PRIVATE",
        )

    @patch("spotify_to_ytmusic.services.ytmusic_service.os.path.exists")
    @patch("spotify_to_ytmusic.services.ytmusic_service.YTMusic")
    def test_handles_create_playlist_error(self, mock_ytmusic_class, mock_exists):
        """Should categorize errors when creating playlist and trigger retries."""
        mock_exists.return_value = True
        mock_ytmusic_instance = Mock()
        mock_ytmusic_class.return_value = mock_ytmusic_instance

        mock_ytmusic_instance.create_playlist.side_effect = Exception("Server error")

        service = YouTubeMusicService()

        # The retry decorator will retry 3 times before raising MaxRetriesExceededError
        from spotify_to_ytmusic.exceptions import MaxRetriesExceededError

        with pytest.raises(MaxRetriesExceededError):
            service.create_playlist("My Playlist")

        # Verify it was called 3 times (max_attempts)
        assert mock_ytmusic_instance.create_playlist.call_count == 3


class TestAddTracksToPlaylist:
    """Tests for add_tracks_to_playlist method."""

    @patch("spotify_to_ytmusic.services.ytmusic_service.os.path.exists")
    @patch("spotify_to_ytmusic.services.ytmusic_service.YTMusic")
    def test_adds_tracks_to_playlist(self, mock_ytmusic_class, mock_exists):
        """Should add tracks to a playlist."""
        mock_exists.return_value = True
        mock_ytmusic_instance = Mock()
        mock_ytmusic_class.return_value = mock_ytmusic_instance

        mock_ytmusic_instance.add_playlist_items.return_value = {"status": "success"}

        service = YouTubeMusicService()
        response = service.add_tracks_to_playlist(
            "playlist123",
            ["video1", "video2", "video3"],
        )

        assert response == {"status": "success"}
        mock_ytmusic_instance.add_playlist_items.assert_called_once_with(
            "playlist123",
            ["video1", "video2", "video3"],
        )

    @patch("spotify_to_ytmusic.services.ytmusic_service.os.path.exists")
    @patch("spotify_to_ytmusic.services.ytmusic_service.YTMusic")
    def test_handles_empty_track_list(self, mock_ytmusic_class, mock_exists):
        """Should handle empty track list gracefully."""
        mock_exists.return_value = True
        mock_ytmusic_instance = Mock()
        mock_ytmusic_class.return_value = mock_ytmusic_instance

        service = YouTubeMusicService()
        response = service.add_tracks_to_playlist("playlist123", [])

        assert response == {"status": "No tracks to add"}
        mock_ytmusic_instance.add_playlist_items.assert_not_called()


class TestMigratePlaylist:
    """Tests for migrate_playlist method."""

    @patch("spotify_to_ytmusic.services.ytmusic_service.os.path.exists")
    @patch("spotify_to_ytmusic.services.ytmusic_service.YTMusic")
    def test_migrates_playlist_successfully(self, mock_ytmusic_class, mock_exists):
        """Should migrate a playlist from Spotify to YouTube Music."""
        mock_exists.return_value = True
        mock_ytmusic_instance = Mock()
        mock_ytmusic_class.return_value = mock_ytmusic_instance

        # Mock playlist creation
        mock_ytmusic_instance.create_playlist.return_value = "yt_playlist123"

        # Mock track searches (all successful)
        mock_ytmusic_instance.search.side_effect = [
            [
                {
                    "videoId": "video1",
                    "title": "Track 1",
                    "artists": [{"name": "Artist 1"}],
                }
            ],
            [
                {
                    "videoId": "video2",
                    "title": "Track 2",
                    "artists": [{"name": "Artist 2"}],
                }
            ],
        ]

        # Mock adding tracks
        mock_ytmusic_instance.add_playlist_items.return_value = {"status": "success"}

        service = YouTubeMusicService()

        tracks = [
            Track("Track 1", ["Artist 1"], "Album 1", 180000),
            Track("Track 2", ["Artist 2"], "Album 2", 200000),
        ]

        spotify_playlist = Playlist(
            name="My Playlist",
            description="Description",
            tracks=tracks,
            public=True,
        )

        result = service.migrate_playlist(spotify_playlist)

        assert result.total_tracks == 2
        assert result.successful_tracks == 2
        assert len(result.failed_tracks) == 0
        assert result.success_rate == 100.0

    @patch("spotify_to_ytmusic.services.ytmusic_service.os.path.exists")
    @patch("spotify_to_ytmusic.services.ytmusic_service.YTMusic")
    def test_handles_failed_track_searches(self, mock_ytmusic_class, mock_exists):
        """Should handle failed track searches gracefully."""
        mock_exists.return_value = True
        mock_ytmusic_instance = Mock()
        mock_ytmusic_class.return_value = mock_ytmusic_instance

        mock_ytmusic_instance.create_playlist.return_value = "yt_playlist123"

        # First track succeeds, second fails
        mock_ytmusic_instance.search.side_effect = [
            [
                {
                    "videoId": "video1",
                    "title": "Track 1",
                    "artists": [{"name": "Artist 1"}],
                }
            ],
            [],  # No results for second track
        ]

        mock_ytmusic_instance.add_playlist_items.return_value = {"status": "success"}

        service = YouTubeMusicService()

        tracks = [
            Track("Track 1", ["Artist 1"], "Album 1", 180000),
            Track("Track 2", ["Artist 2"], "Album 2", 200000),
        ]

        spotify_playlist = Playlist(
            name="My Playlist",
            description="Description",
            tracks=tracks,
            public=False,
        )

        result = service.migrate_playlist(spotify_playlist)

        assert result.total_tracks == 2
        assert result.successful_tracks == 1
        assert len(result.failed_tracks) == 1
        assert result.success_rate == 50.0

    @patch("spotify_to_ytmusic.services.ytmusic_service.os.path.exists")
    @patch("spotify_to_ytmusic.services.ytmusic_service.YTMusic")
    def test_respects_playlist_privacy(self, mock_ytmusic_class, mock_exists):
        """Should respect playlist privacy settings."""
        mock_exists.return_value = True
        mock_ytmusic_instance = Mock()
        mock_ytmusic_class.return_value = mock_ytmusic_instance

        mock_ytmusic_instance.create_playlist.return_value = "yt_playlist123"
        mock_ytmusic_instance.search.return_value = []

        service = YouTubeMusicService()

        # Test private playlist
        private_playlist = Playlist(
            name="Private Playlist",
            description="",
            tracks=[],
            public=False,
        )

        service.migrate_playlist(private_playlist)

        call_args = mock_ytmusic_instance.create_playlist.call_args
        assert call_args[1]["privacy_status"] == "PRIVATE"

        # Test public playlist
        public_playlist = Playlist(
            name="Public Playlist",
            description="",
            tracks=[],
            public=True,
        )

        service.migrate_playlist(public_playlist)

        call_args = mock_ytmusic_instance.create_playlist.call_args
        assert call_args[1]["privacy_status"] == "PUBLIC"


class TestGetUserPlaylists:
    """Tests for get_user_playlists method."""

    @patch("spotify_to_ytmusic.services.ytmusic_service.os.path.exists")
    @patch("spotify_to_ytmusic.services.ytmusic_service.YTMusic")
    def test_returns_user_playlists(self, mock_ytmusic_class, mock_exists):
        """Should return user's YouTube Music playlists."""
        mock_exists.return_value = True
        mock_ytmusic_instance = Mock()
        mock_ytmusic_class.return_value = mock_ytmusic_instance

        mock_ytmusic_instance.get_library_playlists.return_value = [
            {"title": "Playlist 1", "playlistId": "pl1"},
            {"title": "Playlist 2", "playlistId": "pl2"},
        ]

        service = YouTubeMusicService()
        playlists = service.get_user_playlists()

        assert len(playlists) == 2
        assert playlists[0]["title"] == "Playlist 1"
