"""
Spotify API client for fetching playlist metadata.
"""
import logging
from dataclasses import dataclass
from typing import List, Optional
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException


@dataclass
class Track:
    """Represents a track with all relevant metadata."""
    
    track_id: str
    title: str
    artists: List[str]
    album: str
    track_number: int
    disc_number: int
    duration_ms: int
    isrc: Optional[str]
    cover_url: Optional[str]
    release_year: Optional[str]
    explicit: bool
    
    def __str__(self) -> str:
        """String representation of track."""
        artist_str = ", ".join(self.artists)
        return f"{artist_str} - {self.title}"
    
    @property
    def duration_seconds(self) -> int:
        """Get duration in seconds."""
        return self.duration_ms // 1000


class SpotifyClient:
    """Client for interacting with Spotify API."""
    
    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize Spotify client.
        
        Args:
            client_id: Spotify application client ID
            client_secret: Spotify application client secret
        """
        self.logger = logging.getLogger(__name__)
        
        try:
            auth_manager = SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            self.logger.info("Spotify client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Spotify client: {e}")
            raise
    
    def get_playlist_info(self, playlist_id: str) -> dict:
        """
        Get basic playlist information.
        
        Args:
            playlist_id: Spotify playlist ID
            
        Returns:
            Dictionary with playlist name and owner info
        """
        try:
            playlist = self.sp.playlist(playlist_id, fields='name,owner.display_name,tracks.total')
            return {
                'name': playlist['name'],
                'owner': playlist['owner']['display_name'],
                'total_tracks': playlist['tracks']['total']
            }
        except SpotifyException as e:
            self.logger.error(f"Failed to fetch playlist info: {e}")
            raise
    
    def get_playlist_tracks(self, playlist_id: str) -> List[Track]:
        """
        Fetch all tracks from a playlist with pagination.
        
        Args:
            playlist_id: Spotify playlist ID
            
        Returns:
            List of Track objects
        """
        tracks = []
        offset = 0
        limit = 100  # Maximum allowed by Spotify API
        
        self.logger.info(f"Fetching tracks for playlist: {playlist_id}")
        
        try:
            while True:
                results = self.sp.playlist_items(
                    playlist_id,
                    offset=offset,
                    limit=limit,
                    additional_types=['track']
                )
                
                if not results or not results.get('items'):
                    break
                
                for item in results['items']:
                    track_data = item.get('track')
                    
                    # Skip if track is None (deleted/unavailable)
                    if not track_data:
                        self.logger.warning("Skipping unavailable track")
                        continue
                    
                    # Skip if track is not a track (could be episode, etc.)
                    if track_data.get('type') != 'track':
                        self.logger.debug(f"Skipping non-track item: {track_data.get('type')}")
                        continue
                    
                    try:
                        track = self._parse_track(track_data)
                        tracks.append(track)
                    except Exception as e:
                        self.logger.warning(f"Failed to parse track: {e}")
                        continue
                
                # Check if there are more tracks
                if not results.get('next'):
                    break
                
                offset += limit
                self.logger.debug(f"Fetched {len(tracks)} tracks so far...")
            
            self.logger.info(f"Successfully fetched {len(tracks)} tracks")
            return tracks
            
        except SpotifyException as e:
            self.logger.error(f"Failed to fetch playlist tracks: {e}")
            raise
    
    def _parse_track(self, track_data: dict) -> Track:
        """
        Parse Spotify track data into Track object.
        
        Args:
            track_data: Raw track data from Spotify API
            
        Returns:
            Track object
        """
        # Extract artists
        artists = [artist['name'] for artist in track_data.get('artists', [])]
        
        # Extract album info
        album_data = track_data.get('album', {})
        album = album_data.get('name', 'Unknown Album')
        
        # Extract cover art (prefer largest image)
        images = album_data.get('images', [])
        cover_url = images[0]['url'] if images else None
        
        # Extract release year
        release_date = album_data.get('release_date', '')
        release_year = release_date[:4] if len(release_date) >= 4 else None
        
        # Extract ISRC
        external_ids = track_data.get('external_ids', {})
        isrc = external_ids.get('isrc')
        
        return Track(
            track_id=track_data['id'],
            title=track_data['name'],
            artists=artists,
            album=album,
            track_number=track_data.get('track_number', 0),
            disc_number=track_data.get('disc_number', 1),
            duration_ms=track_data.get('duration_ms', 0),
            isrc=isrc,
            cover_url=cover_url,
            release_year=release_year,
            explicit=track_data.get('explicit', False)
        )
    
    @staticmethod
    def extract_playlist_id(url_or_id: str) -> str:
        """
        Extract playlist ID from URL or return ID if already extracted.
        
        Args:
            url_or_id: Spotify playlist URL or ID
            
        Returns:
            Playlist ID
        """
        # If it's already just an ID
        if '/' not in url_or_id and '?' not in url_or_id:
            return url_or_id
        
        # Extract from URL
        # Format: https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=...
        parts = url_or_id.split('/')
        
        for i, part in enumerate(parts):
            if part == 'playlist' and i + 1 < len(parts):
                playlist_id = parts[i + 1]
                # Remove query parameters
                playlist_id = playlist_id.split('?')[0]
                return playlist_id
        
        # If we can't extract it, assume it's already an ID
        return url_or_id.split('?')[0]
