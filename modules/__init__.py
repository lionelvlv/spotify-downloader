"""Main modules for the Spotify to Opus converter."""

from .spotify_client import SpotifyClient, Track
from .search_engine import SearchEngine
from .downloader import Downloader, DownloadError
from .converter import Converter, ConversionError
from .tagger import Tagger, TaggingError
from .orchestrator import Orchestrator, ProcessResult

__all__ = [
    'SpotifyClient',
    'Track',
    'SearchEngine',
    'Downloader',
    'DownloadError',
    'Converter',
    'ConversionError',
    'Tagger',
    'TaggingError',
    'Orchestrator',
    'ProcessResult',
]
