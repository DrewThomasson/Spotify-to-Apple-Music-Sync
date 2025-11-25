# Spotify to Apple Music (iPod) Sync

A professional tool to sync multiple Spotify playlists (or your Liked Songs) to local storage and import them automatically into specific Apple Music playlists. (I made this for auto-Syncing my ipod with my spotify playlists)

# IMPORTANT
### MAKE SURE TO GO INTO APPLE MUSIC SETTINGS -> FILES AND TURN OFF COPY FILES TO MUSIC MEDIA folder when adding to library

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

playlists:
  - name: "My Liked Songs"
    type: "saved_tracks"
    local_dir: "~/Music/Spotify_Liked"
    apple_playlist_name: "Spotify Liked"

  - name: "Gym Mix"
    type: "playlist"
    spotify_playlist_url: "https://open.spotify.com/playlist/..."
    local_dir: "~/Music/Gym_Mix"
    apple_playlist_name: "Gym Hits"
```
