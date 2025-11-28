# Spotify to Apple Music Sync

> [!IMPORTANT]
> **CRITICAL SETUP STEP**: Before using this tool, you **MUST** disable "Copy files to Music Media folder when adding to library" in Apple Music.
>
> 1. Open Apple Music.
> 2. Go to **Music** > **Settings...** > **Files**.
> 3. **UNCHECK** "Copy files to Music Media folder when adding to library".
> 4. **UNCHECK** "Keep Music Media folder organized" (recommended).
>
> If you do not do this, the sync **WILL FAIL** and duplicate songs will be created.

This is for auto-syncing your spotify playlists to your offline Apple Music

## Features
- **Multi-Playlist Support:** Sync "Liked Songs" and custom playlists simultaneously.
- **Local Backups:** Downloads high-quality audio via `spotdl` to organized local folders.
- **Smart Syncing:** Checks Apple Music contents to avoid duplicates.
- **Interactive:** Detects new setups and asks if you want to download the *entire* history or just recent updates.
- **Configurable:** All settings managed in a clean YAML file.

## Prerequisites
- macOS (Required for Apple Music integration)
- Python 3.8+
- [FFmpeg](https://ffmpeg.org/download.html) (Required by spotdl)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/spotify-sync.git
   cd spotify-sync
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install FFmpeg:**
   ```bash
   brew install ffmpeg
   ```

4. **Configuration:**
   - Rename `config/settings.yaml.example` to `config/settings.yaml` (if applicable) or create it.
   - Get your Spotify API Credentials from [developer.spotify.com](https://developer.spotify.com/dashboard/).
   - Fill in `client_id` and `client_secret` in the config file.
   - Define your playlists in the config file (see example below).

## Usage

Simply run:
```bash
python main.py
```

On the first run, if a local directory is empty, the script will ask if you want to attempt a full download (all songs) or just the most recent 50 (default for updates).

## Configuration Example

```yaml
spotify:
  client_id: "..."
  client_secret: "..."
  redirect_uri: "http://127.0.0.1:8888/callback"
  scope: "user-library-read"

# Default limit for number of songs to sync per playlist
sync_limit_default: 50

# Set to true to automatically sync ALL your Spotify playlists
# This will create a folder for each playlist in ~/Music/Spotify/
sync_all_playlists: false

playlists:
  # --- Example 1: Sync "Liked Songs" (Saved Tracks) ---
  - name: "Liked Songs"
    type: "saved_tracks"                  # Special type for 'Liked Songs'
    local_dir: "~/Music/Spotify/LikedSongs" # Where to save the files locally
    apple_playlist_name: "Spotify Liked"  # Name of the playlist in Apple Music
    sync_limit: 100                       # Optional: Override global sync limit for this job

  # --- Example 2: Sync a Specific Spotify Playlist ---
  - name: "Gym Hits"
    type: "playlist"
    spotify_playlist_url: "https://open.spotify.com/playlist/37i9dQZF1DX9sIqqvKsjG8"
    local_dir: "~/Music/Spotify/GymMix"
    apple_playlist_name: "Gym Hits"
    sync_limit: 100                       # Optional: Download up to 100 songs (default is 50)
```
