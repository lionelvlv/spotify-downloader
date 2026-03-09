# Spotify to Opus Converter

Convert Spotify playlists to high-quality tagged `.opus` files. This tool uses Spotify only for metadata and obtains audio from public sources.

## Features

- **Clean Architecture**: Modular design with clear separation of concerns
- **Parallel Processing**: Download multiple tracks simultaneously
- **Robust Error Handling**: Retry logic, graceful failures, detailed logging
- **Smart Search**: Fuzzy matching with duration and artist verification
- **Rich Metadata**: Embeds title, artist, album, track number, cover art, ISRC
- **High Quality**: Opus format with configurable bitrate (96k-320k)
- **Resume Support**: Skips already converted files by default
- **Customizable Output**: Configurable folder structure and filenames

## Requirements

### System Requirements
- Python 3.9 or higher
- FFmpeg (must be installed separately)

### Installing FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

## Installation

1. **Clone or download this repository**

2. **Create a virtual environment (recommended):**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Get Spotify API credentials:**
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Create a new app
   - Copy your Client ID and Client Secret

5. **Create a `.env` file:**
```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
```
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

## Usage

### Basic Usage

Convert a playlist:
```bash
python main.py https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
```

Or use just the playlist ID:
```bash
python main.py 37i9dQZF1DXcBWIGoYBM5M
```

### Advanced Options

**Specify output directory:**
```bash
python main.py PLAYLIST_URL -o ~/Music/Spotify
```

**Change audio quality:**
```bash
python main.py PLAYLIST_URL --bitrate 160k
```

**Dry run (see what would be downloaded):**
```bash
python main.py PLAYLIST_URL --dry-run
```

**Process with more parallel jobs:**
```bash
python main.py PLAYLIST_URL -j 5
```

**Enable verbose logging:**
```bash
python main.py PLAYLIST_URL -v
```

**Save logs to file:**
```bash
python main.py PLAYLIST_URL --log-file conversion.log
```

**Re-process existing files:**
```bash
python main.py PLAYLIST_URL --no-skip
```

**Custom folder structure:**
```bash
python main.py PLAYLIST_URL --folder-structure "{artist}/{album}"
```

**Custom filename template:**
```bash
python main.py PLAYLIST_URL --filename-template "{track_num:02d} - {title}"
```

### Full Options

```
usage: main.py [-h] [-o OUTPUT] [--folder-structure FOLDER_STRUCTURE]
               [--filename-template FILENAME_TEMPLATE] [--bitrate BITRATE]
               [--sample-rate SAMPLE_RATE] [--compression-level {0-10}]
               [--dry-run] [--no-skip] [--no-cleanup] [-j JOBS]
               [--retry RETRY] [-v] [-q] [--log-file LOG_FILE]
               playlist

Output Options:
  -o, --output          Output directory (default: ./output)
  --folder-structure    Folder template (default: {artist}/{album})
  --filename-template   Filename template (default: {track_num:02d} - {title})

Audio Options:
  --bitrate            Opus bitrate (default: 128k)
  --sample-rate        Sample rate in Hz (default: 48000)
  --compression-level  Compression 0-10 (default: 10)

Behavior Options:
  --dry-run            Show what would be done
  --no-skip            Re-process existing files
  --no-cleanup         Keep temporary files

Performance Options:
  -j, --jobs           Concurrent downloads (default: 3)
  --retry              Retry attempts (default: 3)

Logging Options:
  -v, --verbose        Verbose output
  -q, --quiet          Minimal output
  --log-file          Write logs to file
```

## Project Structure

```
spotify-to-opus/
├── config.py              # Configuration management
├── main.py                # CLI entry point
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── modules/
│   ├── spotify_client.py  # Spotify API client
│   ├── search_engine.py   # Audio source search
│   ├── downloader.py      # Audio downloader
│   ├── converter.py       # FFmpeg wrapper
│   ├── tagger.py          # Metadata embedding
│   └── orchestrator.py    # Pipeline coordination
└── utils/
    ├── file_utils.py      # File operations
    ├── logging_utils.py   # Logging setup
    └── string_similarity.py # Matching algorithms
```

## How It Works

1. **Metadata Retrieval**: Fetches track information from Spotify API
2. **Audio Search**: Searches public sources (YouTube) for matching audio
3. **Smart Matching**: Ranks results by title, artist, and duration similarity
4. **Download**: Downloads best match using yt-dlp
5. **Conversion**: Converts to Opus format using FFmpeg
6. **Tagging**: Embeds metadata and cover art using Mutagen
7. **Organization**: Saves to structured folders

## Default Output Structure

```
output/
└── Playlist Name/
    └── Artist Name/
        └── Album Name/
            ├── 01 - Track Title.opus
            ├── 02 - Another Track.opus
            └── ...
```

## Troubleshooting

**"FFmpeg not found"**
- Ensure FFmpeg is installed and in your system PATH
- Test with: `ffmpeg -version`

**"Spotify API credentials not found"**
- Check your `.env` file exists and has correct values
- Ensure no spaces around the `=` sign

**"No matching audio source found"**
- The search algorithm couldn't find a good match
- Track might not be available on public platforms
- Try adjusting search parameters or using a different source

**Downloads are slow**
- Reduce concurrent jobs: `-j 1`
- Check your internet connection
- Some sources may throttle downloads

**Permission denied**
- Ensure you have write permissions to output directory
- Try running with appropriate permissions

## Privacy & Security

- Your Spotify credentials are only used for API access (read-only)
- No user data is collected or transmitted
- All processing happens locally on your machine
- Temporary files are cleaned up automatically (unless `--no-cleanup` is used)

## Configuration Files

### `.env` File Format
```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
OUTPUT_ROOT=/path/to/output  # Optional
OPUS_BITRATE=128k            # Optional
MAX_CONCURRENT_TRACKS=3      # Optional
```

## Acknowledgments

- [Spotipy](https://github.com/plamere/spotipy) - Spotify API wrapper
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Universal media downloader
- [Mutagen](https://github.com/quodlibet/mutagen) - Audio metadata library
- [FFmpeg](https://ffmpeg.org/) - Audio/video processing
