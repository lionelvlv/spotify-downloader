"""
Metadata tagger for embedding information in Opus files.
"""
import logging
from pathlib import Path
from typing import Optional
import requests
from mutagen.oggopus import OggOpus
from mutagen.flac import Picture
import base64
import io


class TaggingError(Exception):
    """Custom exception for tagging failures."""
    pass


class Tagger:
    """Embed metadata into Opus audio files."""
    
    def __init__(self, download_covers: bool = True, cover_timeout: int = 10):
        """
        Initialize tagger.
        
        Args:
            download_covers: Whether to download and embed cover art
            cover_timeout: Timeout for cover art downloads in seconds
        """
        self.logger = logging.getLogger(__name__)
        self.download_covers = download_covers
        self.cover_timeout = cover_timeout
    
    def tag(self, opus_path: Path, track, cover_url: Optional[str] = None) -> Path:
        """
        Embed metadata into Opus file.
        
        Args:
            opus_path: Path to Opus file
            track: Track object with metadata
            cover_url: Optional URL to cover art image
            
        Returns:
            Path to tagged file
            
        Raises:
            TaggingError: If tagging fails
        """
        if not opus_path.exists():
            raise TaggingError(f"File not found: {opus_path}")
        
        try:
            # Load Opus file
            audio = OggOpus(opus_path)
            
            # Clear existing tags
            audio.clear()
            
            # Basic metadata
            audio['TITLE'] = track.title
            audio['ALBUM'] = track.album
            
            # Artists - store as semicolon-separated list
            if track.artists:
                audio['ARTIST'] = '; '.join(track.artists)
                # Also store first artist separately
                audio['ALBUMARTIST'] = track.artists[0]
            
            # Track and disc numbers
            if track.track_number:
                audio['TRACKNUMBER'] = str(track.track_number)
            
            if track.disc_number:
                audio['DISCNUMBER'] = str(track.disc_number)
            
            # Date/year
            if track.release_year:
                audio['DATE'] = track.release_year
                audio['YEAR'] = track.release_year
            
            # ISRC (International Standard Recording Code)
            if track.isrc:
                audio['ISRC'] = track.isrc
            
            # Additional metadata
            if track.explicit:
                audio['ITUNESADVISORY'] = '1'  # Explicit content
            
            # Embed cover art
            if self.download_covers and cover_url:
                try:
                    cover_data = self._download_cover(cover_url)
                    if cover_data:
                        self._embed_cover(audio, cover_data)
                except Exception as e:
                    self.logger.warning(f"Failed to embed cover art: {e}")
            
            # Save tags
            audio.save()
            self.logger.debug(f"Successfully tagged: {opus_path}")
            
            return opus_path
            
        except Exception as e:
            raise TaggingError(f"Failed to tag file: {e}")
    
    def _download_cover(self, url: str) -> Optional[bytes]:
        """
        Download cover art from URL.
        
        Args:
            url: Cover art URL
            
        Returns:
            Image bytes or None on failure
        """
        try:
            response = requests.get(
                url,
                timeout=self.cover_timeout,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            if response.status_code == 200:
                return response.content
            else:
                self.logger.warning(f"Cover download failed with status: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.warning(f"Failed to download cover: {e}")
            return None
    
    def _embed_cover(self, audio: OggOpus, image_data: bytes):
        """
        Embed cover art in Opus file.
        
        Args:
            audio: OggOpus object
            image_data: Image bytes
        """
        # Create Picture object
        picture = Picture()
        picture.data = image_data
        picture.type = 3  # Front cover
        
        # Detect MIME type from image data
        if image_data[:4] == b'\xff\xd8\xff\xe0' or image_data[:4] == b'\xff\xd8\xff\xe1':
            picture.mime = 'image/jpeg'
        elif image_data[:8] == b'\x89PNG\r\n\x1a\n':
            picture.mime = 'image/png'
        else:
            picture.mime = 'image/jpeg'  # Default to JPEG
        
        # Add description
        picture.desc = 'Front Cover'
        
        # Encode and add to file
        # Opus uses metadata_block_picture field
        picture_data = picture.write()
        encoded_data = base64.b64encode(picture_data).decode('ascii')
        audio['metadata_block_picture'] = [encoded_data]
    
    def verify_tags(self, opus_path: Path) -> dict:
        """
        Verify and read tags from an Opus file.
        
        Args:
            opus_path: Path to Opus file
            
        Returns:
            Dictionary of tags
        """
        try:
            audio = OggOpus(opus_path)
            tags = {}
            
            for key, value in audio.items():
                if isinstance(value, list) and len(value) == 1:
                    tags[key] = value[0]
                else:
                    tags[key] = value
            
            return tags
            
        except Exception as e:
            self.logger.error(f"Failed to read tags: {e}")
            return {}
