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
    existing_tracks = apple_music.get_existing_tracks(apple_pl_name)
    
    # Create lookup sets for fast matching
    existing_paths = {t['path'] for t in existing_tracks if t['path']}
    
    # Determine diff
    files_to_add = []
    for f in local_files:
        # Strict File Path Check
        if os.path.normcase(f) in existing_paths:
            continue
            
        files_to_add.append(f)

    if files_to_add:
        log_info(f"Found {len(files_to_add)} songs to add to Apple Music.")
        
        # --- SETTING CHECK START ---
        # We use the first file to verify the "Copy files" setting
        first_file = files_to_add[0]
        remaining_files = files_to_add[1:]
        
        log_info(f"Adding first file to verify settings: {os.path.basename(first_file)}")
        if apple_music.add_files_to_playlist([first_file], apple_pl_name, delay=2.0) == 1:
            # Verify path immediately
            import time
            # Give it a moment to update
            time.sleep(1.0) 
            
            updated_tracks = apple_music.get_existing_tracks(apple_pl_name)
            
            # Find the track we just added
            added_track = None
            for t in updated_tracks:
                # We can't rely on path being correct yet, so we have to look for name/artist match 
                # OR just look for the path if it WAS copied (which is what we want to detect)
                # But wait, if it was copied, the path will be different.
                # If it wasn't copied, the path will be the same.
                # So we just look for a track with the SAME path.
                if t['path'] and os.path.normcase(t['path']) == os.path.normcase(first_file):
                    added_track = t
                    break
            
            if not added_track:
                # If we can't find the track with the exact path, it might have been copied.
                # Let's try to find it by metadata to confirm it was added but has wrong path.
                # This is tricky because metadata might not match exactly what we expect from filename.
                # But if we just added it, it should be there.
                
                # Let's check if ANY track has the wrong path (i.e. inside Music Media folder)
                # This is hard to generalize.
                
                # Simpler check: If we added it, and it's not in our 'existing_paths' (which we updated?),
                # actually we need to re-fetch.
                
                # Let's look for the file we just added.
                # If we can't find it by path, then the setting is likely ON.
                log_error("CRITICAL: Added file not found by path in Apple Music.")
                log_error(f"Expected Path: {first_file}")
                log_error(f"Normalized Expected: {os.path.normcase(first_file)}")
                
                log_info("Dumping found tracks in Apple Music for debugging:")
                for t in updated_tracks:
                    log_info(f" - Name: {t['name']}")
                    log_info(f"   Artist: {t['artist']}")
                    log_info(f"   Path: {t['path']}")
                    log_info(f"   Raw Location: {t.get('raw_location', 'N/A')}")
                    if t['path']:
                        log_info(f"   Normalized Path: {os.path.normcase(t['path'])}")
                        
                log_error("This likely means 'Copy files to Music Media folder' is ON.")
                log_error("Please UNCHECK 'Copy files to Music Media folder when adding to library' in Music > Settings > Files.")
                
                # Try to clean up if possible? Hard to know which track it is if path doesn't match.
                return
            else:
                log_success("Settings verified: File added with correct path.")
                
        else:
            log_error("Failed to add the first file. Aborting sync.")
            return
            
        # --- SETTING CHECK END ---

        if remaining_files:
            log_info(f"Adding remaining {len(remaining_files)} songs...")
            count = apple_music.add_files_to_playlist(remaining_files, apple_pl_name, delay=2.0)
            log_success(f"Successfully added {count + 1} songs to '{apple_pl_name}'.") # +1 for the first one
        else:
            log_success(f"Successfully added 1 song to '{apple_pl_name}'.")
            
    else:
        log_success("Apple Music playlist is already up to date with local files.")

def main():
    # Load Config
    config = load_config()
    sp_config = config['spotify']
    playlists = config.get('playlists', [])
    default_limit = config.get('sync_limit_default', 50)
    sync_all_playlists = config.get('sync_all_playlists', False)

    # Check Apple Music Settings First
    # Use a temp directory for the check
    import tempfile
    # We can skip the temp dir check here since we do it inline now, 
    # but let's keep the imports if needed later.
    pass

    # Initialize Spotify
    try:
        handler = SpotifyHandler(sp_config)
    except Exception as e:
        log_error(f"Failed to initialize Spotify Client: {e}")
        return

    # Handle "Sync All Playlists"
    if sync_all_playlists:
        log_info("Sync All Playlists is ENABLED. Fetching all user playlists...")
        user_playlists = handler.get_all_user_playlists()
        log_info(f"Found {len(user_playlists)} playlists on Spotify.")
        
        for pl in user_playlists:
            # Sanitize name for folder
            safe_name = "".join([c for c in pl['name'] if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).strip()
            
            # Create job object
            job = {
                'name': pl['name'],
                'type': 'playlist',
                'spotify_playlist_url': pl['spotify_playlist_url'],
                'local_dir': os.path.expanduser(f"~/Music/Spotify/{safe_name}"),
                'apple_playlist_name': pl['name'],
                'sync_limit': default_limit
            }
            playlists.append(job)

    if not playlists:
        log_warning("No playlists defined in settings.yaml and sync_all_playlists is False.")
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
