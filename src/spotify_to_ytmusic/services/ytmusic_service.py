"""Service for interacting with YouTube Music API."""

import os
import logging
from typing import List, Optional, Dict, Any
from tqdm import tqdm
from ytmusicapi import YTMusic, setup
from ..models.track import Track, Playlist, MigrationResult
from ..exceptions import (
    AuthenticationError,
    ConfigurationError,
    RateLimitError,
    NetworkError,
    TrackNotFoundError,
    APIError,
)
from ..utils.retry import retry_with_backoff, categorize_api_error

logger = logging.getLogger(__name__)


class YouTubeMusicService:
    """Handles all interactions with the YouTube Music API."""

    def __init__(self, headers_file: Optional[str] = None):
        """Initialize the YouTube Music service.

        Args:
            headers_file: Path to the browser headers JSON file.
        """
        if headers_file is None:
            headers_file = os.getenv("YTMUSIC_HEADERS_FILE", "headers_auth.json")

        if not os.path.exists(headers_file):
            raise ConfigurationError(
                f"YouTube Music headers file not found: {headers_file}\n"
                "Please run: poetry run spotify-to-ytmusic setup-ytmusic"
            )

        try:
            self.ytmusic = YTMusic(headers_file)
        except Exception as e:
            raise ConfigurationError(
                f"Failed to initialize YouTube Music client: {str(e)}\n"
                "Your headers file may be corrupted or expired.\n"
                "Please run: poetry run spotify-to-ytmusic setup-ytmusic"
            )

    @staticmethod
    def setup_browser_auth(filepath: str = "headers_auth.json") -> None:
        """Run the browser authentication setup for YouTube Music.

        Args:
            filepath: Where to save the browser headers
        """
        import subprocess

        print("\n=== YouTube Music Browser Authentication Setup ===")
        print("Running ytmusicapi's built-in setup tool...\n")

        try:
            # Use ytmusicapi's CLI tool which handles the setup interactively
            subprocess.run(["ytmusicapi", "browser", "--file", filepath], check=True)
            print(f"\nAuthentication successful! Headers saved to: {filepath}")
            print("Note: These credentials are valid for ~2 years unless you log out.")
        except subprocess.CalledProcessError as e:
            print(f"\nSetup failed: {str(e)}")
            print("\nTroubleshooting:")
            print("1. Make sure you're logged into YouTube Music in your browser")
            print("2. Follow the prompts from ytmusicapi")
        except FileNotFoundError:
            print("\nError: ytmusicapi command not found!")
            print("This shouldn't happen as ytmusicapi is installed with this package.")

    @retry_with_backoff(
        max_attempts=3,
        initial_delay=1.0,
        exceptions=(NetworkError, RateLimitError, APIError),
    )
    def search_track(self, track: Track) -> Optional[str]:
        """Search for a track on YouTube Music with retry logic.

        Args:
            track: Track object to search for

        Returns:
            YouTube Music video ID if found, None otherwise

        Raises:
            RateLimitError: If rate limit is exceeded after retries
            NetworkError: If network errors persist after retries
            APIError: If API errors persist after retries
        """
        try:
            # Try searching with ISRC first, but validate the result
            if track.isrc:
                isrc_results = self._search_with_error_handling(
                    track.isrc, filter="songs", limit=3
                )
                if isrc_results:
                    # Validate ISRC result: check if artist matches
                    for result in isrc_results:
                        result_artists = " ".join(
                            [
                                artist["name"].lower()
                                for artist in result.get("artists", [])
                            ]
                        )
                        # Check if at least one artist from Spotify matches
                        if any(
                            artist.lower() in result_artists for artist in track.artists
                        ):
                            return result["videoId"]
                    # If no ISRC result matches the artist, fall through to name search

            # Fall back to name and artist search
            query = track.search_query
            results = self._search_with_error_handling(query, filter="songs", limit=5)

            if not results:
                logger.debug(f"No results found for track: {track.name}")
                return None

            # Try to find the best match
            for result in results:
                # Simple matching: check if track name and artist match
                result_title = result.get("title", "").lower()
                result_artists = " ".join(
                    [artist["name"].lower() for artist in result.get("artists", [])]
                )

                track_name_lower = track.name.lower()

                # Check if both name and at least one artist match
                if track_name_lower in result_title or result_title in track_name_lower:
                    if any(
                        artist.lower() in result_artists for artist in track.artists
                    ):
                        return result["videoId"]

            # If no good match found, return the first result
            return results[0]["videoId"] if results else None

        except Exception as e:
            # Categorize the error for better handling
            categorized_error = categorize_api_error(e, "YouTube Music")
            logger.error(
                f"Error searching for track {track.name}: {str(categorized_error)}"
            )
            raise categorized_error from e

    def _search_with_error_handling(self, query: str, **kwargs) -> List[Dict]:
        """Perform a search with proper error handling.

        Args:
            query: Search query
            **kwargs: Additional arguments for ytmusic.search()

        Returns:
            List of search results

        Raises:
            Categorized exceptions based on the error type
        """
        try:
            return self.ytmusic.search(query, **kwargs)
        except Exception as e:
            raise categorize_api_error(e, "YouTube Music") from e

    @retry_with_backoff(
        max_attempts=3,
        initial_delay=2.0,
        exceptions=(NetworkError, RateLimitError, APIError),
    )
    def create_playlist(
        self, name: str, description: str = "", privacy: str = "PRIVATE"
    ) -> str:
        """Create a new playlist on YouTube Music with retry logic.

        Args:
            name: Playlist name
            description: Playlist description
            privacy: Privacy setting (PRIVATE, PUBLIC, or UNLISTED)

        Returns:
            YouTube Music playlist ID

        Raises:
            RateLimitError: If rate limit is exceeded after retries
            NetworkError: If network errors persist after retries
            APIError: If API errors persist after retries
        """
        try:
            playlist_id = self.ytmusic.create_playlist(
                title=name, description=description, privacy_status=privacy
            )
            logger.info(f"Created playlist: {name} (ID: {playlist_id})")
            return playlist_id
        except Exception as e:
            categorized_error = categorize_api_error(e, "YouTube Music")
            logger.error(f"Error creating playlist {name}: {str(categorized_error)}")
            raise categorized_error from e

    @retry_with_backoff(
        max_attempts=3,
        initial_delay=2.0,
        exceptions=(NetworkError, RateLimitError, APIError),
    )
    def add_tracks_to_playlist(
        self, playlist_id: str, track_ids: List[str]
    ) -> Dict[str, Any]:
        """Add tracks to a YouTube Music playlist with retry logic.

        Args:
            playlist_id: YouTube Music playlist ID
            track_ids: List of YouTube Music video IDs to add

        Returns:
            Response from the API

        Raises:
            RateLimitError: If rate limit is exceeded after retries
            NetworkError: If network errors persist after retries
            APIError: If API errors persist after retries
        """
        if not track_ids:
            return {"status": "No tracks to add"}

        try:
            response = self.ytmusic.add_playlist_items(playlist_id, track_ids)
            logger.info(f"Added {len(track_ids)} tracks to playlist {playlist_id}")
            return response
        except Exception as e:
            categorized_error = categorize_api_error(e, "YouTube Music")
            logger.error(
                f"Error adding tracks to playlist {playlist_id}: {str(categorized_error)}"
            )
            raise categorized_error from e

    def migrate_playlist(self, spotify_playlist: Playlist) -> MigrationResult:
        """Migrate a Spotify playlist to YouTube Music.

        Args:
            spotify_playlist: Playlist object from Spotify

        Returns:
            MigrationResult with details about the migration
        """
        print(f"\nMigrating playlist: {spotify_playlist.name}")
        print(f"Total tracks: {len(spotify_playlist.tracks)}")

        # Create the playlist on YouTube Music
        privacy = "PUBLIC" if spotify_playlist.public else "PRIVATE"
        yt_playlist_id = self.create_playlist(
            name=spotify_playlist.name,
            description=spotify_playlist.description or f"Migrated from Spotify",
            privacy=privacy,
        )

        print(f"Created YouTube Music playlist: {yt_playlist_id}")

        # Search and collect track IDs
        successful_track_ids = []
        failed_tracks = []
        skipped_tracks = []

        # Use tqdm for progress bar
        with tqdm(
            total=len(spotify_playlist.tracks), desc="Searching tracks", unit="track"
        ) as pbar:
            for track in spotify_playlist.tracks:
                pbar.set_postfix_str(f"{track.name[:40]}...")

                try:
                    video_id = self.search_track(track)

                    if video_id:
                        successful_track_ids.append(video_id)
                        track.youtube_id = video_id
                        pbar.set_postfix_str(f"Found: {track.name[:35]}...")
                    else:
                        failed_tracks.append(track)
                        pbar.set_postfix_str(f"Not found: {track.name[:30]}...")

                except (RateLimitError, NetworkError, APIError) as e:
                    # These errors have already been retried, so we skip the track
                    logger.warning(
                        f"Failed to search track after retries: {track.name} - {str(e)}"
                    )
                    failed_tracks.append(track)
                    pbar.set_postfix_str(f"Error: {str(e)[:40]}")

                except Exception as e:
                    # Unexpected errors
                    logger.error(
                        f"Unexpected error searching track {track.name}: {str(e)}"
                    )
                    failed_tracks.append(track)
                    pbar.set_postfix_str(f"Error: {str(e)[:40]}")

                pbar.update(1)

        # Add all successful tracks to the playlist
        if successful_track_ids:
            print(f"\nAdding {len(successful_track_ids)} tracks to playlist...")
            self.add_tracks_to_playlist(yt_playlist_id, successful_track_ids)

        return MigrationResult(
            source_name=spotify_playlist.name,
            destination_name=spotify_playlist.name,
            total_tracks=len(spotify_playlist.tracks),
            successful_tracks=len(successful_track_ids),
            failed_tracks=failed_tracks,
            skipped_tracks=skipped_tracks,
        )

    def get_user_playlists(self) -> List[Dict[str, Any]]:
        """Get all playlists for the authenticated user.

        Returns:
            List of playlist dictionaries
        """
        return self.ytmusic.get_library_playlists()
