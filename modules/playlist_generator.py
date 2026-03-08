"""
Playlist generator for creating VLC and M3U format playlists.
"""
import logging
from pathlib import Path
from typing import List
from datetime import datetime


class PlaylistGenerator:
    """Generate playlist files in various formats."""
    
    def __init__(self):
        """Initialize playlist generator."""
        self.logger = logging.getLogger(__name__)
    
    def create_m3u(
        self,
        tracks: List[Path],
        output_path: Path,
        playlist_name: str = "Spotify Playlist"
    ) -> Path:
        """
        Create an M3U playlist file.
        
        Args:
            tracks: List of Path objects pointing to audio files
            output_path: Where to save the playlist file
            playlist_name: Name of the playlist
            
        Returns:
            Path to created playlist file
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # M3U header
                f.write("#EXTM3U\n")
                f.write(f"# Playlist: {playlist_name}\n")
                f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Tracks: {len(tracks)}\n\n")
                
                for track_path in tracks:
                    if track_path.exists():
                        # Get track duration if available (using mutagen)
                        duration = self._get_track_duration(track_path)
                        
                        # Get track info from filename/tags
                        title = self._extract_title(track_path)
                        
                        # Write EXTINF line (duration, artist - title)
                        f.write(f"#EXTINF:{duration},{title}\n")
                        
                        # Write file path (absolute)
                        f.write(f"{track_path.absolute()}\n")
            
            self.logger.info(f"Created M3U playlist: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to create M3U playlist: {e}")
            raise
    
    def create_m3u8(
        self,
        tracks: List[Path],
        output_path: Path,
        playlist_name: str = "Spotify Playlist"
    ) -> Path:
        """
        Create an M3U8 playlist file (UTF-8 encoded M3U).
        
        Args:
            tracks: List of Path objects pointing to audio files
            output_path: Where to save the playlist file
            playlist_name: Name of the playlist
            
        Returns:
            Path to created playlist file
        """
        # M3U8 is just UTF-8 encoded M3U, so we use the same method
        return self.create_m3u(tracks, output_path, playlist_name)
    
    def create_xspf(
        self,
        tracks: List[Path],
        output_path: Path,
        playlist_name: str = "Spotify Playlist"
    ) -> Path:
        """
        Create an XSPF (XML Shareable Playlist Format) file.
        VLC's native format.
        
        Args:
            tracks: List of Path objects pointing to audio files
            output_path: Where to save the playlist file
            playlist_name: Name of the playlist
            
        Returns:
            Path to created playlist file
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # XSPF header
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<playlist version="1" xmlns="http://xspf.org/ns/0/">\n')
                f.write(f'  <title>{self._escape_xml(playlist_name)}</title>\n')
                f.write(f'  <creator>Spotify to Opus Converter</creator>\n')
                f.write(f'  <date>{datetime.now().isoformat()}</date>\n')
                f.write('  <trackList>\n')
                
                for i, track_path in enumerate(tracks, 1):
                    if track_path.exists():
                        # Get metadata
                        title, artist, album, duration = self._get_track_metadata(track_path)
                        
                        f.write('    <track>\n')
                        f.write(f'      <location>file://{track_path.absolute().as_posix()}</location>\n')
                        if title:
                            f.write(f'      <title>{self._escape_xml(title)}</title>\n')
                        if artist:
                            f.write(f'      <creator>{self._escape_xml(artist)}</creator>\n')
                        if album:
                            f.write(f'      <album>{self._escape_xml(album)}</album>\n')
                        if duration:
                            f.write(f'      <duration>{duration * 1000}</duration>\n')  # milliseconds
                        f.write(f'      <trackNum>{i}</trackNum>\n')
                        f.write('    </track>\n')
                
                f.write('  </trackList>\n')
                f.write('</playlist>\n')
            
            self.logger.info(f"Created XSPF playlist: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to create XSPF playlist: {e}")
            raise
    
    def create_pls(
        self,
        tracks: List[Path],
        output_path: Path,
        playlist_name: str = "Spotify Playlist"
    ) -> Path:
        """
        Create a PLS playlist file.
        
        Args:
            tracks: List of Path objects pointing to audio files
            output_path: Where to save the playlist file
            playlist_name: Name of the playlist
            
        Returns:
            Path to created playlist file
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('[playlist]\n')
                f.write(f'X-GNOME-Title={playlist_name}\n\n')
                
                for i, track_path in enumerate(tracks, 1):
                    if track_path.exists():
                        title = self._extract_title(track_path)
                        duration = self._get_track_duration(track_path)
                        
                        f.write(f'File{i}={track_path.absolute()}\n')
                        f.write(f'Title{i}={title}\n')
                        f.write(f'Length{i}={duration}\n\n')
                
                f.write(f'NumberOfEntries={len(tracks)}\n')
                f.write('Version=2\n')
            
            self.logger.info(f"Created PLS playlist: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to create PLS playlist: {e}")
            raise
    
    def _get_track_duration(self, track_path: Path) -> int:
        """
        Get track duration in seconds.
        
        Args:
            track_path: Path to audio file
            
        Returns:
            Duration in seconds, or -1 if unavailable
        """
        try:
            from mutagen import File
            audio = File(track_path)
            if audio and audio.info:
                return int(audio.info.length)
        except Exception:
            pass
        return -1
    
    def _get_track_metadata(self, track_path: Path) -> tuple:
        """
        Get track metadata from file.
        
        Args:
            track_path: Path to audio file
            
        Returns:
            Tuple of (title, artist, album, duration)
        """
        try:
            from mutagen import File
            audio = File(track_path)
            
            title = None
            artist = None
            album = None
            duration = None
            
            if audio:
                # Get duration
                if audio.info:
                    duration = int(audio.info.length)
                
                # Get tags
                if audio.tags:
                    # Try different tag formats
                    title = (audio.tags.get('TITLE') or 
                            audio.tags.get('title') or 
                            [track_path.stem])[0]
                    
                    artist = (audio.tags.get('ARTIST') or 
                             audio.tags.get('artist') or 
                             [None])[0]
                    
                    album = (audio.tags.get('ALBUM') or 
                            audio.tags.get('album') or 
                            [None])[0]
            
            # Fallback to filename
            if not title:
                title = track_path.stem
            
            return (title, artist, album, duration)
            
        except Exception as e:
            self.logger.debug(f"Failed to read metadata from {track_path}: {e}")
            return (track_path.stem, None, None, None)
    
    def _extract_title(self, track_path: Path) -> str:
        """
        Extract title from track file.
        
        Args:
            track_path: Path to audio file
            
        Returns:
            Track title
        """
        title, artist, _, _ = self._get_track_metadata(track_path)
        
        if artist:
            return f"{artist} - {title}"
        return title
    
    def _escape_xml(self, text: str) -> str:
        """
        Escape XML special characters.
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text
        """
        if not text:
            return ""
        
        text = str(text)
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')
        return text
