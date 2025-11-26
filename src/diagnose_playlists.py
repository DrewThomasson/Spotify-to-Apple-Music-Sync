import subprocess

def run_applescript(script):
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, check=True
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def list_playlists():
    script = '''
    tell application "Music"
        set output to ""
        repeat with p in user playlists
            set pName to name of p
            set tCount to count of tracks of p
            set output to output & "Name: " & pName & " | Tracks: " & tCount & "\n"
        end repeat
        return output
    end tell
    '''
    success, output = run_applescript(script)
    if success:
        print("=== Apple Music Playlists ===")
        print(output)
    else:
        print(f"Error: {output}")

if __name__ == "__main__":
    list_playlists()
