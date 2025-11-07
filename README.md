# Spotify to YouTube Music Migrator

A Python CLI tool to migrate your playlists and albums from Spotify to YouTube Music with smart track matching.

## Features

- Export playlists from Spotify
- Smart track matching using ISRC codes and fuzzy search
- Migrate individual or all playlists
- Detailed migration reports with success rates
- Privacy settings (public/private playlists)
- Album migration (coming soon)

## Prerequisites

- Python 3.10+
- Poetry (for dependency management)
- Spotify Developer Account (free)
- YouTube Music Account

## Quick Start

### 1. Clone and Install

```bash
cd /path/to/spotify-to-ytmusic
poetry install
```

### 2. Set Up Spotify API

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click "Create App"
3. Fill in the app details:
   - App name: "Spotify to YT Music Migrator" (or any name)
   - Redirect URI: `http://localhost:8888/callback`
4. Copy your **Client ID** and **Client Secret**

### 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Spotify credentials
# SPOTIFY_CLIENT_ID=your_client_id_here
# SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

### 4. Set Up YouTube Music

```bash
# Run the setup command to authenticate with YouTube Music
poetry run spotify-to-ytmusic setup-ytmusic

# Follow the prompts to copy browser headers for authentication
```

### 5. Start Migrating!

```bash
# See all your Spotify playlists
poetry run spotify-to-ytmusic list-playlists

# Migrate a specific playlist
poetry run spotify-to-ytmusic migrate-playlist "My Awesome Playlist"

# Migrate all playlists (use with caution!)
poetry run spotify-to-ytmusic migrate-all --limit 5
```

## Commands

### Account Information
```bash
# View Spotify and YouTube Music account info
poetry run spotify-to-ytmusic info
```

### List Content
```bash
# List all Spotify playlists
poetry run spotify-to-ytmusic list-playlists

# List saved albums (not yet implemented)
poetry run spotify-to-ytmusic list-albums
```

### Migration
```bash
# Migrate a specific playlist (private by default)
poetry run spotify-to-ytmusic migrate-playlist "Playlist Name"

# Migrate as public playlist
poetry run spotify-to-ytmusic migrate-playlist "Playlist Name" --public

# Migrate all playlists (you'll be prompted to confirm)
poetry run spotify-to-ytmusic migrate-all

# Migrate limited number of playlists for testing
poetry run spotify-to-ytmusic migrate-all --limit 3
```

## How It Works

1. **Authentication**: Uses OAuth for Spotify and browser header authentication for YouTube Music
2. **Playlist Export**: Fetches playlist metadata and all track details from Spotify
3. **Smart Matching**: Searches for tracks on YouTube Music using:
   - ISRC codes (International Standard Recording Code) for exact matches
   - Track name and artist fuzzy matching as fallback
4. **Playlist Creation**: Creates equivalent playlists on YouTube Music
5. **Track Addition**: Adds matched tracks to the new playlists
6. **Reporting**: Provides detailed success/failure reports

## Project Structure

```
spotify-to-ytmusic/
├── src/
│   └── spotify_to_ytmusic/
│       ├── models/          # Data models (Track, Playlist, Album)
│       ├── services/        # API service wrappers
│       │   ├── spotify_service.py
│       │   └── ytmusic_service.py
│       └── cli.py          # Command-line interface
├── .env.example            # Environment template
├── pyproject.toml          # Poetry dependencies
└── README.md
```

## Troubleshooting

### "Spotify credentials not found"
- Make sure you created a `.env` file (not `.env.example`)
- Verify your Client ID and Secret are correct
- Check there are no extra spaces or quotes

### "YouTube Music headers file not found"
- Run `poetry run spotify-to-ytmusic setup-ytmusic` first
- Follow the browser header authentication instructions completely
- Make sure you're logged into YouTube Music in your browser before copying headers

### Tracks not found
- Some tracks may not be available on YouTube Music
- Regional restrictions may apply
- Check the migration report for failed tracks

## Project Status

**Current**: CLI MVP (Minimum Viable Product)

Successfully migrates Spotify playlists to YouTube Music with smart matching.

## Future Plans

- [ ] Album migration support
- [ ] Web application with UI for easier use
- [ ] Migration history and undo functionality
- [ ] Reverse migration (YouTube Music → Spotify)
- [ ] Batch operations and scheduling
- [ ] Better error handling and retry logic
- [ ] Export migration reports to CSV/JSON

## Contributing

This is currently a personal project. Feel free to fork and modify for your own use.

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0) - see the [LICENSE](LICENSE) file for details.

**Note**: Built with assistance from [Claude Code](https://claude.com/claude-code)
