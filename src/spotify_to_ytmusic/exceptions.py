"""Custom exceptions for the Spotify to YouTube Music migrator."""

from typing import List, Optional


class SpotifyToYTMusicError(Exception):
    """Base exception for all application errors."""


class ConfigurationError(SpotifyToYTMusicError):
    """Raised when configuration is missing or invalid."""


class AuthenticationError(SpotifyToYTMusicError):
    """Raised when authentication fails."""

    def __init__(self, service: str, message: Optional[str] = None) -> None:
        self.service = service
        if message is None:
            message = f"Authentication failed for {service}"
        super().__init__(message)


class RateLimitError(SpotifyToYTMusicError):
    """Raised when API rate limit is exceeded."""

    def __init__(self, service: str, retry_after: Optional[int] = None) -> None:
        self.service = service
        self.retry_after = retry_after
        message = f"Rate limit exceeded for {service}"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message)


class NetworkError(SpotifyToYTMusicError):
    """Raised when network-related errors occur."""


class TrackNotFoundError(SpotifyToYTMusicError):
    """Raised when a track cannot be found on YouTube Music."""

    def __init__(self, track_name: str, artists: List[str]) -> None:
        self.track_name = track_name
        self.artists = artists
        super().__init__(f"Track not found: {track_name} by {', '.join(artists)}")


class PlaylistNotFoundError(SpotifyToYTMusicError):
    """Raised when a playlist cannot be found."""

    def __init__(self, playlist_name: str) -> None:
        self.playlist_name = playlist_name
        super().__init__(f"Playlist not found: {playlist_name}")


class APIError(SpotifyToYTMusicError):
    """Raised when an API call fails."""

    def __init__(
        self, service: str, message: str, status_code: Optional[int] = None
    ) -> None:
        self.service = service
        self.status_code = status_code
        super().__init__(f"{service} API error: {message}")


class MaxRetriesExceededError(SpotifyToYTMusicError):
    """Raised when maximum retry attempts are exhausted."""

    def __init__(self, operation: str, attempts: int) -> None:
        self.operation = operation
        self.attempts = attempts
        super().__init__(
            f"Maximum retry attempts ({attempts}) exceeded for operation: {operation}"
        )
