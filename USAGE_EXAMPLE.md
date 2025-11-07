# Usage Examples

Step-by-step examples for using the Spotify to YouTube Music migrator.

## Initial Setup (One Time Only)

### Step 1: Get Spotify API Credentials

1. Visit https://developer.spotify.com/dashboard
2. Log in with your Spotify account
3. Click "Create App"
4. Fill in:
   - **App name**: Spotify to YT Music Migrator
   - **App description**: Personal tool to migrate playlists
   - **Redirect URI**: `http://localhost:8888/callback`
5. Click "Save"
6. Copy your **Client ID** and **Client Secret**

### Step 2: Configure .env File

```bash
# Create your .env file from the example
cp .env.example .env

# Edit .env with your favorite editor
# Add your Spotify credentials:
SPOTIFY_CLIENT_ID=abc123your_client_id_here
SPOTIFY_CLIENT_SECRET=xyz789your_client_secret_here
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

### Step 3: Authenticate with YouTube Music

```bash
poetry run spotify-to-ytmusic setup-ytmusic
```

This will:
1. Prompt you to copy browser request headers from YouTube Music
2. Guide you through the process of extracting headers from your browser's Developer Tools
3. Validate the headers and save them to `headers_auth.json`

**Important**: Keep `headers_auth.json` private and secure! These credentials are valid for approximately 2 years unless you log out of YouTube Music.

## Basic Usage

### Check Your Connection

```bash
# View account info for both services
poetry run spotify-to-ytmusic info
```

Expected output:
```
Account Information

Spotify:
  Name: Your Name
  Email: your.email@example.com
  Country: US
  Followers: 10

YouTube Music:
  Playlists: 5
  Status: Connected
```

### List Your Playlists

```bash
poetry run spotify-to-ytmusic list-playlists
```

Expected output:
```
Fetching your Spotify playlists...

Logged in as: Your Name

Found 10 playlists:

1. Workout Mix (45 tracks)
2. Chill Vibes (32 tracks)
3. Road Trip 2024 (78 tracks)
...
```

## Migration Examples

### Example 1: Migrate a Single Playlist

```bash
# Migrate a playlist by exact name (case-insensitive)
poetry run spotify-to-ytmusic migrate-playlist "Workout Mix"
```

Expected flow:
```
Starting migration for: Workout Mix

Searching for playlist on Spotify...
Found: Workout Mix (45 tracks)

Migrating playlist: Workout Mix
Total tracks: 45
Created YouTube Music playlist: PLxxxxxxxxxxxxxxxx
  [1/45] Searching: Song Name - Artist Name
    - Found
  [2/45] Searching: Another Song - Another Artist
    - Found
  ...

Adding 43 tracks to playlist...

============================================================
MIGRATION COMPLETE
============================================================
Migration of 'Workout Mix' to 'Workout Mix':
  Total: 45
  Successful: 43
  Failed: 2
  Skipped: 0
  Success Rate: 95.6%

Failed tracks:
  - Obscure Song - Unknown Artist
  - Limited Release - Indie Band
```

### Example 2: Migrate as Public Playlist

```bash
# Create a public playlist on YouTube Music
poetry run spotify-to-ytmusic migrate-playlist "Party Hits" --public
```

### Example 3: Test Migration (Limited)

```bash
# Test with just 2 playlists first
poetry run spotify-to-ytmusic migrate-all --limit 2
```

### Example 4: Migrate All Playlists

```bash
# Migrate everything (you'll be prompted to confirm)
poetry run spotify-to-ytmusic migrate-all
```

Expected flow:
```
Starting migration of all playlists...

This will migrate ALL your playlists. Continue? [y/N]: y
Found 10 playlists to migrate

============================================================
[1/10] Migrating: Workout Mix
============================================================
...

============================================================
MIGRATION SUMMARY
============================================================
Total playlists migrated: 10
Total tracks processed: 450
Successful tracks: 425
Failed tracks: 25
Overall success rate: 94.4%
```

## Tips & Tricks

### Finding Playlist Names

If you're not sure of the exact playlist name:

```bash
# List all playlists
poetry run spotify-to-ytmusic list-playlists

# Find the exact name, then use it:
poetry run spotify-to-ytmusic migrate-playlist "The Exact Name From List"
```

### What If a Track Fails?

Failed tracks usually occur because:
1. The track isn't available on YouTube Music
2. Regional restrictions
3. The track is too new or too obscure
4. Different metadata on YouTube Music

The migration will still create the playlist with all the tracks it could find.

### Re-running Migration

If you run the same migration again, it will:
- Create a **new** playlist (not update the existing one)
- Search for tracks again

To avoid duplicates, manually delete old playlists from YouTube Music before re-running.

## Common Workflows

### Workflow 1: Fresh Start Migration

```bash
# 1. Check everything is set up
poetry run spotify-to-ytmusic info

# 2. See what you have
poetry run spotify-to-ytmusic list-playlists

# 3. Test with one playlist
poetry run spotify-to-ytmusic migrate-playlist "My Favorite Songs"

# 4. If happy, migrate the rest
poetry run spotify-to-ytmusic migrate-all
```

### Workflow 2: Selective Migration

```bash
# Migrate only specific playlists one by one
poetry run spotify-to-ytmusic migrate-playlist "Workout"
poetry run spotify-to-ytmusic migrate-playlist "Focus Music"
poetry run spotify-to-ytmusic migrate-playlist "Party Playlist"
```

### Workflow 3: Test Before Full Migration

```bash
# Test with 3 playlists
poetry run spotify-to-ytmusic migrate-all --limit 3

# Review results in YouTube Music

# If satisfied, do the rest
poetry run spotify-to-ytmusic migrate-all
```

## Troubleshooting

### Error: "Spotify credentials not found"

**Problem**: `.env` file is missing or incorrectly configured

**Solution**:
```bash
# Check if .env exists
ls -la .env

# If not, create it
cp .env.example .env

# Edit and add credentials
nano .env  # or use any editor
```

### Error: "YouTube Music headers file not found"

**Problem**: Haven't run the YouTube Music setup

**Solution**:
```bash
poetry run spotify-to-ytmusic setup-ytmusic
```

### Error: "Playlist not found"

**Problem**: Typo in playlist name or case mismatch

**Solution**:
```bash
# List all playlists to see exact names
poetry run spotify-to-ytmusic list-playlists

# Copy the exact name and use it
poetry run spotify-to-ytmusic migrate-playlist "Exact Name Here"
```

### High Failure Rate

**Problem**: Many tracks failing to migrate

**Possible causes**:
- Regional differences in YouTube Music catalog
- Very niche/indie music
- Tracks from local files in Spotify

**Note**: 80-90% success rate is typical. Some tracks simply won't be available on YouTube Music.

## Next Steps

After successful migration:

1. **Verify** - Check your YouTube Music app/website to see the new playlists
2. **Clean up** - Remove any duplicate playlists manually
3. **Customize** - Edit playlist descriptions or covers in YouTube Music
4. **Enjoy** - Your music is now on YouTube Music!

## Need More Help?

- Check the main [README.md](README.md) for detailed documentation
- Review your `.env` file for correct credentials
- Make sure both Spotify and YouTube Music accounts are active
