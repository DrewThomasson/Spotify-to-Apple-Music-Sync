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

    def _extract_artist_id(self, url_or_uri):
        """
        Extract artist ID from Spotify URL or URI.
        Supports formats:
        - https://open.spotify.com/artist/4W2IGF6LXg7daQqMGy9S0O
        - spotify:artist:4W2IGF6LXg7daQqMGy9S0O
        """
        artist_id = None
        
        if 'spotify.com/artist/' in url_or_uri:
            # Extract from URL
            parts = url_or_uri.split('spotify.com/artist/')[-1].split('?')[0].split('/')
            artist_id = parts[0] if parts[0] else None
        elif 'spotify:artist:' in url_or_uri:
            # Extract from URI
            parts = url_or_uri.split('spotify:artist:')[-1].split(':')
            artist_id = parts[0] if parts[0] else None
        
        if not artist_id or len(artist_id) < 10:  # Spotify IDs are typically 22 characters
            raise ValueError(f"Invalid artist URL or URI: {url_or_uri}")
        
        return artist_id
    
    def _get_artist_tracks(self, artist_id, limit=None):
        """
        Fetches all tracks from an artist by getting all their albums and then all tracks from those albums.
        """
        tracks = []
        
        # Get all albums from the artist (albums, singles, and compilations)
        albums = []
        offset = 0
        
        while True:
            results = self.sp.artist_albums(
                artist_id, 
                album_type='album,single,compilation',
                limit=50,
                offset=offset
            )
            
            if not results['items']:
                break
                
            albums.extend(results['items'])
            
            if results['next'] is None:
                break
                
            offset += len(results['items'])
        
        # Get tracks from each album
        for album in albums:
            album_id = album['id']
            album_offset = 0
            
            while True:
                album_tracks = self.sp.album_tracks(album_id, limit=50, offset=album_offset)
                
                if not album_tracks['items']:
                    break
                
                for track in album_tracks['items']:
                    if track.get('external_urls') and track['external_urls'].get('spotify'):
                        tracks.append(track['external_urls']['spotify'])
                        
                        # Check if we've reached the limit
                        if limit is not None and len(tracks) >= limit:
                            return tracks[:limit]
                
                if album_tracks['next'] is None:
                    break
                    
                album_offset += len(album_tracks['items'])
        
        return tracks

    def get_tracks(self, playlist_config, limit=50):
        """
        Fetches track URLs from Spotify.
        """
        tracks = []
        offset = 0
        batch_size = 50
        
        fetch_limit = batch_size if limit is None else limit
        
        if playlist_config['type'] == 'artist':
            # Handle artist type
            artist_url = playlist_config['spotify_artist_url']
            artist_id = self._extract_artist_id(artist_url)
            return self._get_artist_tracks(artist_id, limit=limit)
        
        # Handle saved_tracks and playlist types
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