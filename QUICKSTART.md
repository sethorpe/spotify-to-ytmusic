# Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites Check

Before starting, make sure you have:
- [ ] Python 3.10 or higher installed
- [ ] Poetry installed
- [ ] A Spotify account
- [ ] A YouTube Music account (or YouTube Premium)

Check Python version:
```bash
python3 --version
# Should show 3.10 or higher
```

Check Poetry:
```bash
poetry --version
# Should show Poetry version 1.x or higher
```

## 5-Minute Setup

### 1. Install Dependencies (1 minute)

```bash
cd /path/to/spotify-to-ytmusic
poetry install
```

Wait for installation to complete...

### 2. Get Spotify Credentials (2 minutes)

**Quick Steps:**
1. Go to: https://developer.spotify.com/dashboard
2. Click "Create App"
3. Fill in:
   - Name: "My Playlist Migrator"
   - Description: "Personal use"
   - Redirect URI: `http://localhost:8888/callback`
4. Click "Save"
5. Click "Settings"
6. Copy your **Client ID**
7. Copy your **Client Secret**

### 3. Create .env File (30 seconds)

```bash
# Copy the example
cp .env.example .env

# Edit the file (use any editor)
nano .env
```

Paste your credentials:
```bash
SPOTIFY_CLIENT_ID=paste_your_client_id_here
SPOTIFY_CLIENT_SECRET=paste_your_client_secret_here
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

Save and exit (Ctrl+X, then Y, then Enter for nano)

### 4. Authenticate YouTube Music (1 minute)

```bash
poetry run spotify-to-ytmusic setup-ytmusic
```

This will:
1. Prompt you to copy browser request headers from YouTube Music
2. Guide you through the process step-by-step
3. Save the authentication headers for future use

Follow the on-screen instructions carefully to complete the setup.

### 5. Test It! (30 seconds)

```bash
# See your Spotify playlists
poetry run spotify-to-ytmusic list-playlists
```

You should see a list of your playlists!

## Your First Migration

Now that everything is set up, let's migrate a playlist:

```bash
# List your playlists
poetry run spotify-to-ytmusic list-playlists

# Choose one and migrate it (replace with your playlist name)
poetry run spotify-to-ytmusic migrate-playlist "Your Playlist Name"
```

Wait for the migration to complete, then check YouTube Music to see your new playlist!

## What's Next?

- Read [USAGE_EXAMPLE.md](USAGE_EXAMPLE.md) for more examples
- Read [README.md](README.md) for full documentation
- Read [DEVELOPMENT.md](DEVELOPMENT.md) if you want to contribute

## Troubleshooting Quick Fixes

### "Command not found: poetry"

Install Poetry:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### "Spotify credentials not found"

Make sure you:
1. Created `.env` file (not `.env.example`)
2. Added your credentials without quotes
3. Saved the file

### "YouTube Music setup failed"

Make sure you:
1. Are logged into YouTube Music in your browser (Firefox or Chrome)
2. Open the Network tab in Developer Tools before copying headers
3. Copy the complete request headers as instructed

### "Playlist not found"

Make sure you typed the exact playlist name (case-insensitive). Use `list-playlists` to see the exact names.

## Need Help?

Check out:
- [README.md](README.md) - Full documentation
- [USAGE_EXAMPLE.md](USAGE_EXAMPLE.md) - Detailed examples
- [DEVELOPMENT.md](DEVELOPMENT.md) - Technical details

Happy migrating! to YouTube Music
