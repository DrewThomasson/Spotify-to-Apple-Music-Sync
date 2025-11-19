import subprocess
import os
from .utils import log_warning, log_error

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
            set pathList to {{}}
            repeat with t in (get tracks of user playlist "{playlist_name}")
                try
                    if location of t is not missing value then
                        copy POSIX path of (location of t) to end of pathList
                    end if
                end try
            end repeat
            return pathList
        else
            return ""
        end if
    end tell
    '''
    success, output = run_applescript(script)
    if not success:
        return set()
    
    # AppleScript returns comma separated list often, or newlines. 
    # We sanitize and normalize.
    paths = set()
    if output:
        # Handle standard AppleScript list output formatting
        clean_output = output.replace(', /', '\n/').split('\n')
        for p in clean_output:
            p = p.strip().strip(',').strip()
            if p:
                paths.add(os.path.normcase(p))
    return paths

def add_files_to_playlist(file_paths, playlist_name):
    """Adds a list of file paths to the playlist."""
    if not file_paths:
        return 0

    count = 0
    # Apple Music handles batches better than one-by-one
    for file_path in file_paths:
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
        else:
            log_warning(f"Failed to add to Apple Music: {os.path.basename(file_path)}")
            
    return count
