"""
Orchestrator to coordinate the entire conversion pipeline.
"""
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from dataclasses import dataclass
import time

from .spotify_client import SpotifyClient, Track
from .search_engine import SearchEngine
from .downloader import Downloader, DownloadError
from .converter import Converter, ConversionError
from .tagger import Tagger, TaggingError
from utils import (
    build_output_path,
    ensure_directory,
    cleanup_temp_files,
    ProgressLogger,
)


@dataclass
class ProcessResult:
    """Result of processing a single track."""
    track: Track
    success: bool
    output_path: Path = None
    error: str = None
    duration: float = 0.0


class Orchestrator:
    """Coordinate the entire conversion pipeline."""
    
    def __init__(self, config):
        """
        Initialize orchestrator with configuration.
        
        Args:
            config: Config object with all settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize all modules
        self.spotify = SpotifyClient(
            config.spotify_client_id,
            config.spotify_client_secret
        )
        
        self.search = SearchEngine(
            timeout=config.search_timeout,
            max_results=config.max_search_results
        )
        
        self.downloader = Downloader(
            temp_dir=config.temp_root,
            timeout=config.download_timeout,
            retry_attempts=config.retry_attempts,
            retry_delay=config.retry_delay
        )
        
        self.converter = Converter(
            bitrate=config.opus_bitrate,
            sample_rate=config.opus_sample_rate,
            compression_level=config.compression_level
        )
        
        self.tagger = Tagger(
            download_covers=True
        )
        
        # Statistics
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'total_time': 0.0
        }
    
    def run(self, playlist_url: str) -> Dict[str, Any]:
        """
        Run the complete conversion pipeline.
        
        Args:
            playlist_url: Spotify playlist URL or ID
            
        Returns:
            Dictionary with conversion statistics
        """
        start_time = time.time()
        
        try:
            # Extract playlist ID
            playlist_id = SpotifyClient.extract_playlist_id(playlist_url)
            self.logger.info(f"Processing playlist ID: {playlist_id}")
            
            # Get playlist info
            playlist_info = self.spotify.get_playlist_info(playlist_id)
            self.logger.info(
                f"Playlist: '{playlist_info['name']}' "
                f"by {playlist_info['owner']} "
                f"({playlist_info['total_tracks']} tracks)"
            )
            
            # Get all tracks
            tracks = self.spotify.get_playlist_tracks(playlist_id)
            
            if not tracks:
                self.logger.warning("No tracks found in playlist")
                return self.stats
            
            self.stats['total'] = len(tracks)
            
            # Create output directory based on playlist name
            from utils.file_utils import sanitize_filename
            playlist_dir = sanitize_filename(playlist_info['name'])
            output_base = self.config.output_root / playlist_dir
            ensure_directory(output_base)
            
            self.logger.info(f"Output directory: {output_base}")
            
            # Dry run - just show what would be done
            if self.config.dry_run:
                self._dry_run(tracks, output_base)
                return self.stats
            
            # Process tracks
            results = self._process_tracks(tracks, output_base)
            
            # Log summary
            self._log_summary(results)
            
            # Cleanup temp files
            if self.config.clean_temp_on_exit:
                cleaned = cleanup_temp_files(self.config.temp_root)
                self.logger.info(f"Cleaned up {cleaned} temporary files")
            
            self.stats['total_time'] = time.time() - start_time
            return self.stats
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise
    
    def _dry_run(self, tracks: List[Track], output_base: Path):
        """
        Perform a dry run showing what would be processed.
        
        Args:
            tracks: List of tracks
            output_base: Output directory
        """
        self.logger.info("=== DRY RUN - No files will be downloaded ===")
        
        for i, track in enumerate(tracks, 1):
            output_path = build_output_path(
                output_base,
                track,
                self.config.folder_structure,
                self.config.filename_template
            )
            
            status = "EXISTS" if output_path.exists() else "WOULD CREATE"
            self.logger.info(f"[{i}/{len(tracks)}] {status}: {track} -> {output_path}")
        
        self.logger.info("=== DRY RUN COMPLETE ===")
    
    def _process_tracks(self, tracks: List[Track], output_base: Path) -> List[ProcessResult]:
        """
        Process all tracks with parallel execution.
        
        Args:
            tracks: List of tracks to process
            output_base: Base output directory
            
        Returns:
            List of ProcessResult objects
        """
        results = []
        progress = ProgressLogger(len(tracks), self.logger, "Processing")
        
        # Use thread pool for parallel processing
        with ThreadPoolExecutor(max_workers=self.config.max_concurrent_tracks) as executor:
            # Submit all tasks
            future_to_track = {
                executor.submit(self._process_single_track, track, output_base): track
                for track in tracks
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_track):
                track = future_to_track[future]
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result.success:
                        self.stats['success'] += 1
                        progress.increment(success=True)
                        self.logger.info(f"✓ {track.title} -> {result.output_path.name}")
                    else:
                        self.stats['failed'] += 1
                        progress.increment(success=False)
                        self.logger.error(f"✗ {track.title}: {result.error}")
                    
                except Exception as e:
                    self.stats['failed'] += 1
                    progress.increment(success=False)
                    self.logger.error(f"✗ {track.title}: Unexpected error: {e}")
                    results.append(ProcessResult(
                        track=track,
                        success=False,
                        error=str(e)
                    ))
        
        return results
    
    def _process_single_track(self, track: Track, output_base: Path) -> ProcessResult:
        """
        Process a single track through the entire pipeline.
        
        Args:
            track: Track to process
            output_base: Base output directory
            
        Returns:
            ProcessResult object
        """
        start_time = time.time()
        
        try:
            # Determine output path
            output_path = build_output_path(
                output_base,
                track,
                self.config.folder_structure,
                self.config.filename_template
            )
            
            # Skip if already exists
            if self.config.skip_existing and output_path.exists():
                self.logger.debug(f"Skipping existing file: {output_path}")
                self.stats['skipped'] += 1
                return ProcessResult(
                    track=track,
                    success=True,
                    output_path=output_path,
                    duration=time.time() - start_time
                )
            
            # 1. Search for audio source
            match = self.search.search_best_match(track)
            if not match:
                return ProcessResult(
                    track=track,
                    success=False,
                    error="No matching audio source found"
                )
            
            # 2. Download audio
            temp_audio = self.downloader.download(match['webpage_url'], track.track_id)
            
            # 3. Convert to Opus
            temp_opus = self.config.temp_root / f"{track.track_id}.opus"
            self.converter.to_opus(temp_audio, temp_opus)
            
            # 4. Tag with metadata
            self.tagger.tag(temp_opus, track, track.cover_url)
            
            # 5. Move to final location
            ensure_directory(output_path.parent)
            temp_opus.rename(output_path)
            
            # 6. Cleanup temporary files
            self.downloader.cleanup(track.track_id)
            
            return ProcessResult(
                track=track,
                success=True,
                output_path=output_path,
                duration=time.time() - start_time
            )
            
        except (DownloadError, ConversionError, TaggingError) as e:
            # Clean up any partial files
            self.downloader.cleanup(track.track_id)
            return ProcessResult(
                track=track,
                success=False,
                error=str(e),
                duration=time.time() - start_time
            )
            
        except Exception as e:
            # Unexpected error - clean up
            self.downloader.cleanup(track.track_id)
            return ProcessResult(
                track=track,
                success=False,
                error=f"Unexpected error: {e}",
                duration=time.time() - start_time
            )
    
    def _log_summary(self, results: List[ProcessResult]):
        """
        Log summary of processing results.
        
        Args:
            results: List of ProcessResult objects
        """
        self.logger.info("\n" + "=" * 70)
        self.logger.info("CONVERSION SUMMARY")
        self.logger.info("=" * 70)
        self.logger.info(f"Total tracks: {self.stats['total']}")
        self.logger.info(f"Successful: {self.stats['success']}")
        self.logger.info(f"Failed: {self.stats['failed']}")
        self.logger.info(f"Skipped: {self.stats['skipped']}")
        
        # Average processing time
        successful_results = [r for r in results if r.success and r.duration > 0]
        if successful_results:
            avg_time = sum(r.duration for r in successful_results) / len(successful_results)
            self.logger.info(f"Average time per track: {avg_time:.1f}s")
        
        # List failures
        if self.stats['failed'] > 0:
            self.logger.info("\nFailed tracks:")
            for result in results:
                if not result.success:
                    self.logger.info(f"  - {result.track.title}: {result.error}")
        
        self.logger.info("=" * 70 + "\n")
