"""Export migration reports to various formats (CSV, JSON)."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..models.track import MigrationResult, Track


class ReportExporter:
    """Handles exporting migration results to different file formats."""

    @staticmethod
    def export_to_json(
        results: List[MigrationResult],
        output_path: Path,
        include_metadata: bool = True,
    ) -> None:
        """Export migration results to JSON format.

        Args:
            results: List of migration results to export
            output_path: Path where the JSON file should be saved
            include_metadata: Include timestamp and summary metadata
        """
        data: Dict[str, Any] = {}

        if include_metadata:
            data["metadata"] = {
                "export_timestamp": datetime.now().isoformat(),
                "total_playlists": len(results),
                "total_tracks": sum(r.total_tracks for r in results),
                "successful_tracks": sum(r.successful_tracks for r in results),
                "failed_tracks": sum(len(r.failed_tracks) for r in results),
                "skipped_tracks": sum(len(r.skipped_tracks) for r in results),
            }

            if data["metadata"]["total_tracks"] > 0:
                data["metadata"]["overall_success_rate"] = (
                    data["metadata"]["successful_tracks"]
                    / data["metadata"]["total_tracks"]
                ) * 100

        data["migrations"] = [
            ReportExporter._migration_result_to_dict(result) for result in results
        ]

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def export_to_csv(
        results: List[MigrationResult],
        output_path: Path,
        include_track_details: bool = True,
    ) -> None:
        """Export migration results to CSV format.

        Args:
            results: List of migration results to export
            output_path: Path where the CSV file should be saved
            include_track_details: Include detailed track-level information
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if include_track_details:
            ReportExporter._export_detailed_csv(results, output_path)
        else:
            ReportExporter._export_summary_csv(results, output_path)

    @staticmethod
    def export_failed_tracks(
        results: List[MigrationResult],
        output_path: Path,
        format: str = "json",
    ) -> None:
        """Export only failed tracks for manual review.

        Args:
            results: List of migration results to extract failed tracks from
            output_path: Path where the file should be saved
            format: Output format ('json' or 'csv')
        """
        failed_data = []

        for result in results:
            for track in result.failed_tracks:
                failed_data.append(
                    {
                        "playlist": result.source_name,
                        "track_name": track.name,
                        "artists": ", ".join(track.artists),
                        "album": track.album,
                        "isrc": track.isrc or "N/A",
                        "spotify_id": track.spotify_id or "N/A",
                    }
                )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format.lower() == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "export_timestamp": datetime.now().isoformat(),
                        "total_failed_tracks": len(failed_data),
                        "failed_tracks": failed_data,
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
        elif format.lower() == "csv":
            if failed_data:
                with open(output_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=failed_data[0].keys())
                    writer.writeheader()
                    writer.writerows(failed_data)

    @staticmethod
    def _migration_result_to_dict(result: MigrationResult) -> Dict[str, Any]:
        """Convert a MigrationResult to a dictionary for JSON export."""
        return {
            "source_playlist": result.source_name,
            "destination_playlist": result.destination_name,
            "total_tracks": result.total_tracks,
            "successful_tracks": result.successful_tracks,
            "failed_tracks_count": len(result.failed_tracks),
            "skipped_tracks_count": len(result.skipped_tracks),
            "success_rate": round(result.success_rate, 2),
            "failed_tracks": [
                ReportExporter._track_to_dict(track) for track in result.failed_tracks
            ],
            "skipped_tracks": [
                ReportExporter._track_to_dict(track) for track in result.skipped_tracks
            ],
        }

    @staticmethod
    def _track_to_dict(track: Track) -> Dict[str, Any]:
        """Convert a Track to a dictionary."""
        return {
            "name": track.name,
            "artists": track.artists,
            "album": track.album,
            "duration_ms": track.duration_ms,
            "isrc": track.isrc,
            "spotify_id": track.spotify_id,
            "youtube_id": track.youtube_id,
        }

    @staticmethod
    def _export_summary_csv(results: List[MigrationResult], output_path: Path) -> None:
        """Export a summary CSV with one row per playlist."""
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "source_playlist",
                "destination_playlist",
                "total_tracks",
                "successful_tracks",
                "failed_tracks",
                "skipped_tracks",
                "success_rate",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                writer.writerow(
                    {
                        "source_playlist": result.source_name,
                        "destination_playlist": result.destination_name,
                        "total_tracks": result.total_tracks,
                        "successful_tracks": result.successful_tracks,
                        "failed_tracks": len(result.failed_tracks),
                        "skipped_tracks": len(result.skipped_tracks),
                        "success_rate": f"{result.success_rate:.2f}%",
                    }
                )

    @staticmethod
    def _export_detailed_csv(results: List[MigrationResult], output_path: Path) -> None:
        """Export a detailed CSV with one row per track."""
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
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
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                # Write failed tracks
                for track in result.failed_tracks:
                    writer.writerow(
                        {
                            "playlist": result.source_name,
                            "track_name": track.name,
                            "artists": ", ".join(track.artists),
                            "album": track.album,
                            "duration_ms": track.duration_ms,
                            "isrc": track.isrc or "N/A",
                            "status": "failed",
                            "spotify_id": track.spotify_id or "N/A",
                            "youtube_id": track.youtube_id or "N/A",
                        }
                    )

                # Write skipped tracks
                for track in result.skipped_tracks:
                    writer.writerow(
                        {
                            "playlist": result.source_name,
                            "track_name": track.name,
                            "artists": ", ".join(track.artists),
                            "album": track.album,
                            "duration_ms": track.duration_ms,
                            "isrc": track.isrc or "N/A",
                            "status": "skipped",
                            "spotify_id": track.spotify_id or "N/A",
                            "youtube_id": track.youtube_id or "N/A",
                        }
                    )


def generate_default_filename(prefix: str, extension: str) -> str:
    """Generate a default filename with timestamp.

    Args:
        prefix: Prefix for the filename (e.g., 'migration_report')
        extension: File extension (e.g., 'json', 'csv')

    Returns:
        Filename with timestamp (e.g., 'migration_report_20250125_143022.json')
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"
