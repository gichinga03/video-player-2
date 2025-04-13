from flask import Flask, send_file, render_template, request, jsonify, Response, redirect, url_for, send_from_directory
import os
import mimetypes
import json
import time
import re
import ffmpeg
import tempfile
import shutil
from dotenv import load_dotenv
import os
from mutagen import File
from mutagen.easyid3 import EasyID3
import requests
import hashlib
from PIL import Image
from io import BytesIO

load_dotenv()
app = Flask(__name__)
app.secret_key = "BE61D9E9B64AC871D85FD7C285F7D"

# Folder paths for movies, series, and music
MOVIE_FOLDER = os.getenv("MOVIE")
SERIES_FOLDER = os.getenv("SERIES")
MUSIC_FOLDER = r"C:\Users\gichi\Music"
ALBUM_COVERS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "album_covers")

# Create album covers directory if it doesn't exist
os.makedirs(ALBUM_COVERS_FOLDER, exist_ok=True)

# Create default album cover if it doesn't exist
default_cover_path = os.path.join(ALBUM_COVERS_FOLDER, "default.jpg")
if not os.path.exists(default_cover_path):
    try:
        # Download a default cover
        response = requests.get("https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?ixlib=rb-1.2.1&auto=format&fit=crop&w=300&q=80")
        if response.status_code == 200:
            # Process and save the image
            img = Image.open(BytesIO(response.content))
            img = img.convert('RGB')
            img.save(default_cover_path, 'JPEG', quality=85)
            print(f"Created default album cover at {default_cover_path}")
    except Exception as e:
        print(f"Error creating default album cover: {e}")
        # Create a simple colored image as fallback
        try:
            img = Image.new('RGB', (300, 300), color=(29, 185, 84))  # Spotify green
            img.save(default_cover_path, 'JPEG')
            print(f"Created fallback default album cover at {default_cover_path}")
        except Exception as e:
            print(f"Error creating fallback default album cover: {e}")

# Debug information
print(f"MOVIE_FOLDER: {MOVIE_FOLDER}")
print(f"SERIES_FOLDER: {SERIES_FOLDER}")
print(f"MUSIC_FOLDER: {MUSIC_FOLDER}")
print(f"ALBUM_COVERS_FOLDER: {ALBUM_COVERS_FOLDER}")
print(f"MOVIE_FOLDER exists: {os.path.exists(MOVIE_FOLDER)}")
print(f"SERIES_FOLDER exists: {os.path.exists(SERIES_FOLDER)}")
print(f"MUSIC_FOLDER exists: {os.path.exists(MUSIC_FOLDER)}")
print(f"ALBUM_COVERS_FOLDER exists: {os.path.exists(ALBUM_COVERS_FOLDER)}")

# Set Flask app configuration
app.config['MOVIE_FOLDER'] = MOVIE_FOLDER
app.config['SERIES_FOLDER'] = SERIES_FOLDER
app.config['MUSIC_FOLDER'] = MUSIC_FOLDER
app.config['ALBUM_COVERS_FOLDER'] = ALBUM_COVERS_FOLDER

# File to store playback positions
PLAYBACK_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "playback_data.json")

# Initialize playback data
def load_playback_data():
    if os.path.exists(PLAYBACK_DATA_FILE):
        try:
            with open(PLAYBACK_DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_playback_data(data):
    with open(PLAYBACK_DATA_FILE, 'w') as f:
        json.dump(data, f)

# Load playback data at startup
playback_data = load_playback_data()

def get_video_files(directory):
    if not os.path.exists(directory):
        print(f"Directory does not exist: {directory}")
        return []
    
    try:
        files = [f for f in os.listdir(directory) if f.lower().endswith(('.mp4', '.mkv', '.avi', '.ts'))]
        print(f"Found {len(files)} video files in {directory}")
        return files
    except Exception as e:
        print(f"Error reading directory {directory}: {e}")
        return []

def normalize_path(path):
    return path.replace('\\', '/').strip()

@app.route('/')
def index():
    try:
        # Get movies
        print(f"Getting movies from {MOVIE_FOLDER}")
        movies = get_video_files(MOVIE_FOLDER)
        print(f"Movies found: {movies}")
        
        # Get all series folders directly
        print(f"Getting series from {SERIES_FOLDER}")
        series = []
        if os.path.exists(SERIES_FOLDER):
            series = [d for d in os.listdir(SERIES_FOLDER) 
                     if os.path.isdir(os.path.join(SERIES_FOLDER, d))]
            series = sorted(series)  # Sort alphabetically
            print(f"Series found: {series}")
        else:
            print(f"Series folder does not exist: {SERIES_FOLDER}")
        
        return render_template('index.html', movies=movies, series=series)
    except Exception as e:
        print(f"Error accessing folders: {e}")
        return render_template('index.html', movies=[], series=[])

@app.route('/series/<series_name>')
def view_series(series_name):
    try:
        # Get the series folder path
        series_path = os.path.join(SERIES_FOLDER, series_name)
        if not os.path.exists(series_path):
            return "Series not found", 404
            
        # Get all episodes in the series folder
        episodes = get_video_files(series_path)
        episodes.sort(key=lambda x: int(''.join(filter(str.isdigit, x))) if any(c.isdigit() for c in x) else x)
        
        # Find the last played episode
        current_episode = None
        for episode in episodes:
            episode_path = f"series/{series_name}/{episode}"
            if episode_path in playback_data:
                current_episode = episode
                break
        
        # If no last played episode, use the first episode
        if not current_episode and episodes:
            current_episode = episodes[0]
        
        print(f"Found episodes for {series_name}: {episodes}")
        print(f"Current episode: {current_episode}")
        
        return render_template('series.html', 
                             series_name=series_name, 
                             episodes=episodes,
                             current_episode=current_episode)
    except Exception as e:
        print(f"Error getting episodes: {e}")
        return "Series not found", 404

@app.route('/series/<series_name>/<season>')
def view_season(series_name, season):
    try:
        season_path = os.path.join(SERIES_FOLDER, season)
        if not os.path.exists(season_path):
            print(f"Season path not found: {season_path}")
            return "Season not found", 404
        
        episodes = get_video_files(season_path)
        episodes.sort(key=lambda x: int(''.join(filter(str.isdigit, x))) if any(c.isdigit() for c in x) else x)
        print(f"Found episodes for {series_name} {season}: {episodes}")
        
        return render_template('season.html', series_name=series_name, season=season, episodes=episodes)
    except Exception as e:
        print(f"Error getting episodes: {e}")
        return "Error loading season", 500

@app.route('/watch/<path:filepath>')
def watch(filepath):
    try:
        if filepath.startswith('series/'):
            # For series, just join the path directly
            video_path = os.path.join(SERIES_FOLDER, filepath[7:])  # Remove 'series/' prefix
            if not os.path.exists(video_path):
                return "File not found", 404
                
            # Get the series name and episode for the template
            parts = filepath[7:].split('/')  # Remove 'series/' prefix and split
            series_name = parts[0]
            episode = parts[-1]
            
            return render_template('series.html', 
                                series_name=series_name,
                                episodes=get_video_files(os.path.dirname(video_path)),
                                current_episode=episode)
        else:
            # For movies
            video_path = os.path.join(MOVIE_FOLDER, filepath)
            if not os.path.exists(video_path):
                return "File not found", 404
                
            # For .ts files, convert them first
            if filepath.lower().endswith('.ts'):
                return redirect(url_for('convert', movie=filepath))
                
            return render_template('player.html', 
                                video_path=filepath,
                                video_name=os.path.splitext(os.path.basename(filepath))[0],
                                position=playback_data.get(filepath, {}).get('position', 0),
                                file_extension=os.path.splitext(filepath)[1].lower().replace('.', ''),
                                next_episode=None)
    except Exception as e:
        print(f"Error in watch route: {str(e)}")
        return str(e), 500

@app.route('/convert/<movie>')
def convert(movie):
    movie_path = os.path.join(MOVIE_FOLDER, movie)
    
    if not os.path.exists(movie_path):
        return "File not found", 404
    
    movie_name = os.path.splitext(movie)[0]
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    converted_file = os.path.join(temp_dir, f"{movie_name}.mp4")
    
    if os.path.exists(converted_file):
        position = request.args.get('position', '')
        return render_template('player.html', movie=f"{movie_name}.mp4", movie_name=movie_name, position=position, file_extension='mp4', is_converted=True)
    
    return render_template('convert.html', movie=movie, movie_name=movie_name, file_extension='ts')

@app.route('/convert_process/<movie>')
def convert_process(movie):
    movie_path = os.path.join(MOVIE_FOLDER, movie)
    
    if not os.path.exists(movie_path):
        return "File not found", 404
    
    movie_name = os.path.splitext(movie)[0]
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    converted_file = os.path.join(temp_dir, f"{movie_name}.mp4")
    
    try:
        # Convert the file using ffmpeg
        stream = ffmpeg.input(movie_path)
        stream = ffmpeg.output(stream, converted_file, acodec='copy', vcodec='copy')
        ffmpeg.run(stream, overwrite_output=True)
        
        return redirect(url_for('watch', filepath=f"{movie_name}.mp4"))
    except Exception as e:
        print(f"Error converting file: {e}")
        return f"Error converting file: {str(e)}", 500

@app.route('/save_position', methods=['POST'])
def save_position():
    data = request.json
    movie = data.get('movie')
    position = data.get('position')
    
    if movie and position is not None:
        playback_data[movie] = {
            'position': position,
            'timestamp': time.time()
        }
        save_playback_data(playback_data)
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Missing data'})

@app.route('/stream/<path:filepath>')
def stream(filepath):
    try:
        if filepath.startswith('series/'):
            # For series, just join the path directly
            video_path = os.path.join(SERIES_FOLDER, filepath[7:])  # Remove 'series/' prefix
            print(f"Streaming series video from: {video_path}")
        else:
            video_path = os.path.join(MOVIE_FOLDER, filepath)
            print(f"Streaming movie from: {video_path}")
        
        if not os.path.exists(video_path):
            print(f"File not found: {video_path}")
            return "File not found", 404
        
        mime_type, _ = mimetypes.guess_type(video_path)
        
        if filepath.lower().endswith('.ts'):
            mime_type = 'video/MP2T'
        elif mime_type is None:
            mime_type = 'video/mp4'
        
        file_size = os.path.getsize(video_path)
        range_header = request.headers.get('Range', None)
        
        if range_header:
            byte1, byte2 = 0, None
            match = re.search('bytes=(\d+)-(\d*)', range_header)
            groups = match.groups()
            
            if groups[0]: byte1 = int(groups[0])
            if groups[1]: byte2 = int(groups[1])
            
            if byte2 is None:
                byte2 = min(byte1 + 1024*1024, file_size - 1)
                
            length = byte2 - byte1 + 1
            
            with open(video_path, 'rb') as f:
                f.seek(byte1)
                data = f.read(length)
                
            rv = Response(data, 206, mimetype=mime_type, content_type=mime_type, direct_passthrough=True)
            rv.headers.add('Content-Range', f'bytes {byte1}-{byte2}/{file_size}')
            rv.headers.add('Accept-Ranges', 'bytes')
            rv.headers.add('Content-Length', str(length))
            rv.headers.add('Cache-Control', 'no-cache')
            return rv
        
        response = send_file(video_path, mimetype=mime_type)
        response.headers.add('Accept-Ranges', 'bytes')
        response.headers.add('Cache-Control', 'no-cache')
        return response
    except Exception as e:
        print(f"Error streaming file: {str(e)}")
        return str(e), 500

def get_album_cover(music_file):
    """Get album cover for a music file, using only the default cover"""
    # Always return the default cover
    return "album_covers/default.jpg"

def get_music_files():
    music_files = []
    for root, dirs, files in os.walk(MUSIC_FOLDER):
        for file in files:
            if file.lower().endswith(('.mp3', '.wav', '.m4a', '.flac')):
                file_path = os.path.join(root, file)
                try:
                    audio = EasyID3(file_path)
                    title = audio.get('title', [file])[0]
                    artist = audio.get('artist', ['Unknown Artist'])[0]
                except:
                    title = os.path.splitext(file)[0]
                    artist = 'Unknown Artist'
                
                # Create a relative path for the file
                rel_path = os.path.relpath(file_path, MUSIC_FOLDER)
                
                # Get album cover
                cover_path = get_album_cover(file_path)
                
                music_files.append({
                    'name': title,
                    'artist': artist,
                    'path': rel_path,
                    'filename': file,
                    'cover': cover_path
                })
    return music_files

@app.route('/music')
def music_player():
    music_files = get_music_files()
    return render_template('music.html', music_files=music_files)

@app.route('/stream_music/<path:filename>')
def stream_music(filename):
    try:
        # Construct the full file path
        file_path = os.path.join(MUSIC_FOLDER, filename)
        
        # Get the file's mime type
        mime_type = mimetypes.guess_type(file_path)[0]
        if mime_type is None:
            mime_type = 'application/octet-stream'
        
        # Stream the file
        return send_file(
            file_path,
            mimetype=mime_type,
            as_attachment=False
        )
    except Exception as e:
        return str(e), 500

@app.route('/download_music/<path:filename>')
def download_music(filename):
    try:
        # Construct the full file path
        file_path = os.path.join(MUSIC_FOLDER, filename)
        
        # Get the file's mime type
        mime_type = mimetypes.guess_type(file_path)[0]
        if mime_type is None:
            mime_type = 'application/octet-stream'
        
        # Send the file as an attachment
        return send_file(
            file_path,
            mimetype=mime_type,
            as_attachment=True,
            download_name=os.path.basename(file_path)
        )
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
