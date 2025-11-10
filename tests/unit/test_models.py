"""Unit tests for data models."""

import pytest
from spotify_to_ytmusic.models.track import Track, Playlist, Album, MigrationResult


class TestTrack:
    """Tests for the Track model."""

    def test_track_creation(self):
        """Track should be created with required fields."""
        track = Track(
            name="Song Title",
            artists=["Artist 1", "Artist 2"],
            album="Album Name",
            duration_ms=180000,
        )
        assert track.name == "Song Title"
        assert track.artists == ["Artist 1", "Artist 2"]
        assert track.album == "Album Name"
        assert track.duration_ms == 180000

    def test_track_optional_fields(self):
        """Track should support optional fields."""
        track = Track(
            name="Song Title",
            artists=["Artist 1"],
            album="Album Name",
            duration_ms=180000,
            isrc="USRC12345678",
            spotify_id="spotify123",
            youtube_id="youtube123",
        )
        assert track.isrc == "USRC12345678"
        assert track.spotify_id == "spotify123"
        assert track.youtube_id == "youtube123"

    def test_track_default_optional_fields(self):
        """Track optional fields should default to None."""
        track = Track(
            name="Song Title",
            artists=["Artist 1"],
            album="Album Name",
            duration_ms=180000,
        )
        assert track.isrc is None
        assert track.spotify_id is None
        assert track.youtube_id is None

    def test_track_str_representation(self):
        """Track __str__ should format correctly."""
        track = Track(
            name="Song Title",
            artists=["Artist 1", "Artist 2"],
            album="Album Name",
            duration_ms=180000,
        )
        assert str(track) == "Song Title - Artist 1, Artist 2"

    def test_track_str_single_artist(self):
        """Track __str__ should work with single artist."""
        track = Track(
            name="Song Title",
            artists=["Artist 1"],
            album="Album Name",
            duration_ms=180000,
        )
        assert str(track) == "Song Title - Artist 1"

    def test_track_search_query(self):
        """Track search_query should format correctly."""
        track = Track(
            name="Song Title",
            artists=["Artist 1", "Artist 2"],
            album="Album Name",
            duration_ms=180000,
        )
        assert track.search_query == "Song Title Artist 1, Artist 2"


class TestPlaylist:
    """Tests for the Playlist model."""

    def test_playlist_creation(self):
        """Playlist should be created with required fields."""
        tracks = [
            Track("Song 1", ["Artist 1"], "Album 1", 180000),
            Track("Song 2", ["Artist 2"], "Album 2", 200000),
        ]
        playlist = Playlist(
            name="My Playlist",
            description="A great playlist",
            tracks=tracks,
        )
        assert playlist.name == "My Playlist"
        assert playlist.description == "A great playlist"
        assert len(playlist.tracks) == 2

    def test_playlist_optional_fields(self):
        """Playlist should support optional fields."""
        tracks = []
        playlist = Playlist(
            name="My Playlist",
            description="A great playlist",
            tracks=tracks,
            spotify_id="spotify123",
            youtube_id="youtube123",
            owner="User Name",
            public=False,
        )
        assert playlist.spotify_id == "spotify123"
        assert playlist.youtube_id == "youtube123"
        assert playlist.owner == "User Name"
        assert playlist.public is False

    def test_playlist_default_public(self):
        """Playlist public field should default to True."""
        playlist = Playlist(
            name="My Playlist",
            description="Description",
            tracks=[],
        )
        assert playlist.public is True

    def test_playlist_str_representation(self):
        """Playlist __str__ should format correctly."""
        tracks = [
            Track("Song 1", ["Artist 1"], "Album 1", 180000),
            Track("Song 2", ["Artist 2"], "Album 2", 200000),
        ]
        playlist = Playlist(
            name="My Playlist",
            description="Description",
            tracks=tracks,
        )
        assert str(playlist) == "My Playlist (2 tracks)"

    def test_playlist_total_duration(self):
        """Playlist total_duration_ms should calculate correctly."""
        tracks = [
            Track("Song 1", ["Artist 1"], "Album 1", 180000),
            Track("Song 2", ["Artist 2"], "Album 2", 200000),
            Track("Song 3", ["Artist 3"], "Album 3", 220000),
        ]
        playlist = Playlist(
            name="My Playlist",
            description="Description",
            tracks=tracks,
        )
        assert playlist.total_duration_ms == 600000

    def test_playlist_empty_total_duration(self):
        """Playlist with no tracks should have 0 total duration."""
        playlist = Playlist(
            name="Empty Playlist",
            description="No tracks",
            tracks=[],
        )
        assert playlist.total_duration_ms == 0


class TestAlbum:
    """Tests for the Album model."""

    def test_album_creation(self):
        """Album should be created with required fields."""
        tracks = [
            Track("Song 1", ["Artist 1"], "Album Name", 180000),
            Track("Song 2", ["Artist 1"], "Album Name", 200000),
        ]
        album = Album(
            name="Album Name",
            artists=["Artist 1"],
            tracks=tracks,
        )
        assert album.name == "Album Name"
        assert album.artists == ["Artist 1"]
        assert len(album.tracks) == 2

    def test_album_optional_fields(self):
        """Album should support optional fields."""
        tracks = []
        album = Album(
            name="Album Name",
            artists=["Artist 1"],
            tracks=tracks,
            release_date="2023-01-01",
            spotify_id="spotify123",
            youtube_id="youtube123",
        )
        assert album.release_date == "2023-01-01"
        assert album.spotify_id == "spotify123"
        assert album.youtube_id == "youtube123"

    def test_album_str_representation(self):
        """Album __str__ should format correctly."""
        tracks = [
            Track("Song 1", ["Artist 1"], "Album Name", 180000),
            Track("Song 2", ["Artist 1"], "Album Name", 200000),
        ]
        album = Album(
            name="Album Name",
            artists=["Artist 1", "Artist 2"],
            tracks=tracks,
        )
        assert str(album) == "Album Name by Artist 1, Artist 2 (2 tracks)"


class TestMigrationResult:
    """Tests for the MigrationResult model."""

    def test_migration_result_creation(self):
        """MigrationResult should be created with required fields."""
        failed_tracks = [Track("Failed Song", ["Artist 1"], "Album 1", 180000)]
        skipped_tracks = [Track("Skipped Song", ["Artist 2"], "Album 2", 200000)]

        result = MigrationResult(
            source_name="Spotify Playlist",
            destination_name="YouTube Music Playlist",
            total_tracks=10,
            successful_tracks=8,
            failed_tracks=failed_tracks,
            skipped_tracks=skipped_tracks,
        )

        assert result.source_name == "Spotify Playlist"
        assert result.destination_name == "YouTube Music Playlist"
        assert result.total_tracks == 10
        assert result.successful_tracks == 8
        assert len(result.failed_tracks) == 1
        assert len(result.skipped_tracks) == 1

    def test_migration_result_success_rate(self):
        """MigrationResult should calculate success rate correctly."""
        result = MigrationResult(
            source_name="Playlist",
            destination_name="Playlist",
            total_tracks=10,
            successful_tracks=8,
            failed_tracks=[],
            skipped_tracks=[],
        )
        assert result.success_rate == 80.0

    def test_migration_result_success_rate_perfect(self):
        """MigrationResult should handle 100% success rate."""
        result = MigrationResult(
            source_name="Playlist",
            destination_name="Playlist",
            total_tracks=10,
            successful_tracks=10,
            failed_tracks=[],
            skipped_tracks=[],
        )
        assert result.success_rate == 100.0

    def test_migration_result_success_rate_zero(self):
        """MigrationResult should handle 0% success rate."""
        result = MigrationResult(
            source_name="Playlist",
            destination_name="Playlist",
            total_tracks=10,
            successful_tracks=0,
            failed_tracks=[],
            skipped_tracks=[],
        )
        assert result.success_rate == 0.0

    def test_migration_result_success_rate_empty(self):
        """MigrationResult should handle empty playlist."""
        result = MigrationResult(
            source_name="Playlist",
            destination_name="Playlist",
            total_tracks=0,
            successful_tracks=0,
            failed_tracks=[],
            skipped_tracks=[],
        )
        assert result.success_rate == 0.0

    def test_migration_result_str_representation(self):
        """MigrationResult __str__ should format correctly."""
        result = MigrationResult(
            source_name="Spotify Playlist",
            destination_name="YouTube Music Playlist",
            total_tracks=10,
            successful_tracks=8,
            failed_tracks=[Track("Failed", ["Artist"], "Album", 180000)],
            skipped_tracks=[Track("Skipped", ["Artist"], "Album", 200000)],
        )

        expected = (
            "Migration of 'Spotify Playlist' to 'YouTube Music Playlist':\n"
            "  Total: 10\n"
            "  Successful: 8\n"
            "  Failed: 1\n"
            "  Skipped: 1\n"
            "  Success Rate: 80.0%"
        )
        assert str(result) == expected
