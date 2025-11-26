"""Unit tests for report exporter functionality."""

import json
import csv
import pytest
from pathlib import Path
from datetime import datetime

from spotify_to_ytmusic.utils.report_exporter import (
    ReportExporter,
    generate_default_filename,
)
from spotify_to_ytmusic.models.track import Track, MigrationResult


@pytest.fixture
def sample_tracks():
    """Create sample tracks for testing."""
    return [
        Track(
            name="Song 1",
            artists=["Artist 1"],
            album="Album 1",
            duration_ms=180000,
            isrc="USRC11700001",
            spotify_id="spotify123",
            youtube_id="youtube123",
        ),
        Track(
            name="Song 2",
            artists=["Artist 2", "Artist 3"],
            album="Album 2",
            duration_ms=200000,
            isrc="USRC11700002",
            spotify_id="spotify456",
            youtube_id=None,
        ),
        Track(
            name="Song 3",
            artists=["Artist 4"],
            album="Album 3",
            duration_ms=220000,
            isrc=None,
            spotify_id="spotify789",
            youtube_id=None,
        ),
    ]


@pytest.fixture
def sample_migration_result(sample_tracks):
    """Create a sample migration result."""
    return MigrationResult(
        source_name="Test Playlist",
        destination_name="Test Playlist (Migrated)",
        total_tracks=10,
        successful_tracks=7,
        failed_tracks=[sample_tracks[1]],
        skipped_tracks=[sample_tracks[2]],
    )


@pytest.fixture
def multiple_migration_results(sample_tracks):
    """Create multiple migration results for testing."""
    return [
        MigrationResult(
            source_name="Playlist 1",
            destination_name="Playlist 1 (Migrated)",
            total_tracks=10,
            successful_tracks=8,
            failed_tracks=[sample_tracks[0]],
            skipped_tracks=[sample_tracks[1]],
        ),
        MigrationResult(
            source_name="Playlist 2",
            destination_name="Playlist 2 (Migrated)",
            total_tracks=5,
            successful_tracks=3,
            failed_tracks=[sample_tracks[2]],
            skipped_tracks=[],
        ),
    ]


class TestGenerateDefaultFilename:
    """Test default filename generation."""

    def test_filename_format(self):
        """Test that filename has correct format."""
        filename = generate_default_filename("migration_report", "json")
        assert filename.startswith("migration_report_")
        assert filename.endswith(".json")

    def test_filename_has_timestamp(self):
        """Test that filename includes timestamp."""
        filename = generate_default_filename("test", "csv")
        # Extract timestamp part (between prefix_ and .extension)
        timestamp_part = filename[5:-4]  # Remove "test_" and ".csv"
        # Should be in format YYYYMMDD_HHMMSS
        assert len(timestamp_part) == 15  # 8 digits + _ + 6 digits
        assert timestamp_part[8] == "_"

    def test_different_extensions(self):
        """Test filename generation with different extensions."""
        json_file = generate_default_filename("report", "json")
        csv_file = generate_default_filename("report", "csv")
        assert json_file.endswith(".json")
        assert csv_file.endswith(".csv")


class TestExportToJSON:
    """Test JSON export functionality."""

    def test_export_single_result_with_metadata(
        self, sample_migration_result, tmp_path
    ):
        """Test exporting a single migration result to JSON with metadata."""
        output_file = tmp_path / "report.json"
        ReportExporter.export_to_json([sample_migration_result], output_file)

        assert output_file.exists()

        with open(output_file, "r") as f:
            data = json.load(f)

        # Check metadata
        assert "metadata" in data
        assert data["metadata"]["total_playlists"] == 1
        assert data["metadata"]["total_tracks"] == 10
        assert data["metadata"]["successful_tracks"] == 7
        assert data["metadata"]["failed_tracks"] == 1
        assert data["metadata"]["skipped_tracks"] == 1
        assert "overall_success_rate" in data["metadata"]
        assert data["metadata"]["overall_success_rate"] == 70.0

    def test_export_without_metadata(self, sample_migration_result, tmp_path):
        """Test exporting without metadata."""
        output_file = tmp_path / "report.json"
        ReportExporter.export_to_json(
            [sample_migration_result], output_file, include_metadata=False
        )

        with open(output_file, "r") as f:
            data = json.load(f)

        assert "metadata" not in data
        assert "migrations" in data

    def test_export_multiple_results(self, multiple_migration_results, tmp_path):
        """Test exporting multiple migration results."""
        output_file = tmp_path / "report.json"
        ReportExporter.export_to_json(multiple_migration_results, output_file)

        with open(output_file, "r") as f:
            data = json.load(f)

        assert len(data["migrations"]) == 2
        assert data["metadata"]["total_playlists"] == 2
        assert data["metadata"]["total_tracks"] == 15
        assert data["metadata"]["successful_tracks"] == 11

    def test_export_creates_parent_directories(self, sample_migration_result, tmp_path):
        """Test that export creates parent directories if they don't exist."""
        output_file = tmp_path / "subdir" / "nested" / "report.json"
        ReportExporter.export_to_json([sample_migration_result], output_file)

        assert output_file.exists()

    def test_migration_result_structure(self, sample_migration_result, tmp_path):
        """Test the structure of exported migration results."""
        output_file = tmp_path / "report.json"
        ReportExporter.export_to_json([sample_migration_result], output_file)

        with open(output_file, "r") as f:
            data = json.load(f)

        migration = data["migrations"][0]
        assert migration["source_playlist"] == "Test Playlist"
        assert migration["destination_playlist"] == "Test Playlist (Migrated)"
        assert migration["total_tracks"] == 10
        assert migration["successful_tracks"] == 7
        assert migration["failed_tracks_count"] == 1
        assert migration["skipped_tracks_count"] == 1
        assert "success_rate" in migration


class TestExportToCSV:
    """Test CSV export functionality."""

    def test_export_detailed_csv(self, multiple_migration_results, tmp_path):
        """Test exporting detailed CSV with track-level information."""
        output_file = tmp_path / "report.csv"
        ReportExporter.export_to_csv(
            multiple_migration_results, output_file, include_track_details=True
        )

        assert output_file.exists()

        with open(output_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should have rows for failed and skipped tracks
        assert len(rows) == 3  # 1 failed + 1 skipped from first, 1 failed from second
        assert all("playlist" in row for row in rows)
        assert all("track_name" in row for row in rows)
        assert all("status" in row for row in rows)

    def test_export_summary_csv(self, multiple_migration_results, tmp_path):
        """Test exporting summary CSV with playlist-level information."""
        output_file = tmp_path / "summary.csv"
        ReportExporter.export_to_csv(
            multiple_migration_results, output_file, include_track_details=False
        )

        assert output_file.exists()

        with open(output_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should have one row per playlist
        assert len(rows) == 2
        assert rows[0]["source_playlist"] == "Playlist 1"
        assert rows[1]["source_playlist"] == "Playlist 2"
        assert "success_rate" in rows[0]

    def test_csv_creates_parent_directories(self, sample_migration_result, tmp_path):
        """Test that CSV export creates parent directories."""
        output_file = tmp_path / "reports" / "export.csv"
        ReportExporter.export_to_csv([sample_migration_result], output_file)

        assert output_file.exists()

    def test_detailed_csv_columns(self, sample_migration_result, tmp_path):
        """Test that detailed CSV has all expected columns."""
        output_file = tmp_path / "detailed.csv"
        ReportExporter.export_to_csv(
            [sample_migration_result], output_file, include_track_details=True
        )

        with open(output_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames

        expected_fields = [
            "playlist",
            "track_name",
            "artists",
            "album",
            "duration_ms",
            "isrc",
            "status",
            "spotify_id",
            "youtube_id",
        ]
        assert all(field in fieldnames for field in expected_fields)

    def test_summary_csv_columns(self, sample_migration_result, tmp_path):
        """Test that summary CSV has all expected columns."""
        output_file = tmp_path / "summary.csv"
        ReportExporter.export_to_csv(
            [sample_migration_result], output_file, include_track_details=False
        )

        with open(output_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames

        expected_fields = [
            "source_playlist",
            "destination_playlist",
            "total_tracks",
            "successful_tracks",
            "failed_tracks",
            "skipped_tracks",
            "success_rate",
        ]
        assert all(field in fieldnames for field in expected_fields)


class TestExportFailedTracks:
    """Test failed tracks export functionality."""

    def test_export_failed_tracks_json(self, multiple_migration_results, tmp_path):
        """Test exporting failed tracks to JSON."""
        output_file = tmp_path / "failed.json"
        ReportExporter.export_failed_tracks(
            multiple_migration_results, output_file, format="json"
        )

        assert output_file.exists()

        with open(output_file, "r") as f:
            data = json.load(f)

        assert "failed_tracks" in data
        assert data["total_failed_tracks"] == 2
        assert len(data["failed_tracks"]) == 2

    def test_export_failed_tracks_csv(self, multiple_migration_results, tmp_path):
        """Test exporting failed tracks to CSV."""
        output_file = tmp_path / "failed.csv"
        ReportExporter.export_failed_tracks(
            multiple_migration_results, output_file, format="csv"
        )

        assert output_file.exists()

        with open(output_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2

    def test_failed_tracks_json_structure(self, sample_migration_result, tmp_path):
        """Test the structure of failed tracks JSON."""
        output_file = tmp_path / "failed.json"
        ReportExporter.export_failed_tracks(
            [sample_migration_result], output_file, format="json"
        )

        with open(output_file, "r") as f:
            data = json.load(f)

        failed_track = data["failed_tracks"][0]
        assert "playlist" in failed_track
        assert "track_name" in failed_track
        assert "artists" in failed_track
        assert "album" in failed_track
        assert "isrc" in failed_track

    def test_failed_tracks_csv_columns(self, sample_migration_result, tmp_path):
        """Test that failed tracks CSV has expected columns."""
        output_file = tmp_path / "failed.csv"
        ReportExporter.export_failed_tracks(
            [sample_migration_result], output_file, format="csv"
        )

        with open(output_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames

        expected_fields = [
            "playlist",
            "track_name",
            "artists",
            "album",
            "isrc",
            "spotify_id",
        ]
        assert all(field in fieldnames for field in expected_fields)

    def test_export_creates_parent_directories(self, sample_migration_result, tmp_path):
        """Test that export creates parent directories."""
        output_file = tmp_path / "deep" / "nested" / "failed.json"
        ReportExporter.export_failed_tracks([sample_migration_result], output_file)

        assert output_file.exists()

    def test_no_failed_tracks(self, tmp_path):
        """Test exporting when there are no failed tracks."""
        result = MigrationResult(
            source_name="Clean Playlist",
            destination_name="Clean Playlist (Migrated)",
            total_tracks=10,
            successful_tracks=10,
            failed_tracks=[],
            skipped_tracks=[],
        )

        output_file = tmp_path / "empty_failed.json"
        ReportExporter.export_failed_tracks([result], output_file, format="json")

        with open(output_file, "r") as f:
            data = json.load(f)

        assert data["total_failed_tracks"] == 0
        assert len(data["failed_tracks"]) == 0


class TestTrackToDict:
    """Test track to dictionary conversion."""

    def test_track_to_dict_complete(self, sample_tracks):
        """Test converting a complete track to dictionary."""
        track_dict = ReportExporter._track_to_dict(sample_tracks[0])

        assert track_dict["name"] == "Song 1"
        assert track_dict["artists"] == ["Artist 1"]
        assert track_dict["album"] == "Album 1"
        assert track_dict["duration_ms"] == 180000
        assert track_dict["isrc"] == "USRC11700001"
        assert track_dict["spotify_id"] == "spotify123"
        assert track_dict["youtube_id"] == "youtube123"

    def test_track_to_dict_with_none_values(self, sample_tracks):
        """Test converting track with None values."""
        track_dict = ReportExporter._track_to_dict(sample_tracks[2])

        assert track_dict["isrc"] is None
        assert track_dict["youtube_id"] is None


class TestMigrationResultToDict:
    """Test migration result to dictionary conversion."""

    def test_migration_result_to_dict(self, sample_migration_result):
        """Test converting migration result to dictionary."""
        result_dict = ReportExporter._migration_result_to_dict(sample_migration_result)

        assert result_dict["source_playlist"] == "Test Playlist"
        assert result_dict["destination_playlist"] == "Test Playlist (Migrated)"
        assert result_dict["total_tracks"] == 10
        assert result_dict["successful_tracks"] == 7
        assert result_dict["failed_tracks_count"] == 1
        assert result_dict["skipped_tracks_count"] == 1
        assert "success_rate" in result_dict
        assert result_dict["success_rate"] == 70.0
