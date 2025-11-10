"""Unit tests for custom exceptions."""

import pytest
from spotify_to_ytmusic.exceptions import (
    SpotifyToYTMusicError,
    ConfigurationError,
    AuthenticationError,
    RateLimitError,
    NetworkError,
    TrackNotFoundError,
    PlaylistNotFoundError,
    APIError,
    MaxRetriesExceededError,
)


class TestSpotifyToYTMusicError:
    """Tests for the base exception class."""

    def test_base_exception_inherits_from_exception(self):
        """Base exception should inherit from Exception."""
        assert issubclass(SpotifyToYTMusicError, Exception)

    def test_base_exception_can_be_raised(self):
        """Base exception should be raiseable."""
        with pytest.raises(SpotifyToYTMusicError) as exc_info:
            raise SpotifyToYTMusicError("test error")
        assert str(exc_info.value) == "test error"


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_inherits_from_base(self):
        """ConfigurationError should inherit from base exception."""
        assert issubclass(ConfigurationError, SpotifyToYTMusicError)

    def test_can_be_raised_with_message(self):
        """ConfigurationError should be raiseable with a message."""
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError("Missing config file")
        assert str(exc_info.value) == "Missing config file"


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_inherits_from_base(self):
        """AuthenticationError should inherit from base exception."""
        assert issubclass(AuthenticationError, SpotifyToYTMusicError)

    def test_has_service_attribute(self):
        """AuthenticationError should have a service attribute."""
        error = AuthenticationError("Spotify")
        assert error.service == "Spotify"

    def test_default_message(self):
        """AuthenticationError should have a default message."""
        error = AuthenticationError("Spotify")
        assert str(error) == "Authentication failed for Spotify"

    def test_custom_message(self):
        """AuthenticationError should accept a custom message."""
        error = AuthenticationError("Spotify", "Invalid credentials")
        assert str(error) == "Invalid credentials"
        assert error.service == "Spotify"


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_inherits_from_base(self):
        """RateLimitError should inherit from base exception."""
        assert issubclass(RateLimitError, SpotifyToYTMusicError)

    def test_has_service_attribute(self):
        """RateLimitError should have a service attribute."""
        error = RateLimitError("Spotify")
        assert error.service == "Spotify"

    def test_has_retry_after_attribute(self):
        """RateLimitError should have a retry_after attribute."""
        error = RateLimitError("Spotify", 60)
        assert error.retry_after == 60

    def test_message_without_retry_after(self):
        """RateLimitError message without retry_after."""
        error = RateLimitError("Spotify")
        assert str(error) == "Rate limit exceeded for Spotify"

    def test_message_with_retry_after(self):
        """RateLimitError message with retry_after."""
        error = RateLimitError("Spotify", 120)
        assert str(error) == "Rate limit exceeded for Spotify. Retry after 120 seconds"


class TestNetworkError:
    """Tests for NetworkError."""

    def test_inherits_from_base(self):
        """NetworkError should inherit from base exception."""
        assert issubclass(NetworkError, SpotifyToYTMusicError)

    def test_can_be_raised_with_message(self):
        """NetworkError should be raiseable with a message."""
        with pytest.raises(NetworkError) as exc_info:
            raise NetworkError("Connection timeout")
        assert str(exc_info.value) == "Connection timeout"


class TestTrackNotFoundError:
    """Tests for TrackNotFoundError."""

    def test_inherits_from_base(self):
        """TrackNotFoundError should inherit from base exception."""
        assert issubclass(TrackNotFoundError, SpotifyToYTMusicError)

    def test_has_track_name_attribute(self):
        """TrackNotFoundError should have track_name attribute."""
        error = TrackNotFoundError("Song Title", ["Artist 1", "Artist 2"])
        assert error.track_name == "Song Title"

    def test_has_artists_attribute(self):
        """TrackNotFoundError should have artists attribute."""
        error = TrackNotFoundError("Song Title", ["Artist 1", "Artist 2"])
        assert error.artists == ["Artist 1", "Artist 2"]

    def test_message_formatting(self):
        """TrackNotFoundError should format message correctly."""
        error = TrackNotFoundError("Song Title", ["Artist 1", "Artist 2"])
        assert str(error) == "Track not found: Song Title by Artist 1, Artist 2"


class TestPlaylistNotFoundError:
    """Tests for PlaylistNotFoundError."""

    def test_inherits_from_base(self):
        """PlaylistNotFoundError should inherit from base exception."""
        assert issubclass(PlaylistNotFoundError, SpotifyToYTMusicError)

    def test_has_playlist_name_attribute(self):
        """PlaylistNotFoundError should have playlist_name attribute."""
        error = PlaylistNotFoundError("My Playlist")
        assert error.playlist_name == "My Playlist"

    def test_message_formatting(self):
        """PlaylistNotFoundError should format message correctly."""
        error = PlaylistNotFoundError("My Playlist")
        assert str(error) == "Playlist not found: My Playlist"


class TestAPIError:
    """Tests for APIError."""

    def test_inherits_from_base(self):
        """APIError should inherit from base exception."""
        assert issubclass(APIError, SpotifyToYTMusicError)

    def test_has_service_attribute(self):
        """APIError should have service attribute."""
        error = APIError("Spotify", "Server error")
        assert error.service == "Spotify"

    def test_has_status_code_attribute(self):
        """APIError should have status_code attribute."""
        error = APIError("Spotify", "Server error", 500)
        assert error.status_code == 500

    def test_status_code_optional(self):
        """APIError should work without status_code."""
        error = APIError("Spotify", "Server error")
        assert error.status_code is None

    def test_message_formatting(self):
        """APIError should format message correctly."""
        error = APIError("Spotify", "Server error", 500)
        assert str(error) == "Spotify API error: Server error"


class TestMaxRetriesExceededError:
    """Tests for MaxRetriesExceededError."""

    def test_inherits_from_base(self):
        """MaxRetriesExceededError should inherit from base exception."""
        assert issubclass(MaxRetriesExceededError, SpotifyToYTMusicError)

    def test_has_operation_attribute(self):
        """MaxRetriesExceededError should have operation attribute."""
        error = MaxRetriesExceededError("search_track", 3)
        assert error.operation == "search_track"

    def test_has_attempts_attribute(self):
        """MaxRetriesExceededError should have attempts attribute."""
        error = MaxRetriesExceededError("search_track", 3)
        assert error.attempts == 3

    def test_message_formatting(self):
        """MaxRetriesExceededError should format message correctly."""
        error = MaxRetriesExceededError("search_track", 3)
        assert (
            str(error)
            == "Maximum retry attempts (3) exceeded for operation: search_track"
        )
