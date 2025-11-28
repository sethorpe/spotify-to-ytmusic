"""Command-line interface for the Spotify to YouTube Music migrator."""

import os
import sys
import click
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional, List
from tqdm import tqdm

from .services.spotify_service import SpotifyService
from .services.ytmusic_service import YouTubeMusicService
from .models.track import MigrationResult
from .utils.report_exporter import ReportExporter, generate_default_filename
from .exceptions import (
    AuthenticationError,
    ConfigurationError,
    RateLimitError,
    NetworkError,
    PlaylistNotFoundError,
    DuplicatePlaylistError,
    APIError,
    MaxRetriesExceededError,
)
from .logging_config import setup_logging


# Load environment variables
load_dotenv()

# Setup logging
setup_logging()


def get_spotify_service() -> SpotifyService:
    """Initialize and return a Spotify service instance."""
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")

    if not client_id or not client_secret:
        click.echo("Error: Spotify credentials not found in .env file", err=True)
        click.echo("\nPlease create a .env file with your Spotify credentials:")
        click.echo("  SPOTIFY_CLIENT_ID=your_client_id")
        click.echo("  SPOTIFY_CLIENT_SECRET=your_client_secret")
        click.echo("\nGet credentials at: https://developer.spotify.com/dashboard")
        sys.exit(1)

    return SpotifyService(client_id, client_secret, redirect_uri)


def get_ytmusic_service() -> YouTubeMusicService:
    """Initialize and return a YouTube Music service instance."""
    try:
        return YouTubeMusicService()
    except ConfigurationError as e:
        click.echo(f"Configuration Error: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(
            f"Unexpected error initializing YouTube Music service: {str(e)}", err=True
        )
        sys.exit(1)


def export_reports(
    results: List[MigrationResult],
    export_json: Optional[str],
    export_csv: Optional[str],
    export_failed: Optional[str],
    csv_summary: bool,
) -> None:
    """Export migration results to specified file formats.

    Args:
        results: List of migration results to export
        export_json: Path for JSON export (None to skip)
        export_csv: Path for CSV export (None to skip)
        export_failed: Path for failed tracks export (None to skip)
        csv_summary: If True, export CSV summary instead of detailed CSV
    """
    if export_json:
        json_path = Path(export_json)
        ReportExporter.export_to_json(results, json_path)
        click.echo(f"\n✓ JSON report exported to: {json_path}")

    if export_csv:
        csv_path = Path(export_csv)
        ReportExporter.export_to_csv(
            results, csv_path, include_track_details=not csv_summary
        )
        report_type = "summary" if csv_summary else "detailed"
        click.echo(f"✓ CSV {report_type} report exported to: {csv_path}")

    if export_failed:
        failed_path = Path(export_failed)
        # Determine format from extension
        format_type = "json" if failed_path.suffix == ".json" else "csv"
        ReportExporter.export_failed_tracks(results, failed_path, format=format_type)
        click.echo(f"✓ Failed tracks exported to: {failed_path}")


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Spotify to YouTube Music Migration Tool

    Migrate your playlists and albums from Spotify to YouTube Music with ease.
    """
    pass


@cli.command()
def setup_ytmusic():
    """Set up YouTube Music authentication using browser headers.

    This will guide you through copying browser authentication headers.
    """
    headers_file = os.getenv("YTMUSIC_HEADERS_FILE", "headers_auth.json")

    if os.path.exists(headers_file):
        click.confirm(
            f"WARNING: Headers file already exists: {headers_file}\nOverwrite?",
            abort=True,
        )

    try:
        YouTubeMusicService.setup_browser_auth(headers_file)
        click.echo("YouTube Music authentication setup complete!")
    except Exception as e:
        click.echo(f"Error during setup: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--show-ids",
    is_flag=True,
    default=False,
    help="Show Spotify playlist IDs (useful for --playlist-id option)",
)
def list_playlists(show_ids: bool):
    """List all your Spotify playlists."""
    click.echo("Fetching your Spotify playlists...\n")

    spotify = get_spotify_service()

    try:
        user_info = spotify.get_user_info()
        click.echo(f"Logged in as: {user_info['display_name']}\n")

        playlists = spotify.get_user_playlists_summary()

        if not playlists:
            click.echo("No playlists found.")
            return

        click.echo(f"Found {len(playlists)} playlists:\n")

        if show_ids:
            # Display as table with IDs
            playlist_names = [p['name'] for p in playlists]
            duplicate_names = {name for name in playlist_names if playlist_names.count(name) > 1}

            # Print table header
            click.echo(f"{'#':<4} {'Name':<50} {'Tracks':<8} {'Playlist ID'}")
            click.echo("-" * 100)

            for i, playlist in enumerate(playlists, 1):
                name = playlist['name']
                track_count = playlist['track_count']
                playlist_id = playlist['id']

                # Truncate long names and mark duplicates
                display_name = name[:47] + "..." if len(name) > 50 else name
                if name in duplicate_names:
                    display_name += " *"

                click.echo(f"{i:<4} {display_name:<50} {track_count:<8} {playlist_id}")

            # Show legend if duplicates exist
            if duplicate_names:
                click.echo("\n* Indicates duplicate playlist names")
        else:
            # Simple list format without IDs
            for i, playlist in enumerate(playlists, 1):
                click.echo(f"{i}. {playlist['name']} ({playlist['track_count']} tracks)")

    except RateLimitError as e:
        click.echo(f"\nRate Limit Error: {str(e)}", err=True)
        click.echo("\nSuggestions:", err=True)
        click.echo("  - Wait a few minutes before trying again", err=True)
        sys.exit(1)
    except NetworkError as e:
        click.echo(f"\nNetwork Error: {str(e)}", err=True)
        click.echo("\nSuggestions:", err=True)
        click.echo("  - Check your internet connection", err=True)
        click.echo("  - Try again in a few moments", err=True)
        sys.exit(1)
    except (AuthenticationError, ConfigurationError, APIError) as e:
        click.echo(f"\nError: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"\nUnexpected Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
def list_albums():
    """List all your saved Spotify albums."""
    click.echo("Fetching your saved albums...\n")

    spotify = get_spotify_service()

    try:
        albums = spotify.get_saved_albums()

        if not albums:
            click.echo("No saved albums found.")
            return

        click.echo(f"Found {len(albums)} saved albums:\n")
        for i, album in enumerate(albums, 1):
            click.echo(f"{i}. {album}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("playlist_name", required=False)
@click.option(
    "--playlist-id",
    type=str,
    default=None,
    help="Spotify playlist ID (use this to migrate a specific playlist when duplicates exist)",
)
@click.option(
    "--public/--private",
    default=False,
    help="Make the YouTube Music playlist public or private (default: private)",
)
@click.option(
    "--export-json",
    type=click.Path(),
    default=None,
    help="Export migration report to JSON file",
)
@click.option(
    "--export-csv",
    type=click.Path(),
    default=None,
    help="Export migration report to CSV file",
)
@click.option(
    "--export-failed",
    type=click.Path(),
    default=None,
    help="Export failed tracks to a separate file (JSON or CSV based on extension)",
)
@click.option(
    "--csv-summary",
    is_flag=True,
    default=False,
    help="Export CSV as summary (playlist-level) instead of detailed (track-level)",
)
def migrate_playlist(
    playlist_name: Optional[str],
    playlist_id: Optional[str],
    public: bool,
    export_json: Optional[str],
    export_csv: Optional[str],
    export_failed: Optional[str],
    csv_summary: bool,
):
    """Migrate a specific Spotify playlist to YouTube Music.

    PLAYLIST_NAME: The name of the playlist to migrate (case-insensitive)

    Use --playlist-id when you have duplicate playlist names or want to migrate
    a specific playlist by its Spotify ID.
    """
    # Validate that at least one identifier is provided
    if not playlist_name and not playlist_id:
        click.echo("Error: You must provide either PLAYLIST_NAME or --playlist-id", err=True)
        click.echo("\nExamples:", err=True)
        click.echo("  spotify-to-ytmusic migrate-playlist \"My Playlist\"")
        click.echo("  spotify-to-ytmusic migrate-playlist --playlist-id 37i9dQZF1DXcBWIGoYBM5M")
        click.echo("\nTo get playlist IDs, run:", err=True)
        click.echo("  spotify-to-ytmusic list-playlists --show-ids")
        sys.exit(1)

    if playlist_name and playlist_id:
        click.echo("Warning: Both playlist name and ID provided. Using playlist ID.", err=True)

    # Initialize services
    spotify = get_spotify_service()
    ytmusic = get_ytmusic_service()

    try:
        # Find the playlist
        if playlist_id:
            click.echo(f"Fetching playlist by ID: {playlist_id}...")
            try:
                playlist = spotify.get_playlist_by_id(playlist_id)
                click.echo(f"Starting migration for: {playlist.name}\n")
            except Exception as e:
                click.echo(f"Error fetching playlist with ID '{playlist_id}': {str(e)}", err=True)
                click.echo("\nMake sure the playlist ID is correct.", err=True)
                click.echo("Run 'list-playlists --show-ids' to see available playlists and their IDs.")
                sys.exit(1)
        else:
            click.echo(f"Starting migration for: {playlist_name}\n")
            click.echo("Searching for playlist on Spotify...\n")
            try:
                playlist = spotify.get_playlist_by_name(playlist_name, show_progress=True)
                click.echo()  # Add blank line after progress bar
            except ValueError as e:
                click.echo(f"Error: {str(e)}", err=True)
                sys.exit(1)
            except DuplicatePlaylistError as e:
                # Display formatted table with duplicate playlist details
                click.echo(f"\nError: Found {len(e.playlists)} playlists with name '{e.playlist_name}'\n", err=True)

                # Print table header
                click.echo(f"{'#':<4} {'Playlist ID':<25} {'Owner':<20} {'Tracks':<8} {'Visibility'}", err=True)
                click.echo("-" * 80, err=True)

                for i, p in enumerate(e.playlists, 1):
                    visibility = "Public" if p['public'] else "Private"
                    click.echo(
                        f"{i:<4} {p['id']:<25} {p['owner']:<20} {p['tracks']:<8} {visibility}",
                        err=True
                    )

                click.echo("\nUse --playlist-id to specify which one to migrate:", err=True)
                click.echo(f"  spotify-to-ytmusic migrate-playlist --playlist-id <ID>", err=True)
                click.echo("\nExample:", err=True)
                click.echo(f"  spotify-to-ytmusic migrate-playlist --playlist-id {e.playlists[0]['id']}", err=True)
                sys.exit(1)

            if not playlist:
                click.echo(f"Playlist not found: {playlist_name}", err=True)
                click.echo("\nRun 'list-playlists' to see available playlists.")
                sys.exit(1)

        click.echo(f"Found: {playlist}\n")

        # Override public setting if specified
        playlist.public = public

        # Migrate the playlist
        result = ytmusic.migrate_playlist(playlist)

        # Display results
        click.echo("\n" + "=" * 60)
        click.echo("MIGRATION COMPLETE")
        click.echo("=" * 60)
        click.echo(str(result))

        if result.failed_tracks:
            click.echo("\nFailed tracks:")
            for track in result.failed_tracks:
                click.echo(f"  - {track}")

        # Export reports if requested
        export_reports(
            [result], export_json, export_csv, export_failed, csv_summary
        )

    except MaxRetriesExceededError as e:
        click.echo(f"\nMax Retries Exceeded: {str(e)}", err=True)
        click.echo("\nThe operation failed after multiple retry attempts.", err=True)
        click.echo("\nSuggestions:", err=True)
        click.echo("  - Check your internet connection", err=True)
        click.echo("  - Verify that the YouTube Music service is operational", err=True)
        click.echo("  - Try again later", err=True)
        sys.exit(1)
    except RateLimitError as e:
        click.echo(f"\nRate Limit Error: {str(e)}", err=True)
        click.echo("\nYou've hit API rate limits.", err=True)
        click.echo("\nSuggestions:", err=True)
        click.echo("  - Wait 10-15 minutes before trying again", err=True)
        click.echo("  - Reduce the number of playlists migrated at once", err=True)
        sys.exit(1)
    except NetworkError as e:
        click.echo(f"\nNetwork Error: {str(e)}", err=True)
        click.echo("\nSuggestions:", err=True)
        click.echo("  - Check your internet connection", err=True)
        click.echo("  - Try again in a few moments", err=True)
        sys.exit(1)
    except (AuthenticationError, ConfigurationError, APIError) as e:
        click.echo(f"\nError: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"\nUnexpected error during migration: {str(e)}", err=True)
        click.echo("\nPlease report this issue if it persists.", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--public/--private",
    default=False,
    help="Make the YouTube Music playlists public or private (default: private)",
)
@click.option(
    "--limit",
    type=int,
    default=None,
    help="Limit the number of playlists to migrate",
)
@click.option(
    "--export-json",
    type=click.Path(),
    default=None,
    help="Export migration report to JSON file",
)
@click.option(
    "--export-csv",
    type=click.Path(),
    default=None,
    help="Export migration report to CSV file",
)
@click.option(
    "--export-failed",
    type=click.Path(),
    default=None,
    help="Export failed tracks to a separate file (JSON or CSV based on extension)",
)
@click.option(
    "--csv-summary",
    is_flag=True,
    default=False,
    help="Export CSV as summary (playlist-level) instead of detailed (track-level)",
)
def migrate_all(
    public: bool,
    limit: Optional[int],
    export_json: Optional[str],
    export_csv: Optional[str],
    export_failed: Optional[str],
    csv_summary: bool,
):
    """Migrate all your Spotify playlists to YouTube Music.

    WARNING: This may take a long time depending on how many playlists you have.
    """
    click.echo("Starting migration of all playlists...\n")

    if not click.confirm("This will migrate ALL your playlists. Continue?"):
        click.echo("Migration cancelled.")
        return

    # Initialize services
    spotify = get_spotify_service()
    ytmusic = get_ytmusic_service()

    try:
        # Get all playlists with progress indicator
        click.echo("Fetching all playlists from Spotify...\n")
        playlists = spotify.get_user_playlists(show_progress=True)
        click.echo()  # Add blank line after progress bar

        if limit:
            playlists = playlists[:limit]

        # Detect duplicate playlist names before migration
        playlist_names = [p.name for p in playlists]
        duplicate_names = {name for name in playlist_names if playlist_names.count(name) > 1}

        # Filter out duplicates
        playlists_to_migrate = []
        skipped_duplicates = []

        for playlist in playlists:
            if playlist.name in duplicate_names:
                skipped_duplicates.append({
                    "name": playlist.name,
                    "id": playlist.spotify_id,
                    "owner": playlist.owner,
                    "tracks": len(playlist.tracks),
                })
            else:
                playlists_to_migrate.append(playlist)

        click.echo(f"Found {len(playlists)} playlists total")
        if skipped_duplicates:
            unique_skipped_names = {p["name"] for p in skipped_duplicates}
            click.echo(f"Skipping {len(skipped_duplicates)} playlists with duplicate names ({len(unique_skipped_names)} unique names)")
        click.echo(f"Migrating {len(playlists_to_migrate)} playlists\n")

        results = []

        # Migrate each playlist with progress bar
        with tqdm(
            total=len(playlists_to_migrate), desc="Overall progress", unit="playlist", position=0
        ) as pbar:
            for playlist in playlists_to_migrate:
                pbar.set_postfix_str(f"Migrating: {playlist.name[:40]}...")

                playlist.public = public
                result = ytmusic.migrate_playlist(playlist)
                results.append(result)

                pbar.update(1)

        # Summary
        click.echo("\n" + "=" * 60)
        click.echo("MIGRATION SUMMARY")
        click.echo("=" * 60)

        total_tracks = sum(r.total_tracks for r in results)
        successful_tracks = sum(r.successful_tracks for r in results)
        failed_tracks_count = sum(len(r.failed_tracks) for r in results)

        click.echo(f"Total playlists migrated: {len(results)}")
        if skipped_duplicates:
            unique_skipped_names = {p["name"] for p in skipped_duplicates}
            click.echo(f"Skipped playlists (duplicates): {len(skipped_duplicates)} ({len(unique_skipped_names)} unique names)")
        click.echo(f"Total tracks processed: {total_tracks}")
        click.echo(f"Successful tracks: {successful_tracks}")
        click.echo(f"Failed tracks: {failed_tracks_count}")

        if total_tracks > 0:
            success_rate = (successful_tracks / total_tracks) * 100
            click.echo(f"Overall success rate: {success_rate:.1f}%")

        # Show skipped playlists details if any
        if skipped_duplicates:
            click.echo("\n" + "=" * 60)
            click.echo("SKIPPED PLAYLISTS (DUPLICATE NAMES)")
            click.echo("=" * 60)
            for p in skipped_duplicates:
                click.echo(f"  - {p['name']} ({p['tracks']} tracks, owner: {p['owner']}, ID: {p['id']})")
            click.echo("\nTo migrate these, use --playlist-id:")
            click.echo("  spotify-to-ytmusic migrate-playlist --playlist-id <ID>")

        # Export reports if requested
        export_reports(results, export_json, export_csv, export_failed, csv_summary)

    except MaxRetriesExceededError as e:
        click.echo(f"\nMax Retries Exceeded: {str(e)}", err=True)
        click.echo("\nThe operation failed after multiple retry attempts.", err=True)
        click.echo("\nSuggestions:", err=True)
        click.echo("  - Check your internet connection", err=True)
        click.echo("  - Verify that the YouTube Music service is operational", err=True)
        click.echo("  - Try migrating playlists one at a time", err=True)
        sys.exit(1)
    except RateLimitError as e:
        click.echo(f"\nRate Limit Error: {str(e)}", err=True)
        click.echo(
            "\nYou've hit API rate limits while migrating multiple playlists.", err=True
        )
        click.echo("\nSuggestions:", err=True)
        click.echo("  - Wait 10-15 minutes before trying again", err=True)
        click.echo(
            "  - Use --limit option to migrate fewer playlists at once", err=True
        )
        click.echo("  - Migrate playlists one at a time instead", err=True)
        sys.exit(1)
    except NetworkError as e:
        click.echo(f"\nNetwork Error: {str(e)}", err=True)
        click.echo("\nSuggestions:", err=True)
        click.echo("  - Check your internet connection", err=True)
        click.echo("  - Try again in a few moments", err=True)
        sys.exit(1)
    except (AuthenticationError, ConfigurationError, APIError) as e:
        click.echo(f"\nError: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"\nUnexpected error during migration: {str(e)}", err=True)
        click.echo("\nPlease report this issue if it persists.", err=True)
        sys.exit(1)


@cli.command()
def info():
    """Display information about your Spotify and YouTube Music accounts."""
    click.echo("Account Information\n")

    # Spotify info
    try:
        spotify = get_spotify_service()
        user_info = spotify.get_user_info()

        click.echo("Spotify:")
        click.echo(f"  Name: {user_info['display_name']}")
        click.echo(f"  Email: {user_info.get('email', 'N/A')}")
        click.echo(f"  Country: {user_info.get('country', 'N/A')}")
        click.echo(f"  Followers: {user_info.get('followers', {}).get('total', 'N/A')}")
    except Exception as e:
        click.echo(f"Spotify: Error - {str(e)}")

    click.echo()

    # YouTube Music info
    try:
        ytmusic = get_ytmusic_service()
        playlists = ytmusic.get_user_playlists()

        click.echo("YouTube Music:")
        click.echo(f"  Playlists: {len(playlists)}")
        click.echo("  Status: Connected")
    except Exception as e:
        click.echo(f"YouTube Music: Error - {str(e)}")


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
