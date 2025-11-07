"""Data models for tracks, playlists, and albums."""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Track:
    """Represents a music track."""

    name: str
    artists: List[str]
    album: str
    duration_ms: int
    isrc: Optional[str] = None  # International Standard Recording Code
    spotify_id: Optional[str] = None
    youtube_id: Optional[str] = None

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        artists_str = ", ".join(self.artists)
        return f"{self.name} - {artists_str}"

    @property
    def search_query(self) -> str:
        """Generate a search query for finding this track on other platforms."""
        artists_str = ", ".join(self.artists)
        return f"{self.name} {artists_str}"


@dataclass
class Playlist:
    """Represents a playlist."""

    name: str
    description: str
    tracks: List[Track]
    spotify_id: Optional[str] = None
    youtube_id: Optional[str] = None
    owner: Optional[str] = None
    public: bool = True

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"{self.name} ({len(self.tracks)} tracks)"

    @property
    def total_duration_ms(self) -> int:
        """Calculate total duration of all tracks in milliseconds."""
        return sum(track.duration_ms for track in self.tracks)


@dataclass
class Album:
    """Represents an album."""

    name: str
    artists: List[str]
    tracks: List[Track]
    release_date: Optional[str] = None
    spotify_id: Optional[str] = None
    youtube_id: Optional[str] = None

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        artists_str = ", ".join(self.artists)
        return f"{self.name} by {artists_str} ({len(self.tracks)} tracks)"


@dataclass
class MigrationResult:
    """Represents the result of a migration operation."""

    source_name: str
    destination_name: str
    total_tracks: int
    successful_tracks: int
    failed_tracks: List[Track]
    skipped_tracks: List[Track]

    @property
    def success_rate(self) -> float:
        """Calculate the success rate as a percentage."""
        if self.total_tracks == 0:
            return 0.0
        return (self.successful_tracks / self.total_tracks) * 100

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return (
            f"Migration of '{self.source_name}' to '{self.destination_name}':\n"
            f"  Total: {self.total_tracks}\n"
            f"  Successful: {self.successful_tracks}\n"
            f"  Failed: {len(self.failed_tracks)}\n"
            f"  Skipped: {len(self.skipped_tracks)}\n"
            f"  Success Rate: {self.success_rate:.1f}%"
        )
