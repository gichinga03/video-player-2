# Video & Music Player

A modern web application for streaming videos and music with a Netflix-inspired UI. This application allows you to browse, play, and download your local media files through a beautiful web interface.

![Screenshot](https://via.placeholder.com/800x450.png?text=Video+and+Music+Player)

## Features

### Video Player
- Browse and play local video files
- Netflix-style UI with movie and series browsing
- Video playback with position memory
- Series organization with seasons and episodes
- Video conversion support for different formats

### Music Player
- Browse and play local music files
- Spotify-inspired UI with album artwork
- Music playback with controls
- Download functionality for offline listening
- Consistent default album artwork for all tracks

## Screenshots

### Video Library
![Video Library](https://via.placeholder.com/800x450.png?text=Video+Library)

### Music Player
![Music Player](https://via.placeholder.com/800x450.png?text=Music+Player)

## Installation

### Prerequisites
- Python 3.8 or higher
- FFmpeg (for video conversion)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/video-player-2.git
   cd video-player-2
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv myvenv
   # On Windows
   .\myvenv\Scripts\activate
   # On macOS/Linux
   source myvenv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory with the following content:
   ```
   MOVIE=C:\path\to\your\movies
   SERIES=C:\path\to\your\series
   ```

5. Run the application:
   ```
   python server.py
   ```

6. Open your browser and navigate to `http://localhost:5000`

## Configuration

### Media Folders
- Set your movie folder path in the `.env` file
- Set your series folder path in the `.env` file
- Music files are read from `C:\Users\gichi\Music` by default (configurable in `server.py`)

### Album Artwork
- A single default album artwork is used for all music tracks
- The default artwork is stored in the `static/album_covers` directory
- No internet requests are made for album artwork

## Usage

### Video Library
- Browse movies and series on the home page
- Click on a movie to play it
- Navigate through series and seasons
- Your playback position is automatically saved

### Music Player
- Access the music player from the navigation bar
- Browse your music collection
- Play music directly in the browser
- Download tracks for offline listening

## Technologies Used

- **Backend**: Flask, Python
- **Frontend**: HTML, CSS, JavaScript
- **Media Processing**: FFmpeg, Mutagen
- **UI Libraries**: Bootstrap, Font Awesome
- **Image Processing**: Pillow

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by Netflix and Spotify UI designs
- Uses FFmpeg for video processing
- Uses Mutagen for audio metadata extraction

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 