"""Service for interacting with YouTube Music API."""

import os
from typing import List, Optional, Dict, Any
from ytmusicapi import YTMusic, setup
from ..models.track import Track, Playlist, MigrationResult


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
            raise FileNotFoundError(
                f"YouTube Music headers file not found: {headers_file}\n"
                "Please run the setup command first to authenticate with YouTube Music."
            )

        self.ytmusic = YTMusic(headers_file)

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

    def search_track(self, track: Track) -> Optional[str]:
        """Search for a track on YouTube Music.

        Args:
            track: Track object to search for

        Returns:
            YouTube Music video ID if found, None otherwise
        """
        # Try searching with ISRC first, but validate the result
        if track.isrc:
            isrc_results = self.ytmusic.search(track.isrc, filter="songs", limit=3)
            if isrc_results:
                # Validate ISRC result: check if artist matches
                for result in isrc_results:
                    result_artists = " ".join(
                        [artist["name"].lower() for artist in result.get("artists", [])]
                    )
                    # Check if at least one artist from Spotify matches
                    if any(artist.lower() in result_artists for artist in track.artists):
                        return result["videoId"]
                # If no ISRC result matches the artist, fall through to name search

        # Fall back to name and artist search
        query = track.search_query
        results = self.ytmusic.search(query, filter="songs", limit=5)

        if not results:
            return None

        # Try to find the best match
        for result in results:
            # Simple matching: check if track name and artist match
            result_title = result.get("title", "").lower()
            result_artists = " ".join(
                [artist["name"].lower() for artist in result.get("artists", [])]
            )

            track_name_lower = track.name.lower()
            track_artists_lower = " ".join([artist.lower() for artist in track.artists])

            # Check if both name and at least one artist match
            if track_name_lower in result_title or result_title in track_name_lower:
                if any(
                    artist.lower() in result_artists
                    for artist in track.artists
                ):
                    return result["videoId"]

        # If no good match found, return the first result
        return results[0]["videoId"] if results else None

    def create_playlist(
        self, name: str, description: str = "", privacy: str = "PRIVATE"
    ) -> str:
        """Create a new playlist on YouTube Music.

        Args:
            name: Playlist name
            description: Playlist description
            privacy: Privacy setting (PRIVATE, PUBLIC, or UNLISTED)

        Returns:
            YouTube Music playlist ID
        """
        playlist_id = self.ytmusic.create_playlist(
            title=name, description=description, privacy_status=privacy
        )
        return playlist_id

    def add_tracks_to_playlist(
        self, playlist_id: str, track_ids: List[str]
    ) -> Dict[str, Any]:
        """Add tracks to a YouTube Music playlist.

        Args:
            playlist_id: YouTube Music playlist ID
            track_ids: List of YouTube Music video IDs to add

        Returns:
            Response from the API
        """
        if not track_ids:
            return {"status": "No tracks to add"}

        return self.ytmusic.add_playlist_items(playlist_id, track_ids)

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

        for i, track in enumerate(spotify_playlist.tracks, 1):
            print(f"  [{i}/{len(spotify_playlist.tracks)}] Searching: {track}")

            try:
                video_id = self.search_track(track)

                if video_id:
                    successful_track_ids.append(video_id)
                    track.youtube_id = video_id
                    print(f"    - Found")
                else:
                    failed_tracks.append(track)
                    print(f"    - Not found")

            except Exception as e:
                print(f"    - Error: {str(e)}")
                failed_tracks.append(track)

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
