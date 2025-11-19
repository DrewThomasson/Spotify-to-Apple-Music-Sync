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
        Fetches track URLs. 
        If limit is None, fetches ALL tracks (pagination).
        """
        tracks = []
        offset = 0
        batch_size = 50
        
        # If limit is provided and small, just use that. 
        # If limit is None (download all), we loop.
        fetch_limit = batch_size if limit is None else limit
        
        while True:
            if playlist_config['type'] == 'saved_tracks':
                results = self.sp.current_user_saved_tracks(limit=fetch_limit, offset=offset)
            else:
                # Extract ID from URL
                pl_id = playlist_config['spotify_playlist_url']
                results = self.sp.playlist_items(pl_id, limit=fetch_limit, offset=offset)

            if not results['items']:
                break

            for item in results['items']:
                if item['track'] and item['track'].get('external_urls'):
                    tracks.append(item['track']['external_urls']['spotify'])
            
            # Break if we hit the user defined limit
            if limit is not None and len(tracks) >= limit:
                tracks = tracks[:limit]
                break
                
            # Break if we've fetched everything available
            if results['next'] is None:
                break
                
            offset += len(results['items'])
            
        return tracks

    def download_tracks(self, track_urls, output_dir):
        """
        Uses SpotDL to download tracks to the specific directory.
        SpotDL automatically skips existing files.
        """
        if not track_urls:
            return []

        log_info(f"Sending {len(track_urls)} songs to SpotDL...")
        
        # Construct SpotDL command
        # --output format ensures files go to the right folder
        cmd = [
            'spotdl', 'download',
            '--output', os.path.join(output_dir, '{artist} - {title}.{ext}')
        ] + track_urls

        try:
            # Run spotdl (suppress heavy output if desired, but keeping it visible is usually good)
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError:
            log_warning("SpotDL encountered an error, but some songs may have downloaded.")
            return False
        except FileNotFoundError:
            log_warning("SpotDL not found! Make sure it is installed (pip install spotdl).")
            return False
