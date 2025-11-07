# Development Guide

Guide for developing and extending the Spotify to YouTube Music migrator.

## Project Structure

```
spotify-to-ytmusic/
├── src/
│   └── spotify_to_ytmusic/
│       ├── __init__.py
│       ├── cli.py                      # CLI interface (Click commands)
│       ├── models/
│       │   ├── __init__.py
│       │   └── track.py               # Data models (Track, Playlist, Album, MigrationResult)
│       ├── services/
│       │   ├── __init__.py
│       │   ├── spotify_service.py     # Spotify API wrapper
│       │   └── ytmusic_service.py     # YouTube Music API wrapper
│       └── utils/
│           └── __init__.py            # Utility functions (future)
├── .env.example                        # Environment variable template
├── .env                                # Your credentials (gitignored)
├── .gitignore
├── pyproject.toml                      # Poetry dependencies & config
├── poetry.lock                         # Locked dependencies
├── README.md                           # User documentation
├── USAGE_EXAMPLE.md                    # Usage examples
└── DEVELOPMENT.md                      # This file
```

## Technology Stack

- **Python 3.10+**: Core language
- **Poetry**: Dependency management and packaging
- **Click**: CLI framework for command-line interface
- **Spotipy**: Spotify Web API wrapper
- **ytmusicapi**: YouTube Music API wrapper
- **python-dotenv**: Environment variable management

## Development Setup

### 1. Install Poetry

If you don't have Poetry installed:

```bash
# macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -

# Or via pip
pip install poetry
```

### 2. Install Dependencies

```bash
cd /Users/seyithorpe/Document/@DevProjects/spotify-to-ytmusic
poetry install
```

### 3. Activate Virtual Environment

```bash
# Option 1: Use poetry shell
poetry shell

# Option 2: Run commands with poetry run
poetry run spotify-to-ytmusic --help
```

### 4. Set Up Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

## Code Architecture

### Data Models ([src/spotify_to_ytmusic/models/track.py](src/spotify_to_ytmusic/models/track.py))

**Track**: Represents a single music track
- Properties: name, artists, album, duration_ms, isrc, spotify_id, youtube_id
- Method: `search_query` - generates search string for other platforms

**Playlist**: Represents a playlist
- Properties: name, description, tracks, spotify_id, youtube_id, owner, public
- Method: `total_duration_ms` - calculates total duration

**Album**: Represents an album
- Properties: name, artists, tracks, release_date, spotify_id, youtube_id

**MigrationResult**: Captures migration outcomes
- Properties: source_name, destination_name, total_tracks, successful_tracks, failed_tracks, skipped_tracks
- Method: `success_rate` - calculates percentage

### Services

#### SpotifyService ([src/spotify_to_ytmusic/services/spotify_service.py](src/spotify_to_ytmusic/services/spotify_service.py))

Wraps the Spotipy library for easier usage.

**Key Methods**:
- `get_user_playlists()` - Fetch all user playlists with pagination
- `get_playlist_by_name(name)` - Find specific playlist
- `get_playlist_by_id(id)` - Fetch playlist by ID
- `get_saved_albums()` - Fetch user's saved albums
- `_parse_track(data)` - Convert API response to Track model
- `_parse_album(data)` - Convert API response to Album model

#### YouTubeMusicService ([src/spotify_to_ytmusic/services/ytmusic_service.py](src/spotify_to_ytmusic/services/ytmusic_service.py))

Wraps the ytmusicapi library.

**Key Methods**:
- `setup_browser_auth(filepath)` - Static method for browser header authentication setup
- `search_track(track)` - Search for track using ISRC or fuzzy matching
- `create_playlist(name, description, privacy)` - Create new playlist
- `add_tracks_to_playlist(playlist_id, track_ids)` - Add tracks to playlist
- `migrate_playlist(spotify_playlist)` - Complete migration workflow
- `get_user_playlists()` - List user's YT Music playlists

### CLI ([src/spotify_to_ytmusic/cli.py](src/spotify_to_ytmusic/cli.py))

Click-based command-line interface.

**Commands**:
- `setup-ytmusic` - Browser header authentication setup for YouTube Music
- `list-playlists` - List Spotify playlists
- `list-albums` - List saved albums
- `migrate-playlist <name>` - Migrate single playlist
- `migrate-all` - Migrate all playlists
- `info` - Display account information

## Adding New Features

### Example: Add Album Migration

1. **Update CLI** ([cli.py](src/spotify_to_ytmusic/cli.py)):

```python
@cli.command()
@click.argument("album_name")
def migrate_album(album_name: str):
    """Migrate a specific album to YouTube Music."""
    spotify = get_spotify_service()
    ytmusic = get_ytmusic_service()

    # Implementation here
    pass
```

2. **Update Service** ([ytmusic_service.py](src/spotify_to_ytmusic/services/ytmusic_service.py)):

```python
def migrate_album(self, spotify_album: Album) -> MigrationResult:
    """Migrate a Spotify album to YouTube Music."""
    # Similar to migrate_playlist but for albums
    pass
```

3. **Test**:

```bash
poetry run spotify-to-ytmusic migrate-album "Album Name"
```

### Example: Add Logging

1. **Install dependency**:

```bash
poetry add loguru
```

2. **Create logger utility** ([utils/logger.py](src/spotify_to_ytmusic/utils/logger.py)):

```python
from loguru import logger

def setup_logger(verbose: bool = False):
    logger.add("migration.log", rotation="10 MB")
    if verbose:
        logger.add(sys.stdout, level="DEBUG")
```

3. **Use in CLI**:

```python
from .utils.logger import setup_logger

@cli.command()
@click.option("--verbose", is_flag=True)
def migrate_playlist(playlist_name: str, verbose: bool):
    setup_logger(verbose)
    # rest of implementation
```

## Testing

Currently, there are no automated tests. Future additions could include:

### Unit Tests

```python
# tests/test_models.py
from spotify_to_ytmusic.models.track import Track

def test_track_search_query():
    track = Track(
        name="Test Song",
        artists=["Artist One", "Artist Two"],
        album="Test Album",
        duration_ms=180000
    )
    assert track.search_query == "Test Song Artist One, Artist Two"
```

### Integration Tests

```python
# tests/test_spotify_service.py
from spotify_to_ytmusic.services.spotify_service import SpotifyService

def test_spotify_connection():
    service = SpotifyService(client_id, client_secret, redirect_uri)
    user_info = service.get_user_info()
    assert user_info is not None
```

## Common Development Tasks

### Add a New Dependency

```bash
poetry add package-name
```

### Update Dependencies

```bash
poetry update
```

### Run CLI During Development

```bash
poetry run spotify-to-ytmusic <command>
```

### Format Code (Optional)

```bash
# Add black for code formatting
poetry add --group dev black

# Format code
poetry run black src/
```

### Type Checking (Optional)

```bash
# Add mypy for type checking
poetry add --group dev mypy

# Check types
poetry run mypy src/
```

## API Rate Limits

### Spotify API
- Rate limit: ~180 requests per minute
- Handles pagination automatically in SpotifyService

### YouTube Music API
- Rate limit: Not publicly documented
- Add delays if encountering rate limit errors

## Environment Variables

All configuration via `.env` file:

```bash
# Required for Spotify
SPOTIFY_CLIENT_ID=xxx
SPOTIFY_CLIENT_SECRET=xxx
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback

# Optional - YouTube Music auth file location
YTMUSIC_HEADERS_FILE=ytmusic_headers.json
```

## Future Enhancements

### Short Term
- [ ] Add progress bars with tqdm
- [ ] Better error messages and recovery
- [ ] Retry logic for failed tracks
- [ ] Export migration reports to CSV/JSON
- [ ] Album migration support

### Medium Term
- [ ] Web UI with Flask/FastAPI
- [ ] Migration history database (SQLite)
- [ ] Undo/rollback functionality
- [ ] Scheduled migrations

### Long Term
- [ ] Reverse migration (YT Music → Spotify)
- [ ] Multi-platform support (Apple Music, Tidal, etc.)
- [ ] Playlist synchronization
- [ ] Collaborative features

## Building for Distribution

### Build Package

```bash
poetry build
```

Creates `dist/` directory with:
- `.whl` file (wheel)
- `.tar.gz` file (source)

### Publish to PyPI (Future)

```bash
poetry publish
```

## Contributing

Currently a personal project. Guidelines for future contributions:

1. Fork the repository
2. Create a feature branch
3. Make changes with clear commit messages
4. Test thoroughly
5. Submit pull request

## Resources

- [Spotipy Documentation](https://spotipy.readthedocs.io/)
- [ytmusicapi Documentation](https://ytmusicapi.readthedocs.io/)
- [Click Documentation](https://click.palletsprojects.com/)
- [Poetry Documentation](https://python-poetry.org/docs/)

## License

TBD - To be determined before open-sourcing.
