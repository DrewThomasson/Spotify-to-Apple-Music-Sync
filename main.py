import os
import sys
from src.config_manager import load_config
from src.spotify_handler import SpotifyHandler
from src import apple_music
from src.utils import log_info, log_success, log_error, log_warning, ask_user, ensure_dir

AUDIO_EXTS = {'.mp3', '.m4a', '.opus', '.flac'}

def scan_directory_for_audio(directory):
    """Returns a list of absolute paths to audio files in the directory."""
    audio_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if os.path.splitext(file)[1].lower() in AUDIO_EXTS:
                audio_files.append(os.path.abspath(os.path.join(root, file)))
    return audio_files

def process_playlist(job, spotify_handler, global_limit):
    name = job['name']
    local_dir = ensure_dir(job['local_dir'])
    apple_pl_name = job['apple_playlist_name']
    
    print("\n" + "="*60)
    log_info(f"Processing: {name}")
    print("="*60)

    # 1. Check Apple Music Playlist State
    if not apple_music.playlist_exists(apple_pl_name):
        log_warning(f"Apple Music playlist '{apple_pl_name}' does not exist.")
        if ask_user("Create this playlist in Apple Music?"):
            if apple_music.create_playlist(apple_pl_name):
                log_success(f"Created playlist '{apple_pl_name}'")
            else:
                log_error("Failed to create playlist. Skipping this job.")
                return
        else:
            log_warning("Skipping job because target playlist is missing.")
            return

    # 2. Determine Download Mode (Fresh vs Update)
    is_empty = len(os.listdir(local_dir)) == 0
    download_limit = job.get('sync_limit', global_limit)
    
    if is_empty:
        log_info("Local directory is empty.")
        if ask_user("Attempt to download ALL songs from this Spotify playlist? (No = use limit)"):
            download_limit = None # No limit
            log_info("Preparing to download entire playlist...")

    # 3. Fetch URLs from Spotify
    log_info("Fetching track list from Spotify...")
    track_urls = spotify_handler.get_tracks(job, limit=download_limit)
    
    if not track_urls:
        log_warning("No tracks found in Spotify source.")
        return

    # 4. Download (SpotDL handles skipping existing files)
    spotify_handler.download_tracks(track_urls, local_dir)

    # 5. Sync to Apple Music
    log_info("Syncing local files to Apple Music...")
    
    # Get what is currently on disk
    local_files = scan_directory_for_audio(local_dir)
    
    # Get what is currently in Apple Music
    # (We normalize paths to ensure accurate comparison)
    existing_am_paths = apple_music.get_existing_tracks(apple_pl_name)
    
    # Determine diff
    files_to_add = []
    for f in local_files:
        if os.path.normcase(f) not in existing_am_paths:
            files_to_add.append(f)

    if files_to_add:
        log_info(f"Found {len(files_to_add)} songs to add to Apple Music.")
        count = apple_music.add_files_to_playlist(files_to_add, apple_pl_name)
        log_success(f"Successfully added {count} songs to '{apple_pl_name}'.")
    else:
        log_success("Apple Music playlist is already up to date with local files.")

def main():
    # Load Config
    config = load_config()
    sp_config = config['spotify']
    playlists = config.get('playlists', [])
    default_limit = config.get('sync_limit_default', 50)

    if not playlists:
        log_warning("No playlists defined in settings.yaml")
        return

    # Initialize Spotify
    try:
        handler = SpotifyHandler(sp_config)
    except Exception as e:
        log_error(f"Failed to initialize Spotify Client: {e}")
        return

    # Run Jobs
    for job in playlists:
        try:
            process_playlist(job, handler, default_limit)
        except Exception as e:
            log_error(f"Critical error processing '{job['name']}': {e}")

    print("\n" + "="*60)
    log_success("All sync jobs completed.")
    print("="*60)

if __name__ == "__main__":
    main()
