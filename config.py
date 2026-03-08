"""
Configuration management for Spotify to Opus converter.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import os


@dataclass
class Config:
    """Application configuration with sensible defaults."""
    
    # Spotify API credentials
    spotify_client_id: str
    spotify_client_secret: str
    
    # Directory paths
    output_root: Path = field(default_factory=lambda: Path("./output"))
    temp_root: Path = field(default_factory=lambda: Path("./temp"))
    
    # Audio conversion settings
    opus_bitrate: str = "128k"
    opus_sample_rate: int = 48000
    compression_level: int = 10
    
    # Search and download settings
    search_timeout: int = 30
    download_timeout: int = 120
    max_search_results: int = 10
    
    # Performance settings
    max_concurrent_tracks: int = 3
    retry_attempts: int = 3
    retry_delay: int = 2
    
    # Application behavior
    dry_run: bool = False
    verbose: bool = False
    skip_existing: bool = True
    clean_temp_on_exit: bool = True
    
    # File naming
    filename_template: str = "{track_num:02d} - {title}"
    folder_structure: str = "{artist}/{album}"
    
    def __post_init__(self):
        """Validate and initialize configuration."""
        # Ensure paths are Path objects
        self.output_root = Path(self.output_root)
        self.temp_root = Path(self.temp_root)
        
        # Validate credentials
        if not self.spotify_client_id or not self.spotify_client_secret:
            raise ValueError("Spotify credentials are required")
        
        # Validate numeric settings
        if self.max_concurrent_tracks < 1:
            raise ValueError("max_concurrent_tracks must be at least 1")
        
        if self.compression_level < 0 or self.compression_level > 10:
            raise ValueError("compression_level must be between 0 and 10")
        
        # Create directories if they don't exist
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.temp_root.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_env(cls, **overrides) -> "Config":
        """Load configuration from environment variables with optional overrides."""
        config_dict = {
            "spotify_client_id": os.getenv("SPOTIFY_CLIENT_ID", ""),
            "spotify_client_secret": os.getenv("SPOTIFY_CLIENT_SECRET", ""),
        }
        
        # Optional environment overrides
        if os.getenv("OUTPUT_ROOT"):
            config_dict["output_root"] = Path(os.getenv("OUTPUT_ROOT"))
        if os.getenv("OPUS_BITRATE"):
            config_dict["opus_bitrate"] = os.getenv("OPUS_BITRATE")
        if os.getenv("MAX_CONCURRENT_TRACKS"):
            config_dict["max_concurrent_tracks"] = int(os.getenv("MAX_CONCURRENT_TRACKS"))
        
        # Apply any programmatic overrides
        config_dict.update(overrides)
        
        return cls(**config_dict)
