"""
Audio downloader using yt-dlp with retry logic.
"""
import logging
from pathlib import Path
from typing import Optional
import yt_dlp
import time


class DownloadError(Exception):
    """Custom exception for download failures."""
    pass


class Downloader:
    """Download audio from public sources."""
    
    def __init__(
        self,
        temp_dir: Path,
        timeout: int = 120,
        retry_attempts: int = 3,
        retry_delay: int = 2
    ):
        """
        Initialize downloader.
        
        Args:
            temp_dir: Directory for temporary downloads
            timeout: Socket timeout in seconds
            retry_attempts: Number of retry attempts on failure
            retry_delay: Delay between retries in seconds
        """
        self.logger = logging.getLogger(__name__)
        self.temp_dir = temp_dir
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        
        # Ensure temp directory exists
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def download(self, url: str, track_id: str) -> Path:
        """
        Download audio from URL with retry logic.
        
        Args:
            url: Source URL to download from
            track_id: Unique identifier for the track (used in filename)
            
        Returns:
            Path to downloaded audio file
            
        Raises:
            DownloadError: If download fails after all retries
        """
        for attempt in range(1, self.retry_attempts + 1):
            try:
                self.logger.debug(f"Download attempt {attempt}/{self.retry_attempts} for {track_id}")
                return self._download_once(url, track_id)
                
            except Exception as e:
                if attempt < self.retry_attempts:
                    self.logger.warning(
                        f"Download attempt {attempt} failed: {e}. "
                        f"Retrying in {self.retry_delay}s..."
                    )
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error(f"All download attempts failed for {track_id}")
                    raise DownloadError(f"Failed to download after {self.retry_attempts} attempts: {e}")
    
    def _download_once(self, url: str, track_id: str) -> Path:
        """
        Perform a single download attempt.
        
        Args:
            url: Source URL
            track_id: Track identifier
            
        Returns:
            Path to downloaded file
        """
        # Output template - let yt-dlp add the extension
        output_template = str(self.temp_dir / f"{track_id}_download.%(ext)s")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': self.timeout,
            'retries': 3,
            'fragment_retries': 3,
            # Post-processing to ensure we get audio
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'best',
                'preferredquality': '0',  # Best quality
            }],
            # Keep the video file for now (we'll convert it ourselves)
            'keepvideo': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Find the downloaded file
            # yt-dlp might have added different extensions
            pattern = f"{track_id}_download.*"
            files = list(self.temp_dir.glob(pattern))
            
            if not files:
                raise DownloadError("No file found after download")
            
            # Return the first match (should only be one)
            downloaded_file = files[0]
            
            # Verify file exists and has content
            if not downloaded_file.exists():
                raise DownloadError(f"Downloaded file doesn't exist: {downloaded_file}")
            
            if downloaded_file.stat().st_size == 0:
                downloaded_file.unlink()
                raise DownloadError("Downloaded file is empty")
            
            self.logger.debug(f"Successfully downloaded to: {downloaded_file}")
            return downloaded_file
            
        except Exception as e:
            # Clean up any partial downloads
            for file in self.temp_dir.glob(f"{track_id}_download.*"):
                try:
                    file.unlink()
                except Exception:
                    pass
            raise
    
    def cleanup(self, track_id: str):
        """
        Clean up temporary files for a specific track.
        
        Args:
            track_id: Track identifier
        """
        pattern = f"{track_id}_*"
        for file in self.temp_dir.glob(pattern):
            try:
                file.unlink()
                self.logger.debug(f"Cleaned up: {file}")
            except Exception as e:
                self.logger.warning(f"Failed to clean up {file}: {e}")
