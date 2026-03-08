#!/bin/bash
# Quick setup script for Spotify to Opus Converter

set -e

echo "======================================"
echo "Spotify to Opus Converter - Setup"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
python --version || {
    echo "ERROR: Python 3 is not installed"
    exit 1
}

# Check FFmpeg
echo "Checking FFmpeg..."
ffmpeg -version > /dev/null 2>&1 || {
    echo "WARNING: FFmpeg is not installed"
    echo "Please install FFmpeg:"
    echo "  Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    echo "  Windows: Download from https://ffmpeg.org/"
    exit 1
}

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || {
    echo "Using Windows activation..."
    source venv/Scripts/activate
}

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create .env from example if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your Spotify credentials!"
    echo "Get credentials from: https://developer.spotify.com/dashboard"
fi

# Create output directory
mkdir -p output temp

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your Spotify API credentials"
echo "2. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo "3. Run the converter:"
echo "   python main.py YOUR_PLAYLIST_URL"
echo ""
echo "For help:"
echo "   python main.py --help"
echo ""
