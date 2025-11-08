"""Command-line interface for the Spotify to YouTube Music migrator."""

import os
import sys
import click
from dotenv import load_dotenv
from typing import Optional
from tqdm import tqdm

from .services.spotify_service import SpotifyService
from .services.ytmusic_service import YouTubeMusicService
from .models.track import MigrationResult


# Load environment variables
load_dotenv()


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
    except (FileNotFoundError, ValueError) as e:
        click.echo(f"Error: {str(e)}", err=True)
        click.echo("\nPlease run the setup command first:")
        click.echo("  poetry run spotify-to-ytmusic setup-ytmusic")
        sys.exit(1)


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
def list_playlists():
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
        for i, playlist in enumerate(playlists, 1):
            click.echo(f"{i}. {playlist['name']} ({playlist['track_count']} tracks)")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
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
@click.argument("playlist_name")
@click.option(
    "--public/--private",
    default=False,
    help="Make the YouTube Music playlist public or private (default: private)",
)
def migrate_playlist(playlist_name: str, public: bool):
    """Migrate a specific Spotify playlist to YouTube Music.

    PLAYLIST_NAME: The name of the playlist to migrate (case-insensitive)
    """
    click.echo(f"Starting migration for: {playlist_name}\n")

    # Initialize services
    spotify = get_spotify_service()
    ytmusic = get_ytmusic_service()

    try:
        # Find the playlist
        click.echo("Searching for playlist on Spotify...")
        playlist = spotify.get_playlist_by_name(playlist_name)

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

    except Exception as e:
        click.echo(f"\nError during migration: {str(e)}", err=True)
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
def migrate_all(public: bool, limit: Optional[int]):
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
        # Get all playlists
        playlists = spotify.get_user_playlists()

        if limit:
            playlists = playlists[:limit]

        click.echo(f"Found {len(playlists)} playlists to migrate\n")

        results = []

        # Migrate each playlist with progress bar
        with tqdm(total=len(playlists), desc="Overall progress", unit="playlist", position=0) as pbar:
            for playlist in playlists:
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
        click.echo(f"Total tracks processed: {total_tracks}")
        click.echo(f"Successful tracks: {successful_tracks}")
        click.echo(f"Failed tracks: {failed_tracks_count}")

        if total_tracks > 0:
            success_rate = (successful_tracks / total_tracks) * 100
            click.echo(f"Overall success rate: {success_rate:.1f}%")

    except Exception as e:
        click.echo(f"\nError during migration: {str(e)}", err=True)
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
