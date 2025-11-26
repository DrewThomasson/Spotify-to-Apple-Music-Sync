import subprocess
import os
from .utils import log_warning, log_error, log_info

def run_applescript(script):
    """Executes raw AppleScript."""
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, check=True
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def playlist_exists(playlist_name):
    script = f'tell application "Music" to return exists user playlist "{playlist_name}"'
    success, output = run_applescript(script)
    return success and output == 'true'

def create_playlist(playlist_name):
    script = f'tell application "Music" to make new user playlist with properties {{name:"{playlist_name}"}}'
    return run_applescript(script)[0]

def get_existing_tracks(playlist_name):
    """Returns a set of normalized file paths currently in the Apple Music playlist."""
    script = f'''
    tell application "Music"
        if exists user playlist "{playlist_name}" then
            set outputList to {{}}
            set trackCount to count of tracks of user playlist "{playlist_name}"
            set playlistTracks to tracks of user playlist "{playlist_name}"
            
            repeat with t in playlistTracks
                set tName to name of t
                set tArtist to artist of t
                try
                    set tLoc to location of t
                    if tLoc is not missing value then
                        set tPath to POSIX path of tLoc
                        copy (tName & "|||" & tArtist & "|||" & tPath) to end of outputList
                    else
                        copy (tName & "|||" & tArtist & "|||MISSING_LOCATION") to end of outputList
                    end if
                on error errMsg
                    copy (tName & "|||" & tArtist & "|||ERROR: " & errMsg) to end of outputList
                end try
            end repeat
            
            set AppleScript's text item delimiters to ":::"
            return (trackCount as text) & ":::" & (outputList as text)
        else
            return "PLAYLIST_NOT_FOUND"
        end if
    end tell
    '''
    success, output = run_applescript(script)
    
    if not success:
        log_error(f"AppleScript error checking playlist '{playlist_name}': {output}")
        return []
        
    if output == "PLAYLIST_NOT_FOUND":
        log_warning(f"Playlist '{playlist_name}' not found during track check.")
        return []

    # Output format: "TrackCount:::Name|||Artist|||Location:::Name|||Artist|||Location..."
    parts = output.split(":::")
    track_count_str = parts[0]
    track_data = parts[1:]
    
    try:
        total_tracks = int(track_count_str)
    except:
        total_tracks = 0
        
    log_info(f"Debug: Apple Music reports {total_tracks} tracks in '{playlist_name}'.")
    
    tracks = []
    
    for item in track_data:
        if not item.strip():
            continue
            
        if "|||" in item:
            parts = item.split("|||")
            if len(parts) >= 3:
                name = parts[0].strip()
                artist = parts[1].strip()
                loc = parts[2].strip()
                
                track_info = {
                    'name': name,
                    'artist': artist,
                    'path': None,
                    'raw_location': loc
                }
                
                if loc and not loc.startswith("MISSING_LOCATION") and not loc.startswith("ERROR"):
                    track_info['path'] = os.path.normcase(loc)
                
                tracks.append(track_info)
        else:
            pass

    log_info(f"Debug: Parsed {len(tracks)} tracks from Apple Music.")
    return tracks

def delete_playlist(playlist_name):
    script = f'tell application "Music" to delete user playlist "{playlist_name}"'
    return run_applescript(script)[0]

def add_files_to_playlist(file_paths, playlist_name, delay=1.0):
    """Adds a list of file paths to the playlist."""
    if not file_paths:
        return 0

    import time
    count = 0
    # Apple Music handles batches better than one-by-one
    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        log_info(f"Adding: {file_name}")
        
        # AppleScript requires POSIX file format
        script = f'''
        tell application "Music"
            try
                add (POSIX file "{file_path}") to user playlist "{playlist_name}"
            on error
                return "fail"
            end try
        end tell
        '''
        success, _ = run_applescript(script)
        if success:
            count += 1
            time.sleep(delay)
        else:
            log_warning(f"Failed to add to Apple Music: {file_name}")
            
    return count
