"""Service for interacting with Spotify API."""

import os
from typing import List, Optional
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from ..models.track import Track, Playlist, Album


class SpotifyService:
    """Handles all interactions with the Spotify API."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """Initialize the Spotify service with credentials.

        Args:
            client_id: Spotify app client ID
            client_secret: Spotify app client secret
            redirect_uri: OAuth redirect URI
        """
        self.scope = "user-library-read playlist-read-private playlist-read-collaborative"

        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=self.scope,
            )
        )

    def get_user_playlists(self) -> List[Playlist]:
        """Fetch all playlists for the authenticated user.

        Returns:
            List of Playlist objects
        """
        playlists = []
        results = self.sp.current_user_playlists()

        while results:
            for item in results["items"]:
                playlist = self._fetch_playlist_details(item["id"])
                playlists.append(playlist)

            # Handle pagination
            if results["next"]:
                results = self.sp.next(results)
            else:
                break

        return playlists

    def get_playlist_by_name(self, name: str) -> Optional[Playlist]:
        """Find a playlist by name.

        Args:
            name: The name of the playlist to find

        Returns:
            Playlist object if found, None otherwise
        """
        playlists = self.get_user_playlists()
        for playlist in playlists:
            if playlist.name.lower() == name.lower():
                return playlist
        return None

    def get_playlist_by_id(self, playlist_id: str) -> Playlist:
        """Fetch a specific playlist by ID.

        Args:
            playlist_id: Spotify playlist ID

        Returns:
            Playlist object
        """
        return self._fetch_playlist_details(playlist_id)

    def _fetch_playlist_details(self, playlist_id: str) -> Playlist:
        """Fetch detailed information about a playlist.

        Args:
            playlist_id: Spotify playlist ID

        Returns:
            Playlist object with all tracks
        """
        playlist_data = self.sp.playlist(playlist_id)
        tracks = self._fetch_playlist_tracks(playlist_id)

        return Playlist(
            name=playlist_data["name"],
            description=playlist_data.get("description", ""),
            tracks=tracks,
            spotify_id=playlist_id,
            owner=playlist_data["owner"]["display_name"],
            public=playlist_data["public"],
        )

    def _fetch_playlist_tracks(self, playlist_id: str) -> List[Track]:
        """Fetch all tracks from a playlist.

        Args:
            playlist_id: Spotify playlist ID

        Returns:
            List of Track objects
        """
        tracks = []
        results = self.sp.playlist_tracks(playlist_id)

        while results:
            for item in results["items"]:
                if item["track"] is None:
                    continue  # Skip deleted tracks

                track_data = item["track"]
                track = self._parse_track(track_data)
                tracks.append(track)

            # Handle pagination
            if results["next"]:
                results = self.sp.next(results)
            else:
                break

        return tracks

    def get_saved_albums(self) -> List[Album]:
        """Fetch all saved albums for the authenticated user.

        Returns:
            List of Album objects
        """
        albums = []
        results = self.sp.current_user_saved_albums()

        while results:
            for item in results["items"]:
                album_data = item["album"]
                album = self._parse_album(album_data)
                albums.append(album)

            # Handle pagination
            if results["next"]:
                results = self.sp.next(results)
            else:
                break

        return albums

    def _parse_album(self, album_data: dict) -> Album:
        """Parse album data from Spotify API response.

        Args:
            album_data: Raw album data from Spotify API

        Returns:
            Album object
        """
        # Fetch full album details to get all tracks
        full_album = self.sp.album(album_data["id"])

        tracks = []
        for track_data in full_album["tracks"]["items"]:
            track = Track(
                name=track_data["name"],
                artists=[artist["name"] for artist in track_data["artists"]],
                album=album_data["name"],
                duration_ms=track_data["duration_ms"],
                spotify_id=track_data["id"],
                isrc=track_data.get("external_ids", {}).get("isrc"),
            )
            tracks.append(track)

        return Album(
            name=album_data["name"],
            artists=[artist["name"] for artist in album_data["artists"]],
            tracks=tracks,
            release_date=album_data.get("release_date"),
            spotify_id=album_data["id"],
        )

    def _parse_track(self, track_data: dict) -> Track:
        """Parse track data from Spotify API response.

        Args:
            track_data: Raw track data from Spotify API

        Returns:
            Track object
        """
        return Track(
            name=track_data["name"],
            artists=[artist["name"] for artist in track_data["artists"]],
            album=track_data["album"]["name"],
            duration_ms=track_data["duration_ms"],
            spotify_id=track_data["id"],
            isrc=track_data.get("external_ids", {}).get("isrc"),
        )

    def get_user_info(self) -> dict:
        """Get information about the current user.

        Returns:
            Dictionary with user information
        """
        return self.sp.current_user()
