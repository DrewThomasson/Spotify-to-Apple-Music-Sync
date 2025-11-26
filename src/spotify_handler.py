import spotipy
from spotipy.oauth2 import SpotifyOAuth
import subprocess
import os
from .utils import log_info, log_success, log_warning

class SpotifyHandler:
    def __init__(self, config):
        self.config = config
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            redirect_uri=config['redirect_uri'],
            scope=config['scope'],
            cache_path=".spotdl_cache"
        ))

    def get_tracks(self, playlist_config, limit=50):
        """
        Fetches track URLs from Spotify.
        """
        tracks = []
        offset = 0
        batch_size = 50
        
        fetch_limit = batch_size if limit is None else limit
        
        while True:
            if playlist_config['type'] == 'saved_tracks':
                results = self.sp.current_user_saved_tracks(limit=fetch_limit, offset=offset)
            else:
                pl_url = playlist_config['spotify_playlist_url']
                results = self.sp.playlist_items(pl_url, limit=fetch_limit, offset=offset)

            if not results['items']:
                break

            for item in results['items']:
                if item.get('track') and item['track'].get('external_urls'):
                    tracks.append(item['track']['external_urls']['spotify'])
            
            if limit is not None and len(tracks) >= limit:
                tracks = tracks[:limit]
                break
                
            if results['next'] is None:
                break
                
            offset += len(results['items'])
            
        return tracks

    def download_tracks(self, track_urls, output_dir):
        """
        Uses SpotDL to download tracks.
        Strategy: Changes the 'current working directory' to the output folder,
        then runs the simple command, mimicking the original working script.
        """
        if not track_urls:
            return []

        log_info(f"Sending {len(track_urls)} songs to SpotDL...")
        
        # Ensure output dir exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # We still batch to be safe, but we remove the complicated flags
        BATCH_SIZE = 50 
        
        for i in range(0, len(track_urls), BATCH_SIZE):
            chunk = track_urls[i:i + BATCH_SIZE]
            
            # The command is exactly what worked for you before:
            # spotdl download url1 url2 url3 ...
            cmd = ['spotdl', 'download'] + chunk
            
            try:
                # KEY FIX: cwd=output_dir
                # This tells Python: "Go into this folder, THEN run the command."
                # This forces the download to land in the right place without using flags.
                subprocess.run(cmd, cwd=output_dir, check=True)
            except subprocess.CalledProcessError:
                log_warning(f"SpotDL skipped some songs in batch {i//BATCH_SIZE + 1}, usually because they already exist.")
            except FileNotFoundError:
                log_warning("SpotDL not found! Make sure it is installed (pip install spotdl).")
                return False
                
        return True

    def get_all_user_playlists(self):
        """
        Fetches all playlists for the current user.
        Returns a list of dicts: {'name': str, 'spotify_playlist_url': str}
        """
        playlists = []
        results = self.sp.current_user_playlists(limit=50)
        
        while results:
            for item in results['items']:
                if item and item.get('name') and item.get('external_urls'):
                    playlists.append({
                        'name': item['name'],
                        'spotify_playlist_url': item['external_urls']['spotify']
                    })
            
            if results['next']:
                results = self.sp.next(results)
            else:
                break
                
        return playlists