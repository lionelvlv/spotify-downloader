#!/usr/bin/env python
"""
Spotify to Opus Converter
Convert Spotify playlists to tagged Opus audio files.
"""
import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

from config import Config
from modules import Orchestrator
from utils import setup_logging


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert Spotify playlists to Opus audio files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
  %(prog)s 37i9dQZF1DXcBWIGoYBM5M -o ~/Music/Spotify
  %(prog)s PLAYLIST_ID --bitrate 160k --dry-run
  %(prog)s PLAYLIST_URL -v --no-skip

Environment Variables:
  SPOTIFY_CLIENT_ID       Spotify API client ID (required)
  SPOTIFY_CLIENT_SECRET   Spotify API client secret (required)
  OUTPUT_ROOT            Default output directory
  OPUS_BITRATE           Default Opus bitrate
        """
    )
    
    # Required arguments
    parser.add_argument(
        'playlist',
        help='Spotify playlist URL or ID'
    )
    
    # Output options
    output_group = parser.add_argument_group('output options')
    output_group.add_argument(
        '-o', '--output',
        type=Path,
        default=Path('./output'),
        help='Output directory (default: ./output)'
    )
    output_group.add_argument(
        '--folder-structure',
        default='{artist}/{album}',
        help='Folder structure template (default: {artist}/{album})'
    )
    output_group.add_argument(
        '--filename-template',
        default='{track_num:02d} - {title}',
        help='Filename template (default: {track_num:02d} - {title})'
    )
    
    # Audio options
    audio_group = parser.add_argument_group('audio options')
    audio_group.add_argument(
        '--bitrate',
        default='128k',
        help='Opus bitrate: 96k, 128k, 160k, etc. (default: 128k)'
    )
    audio_group.add_argument(
        '--sample-rate',
        type=int,
        default=48000,
        help='Sample rate in Hz (default: 48000)'
    )
    audio_group.add_argument(
        '--compression-level',
        type=int,
        choices=range(0, 11),
        default=10,
        help='Compression level 0-10 (default: 10)'
    )
    
    # Behavior options
    behavior_group = parser.add_argument_group('behavior options')
    behavior_group.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without downloading'
    )
    behavior_group.add_argument(
        '--no-skip',
        action='store_true',
        help='Re-process existing files'
    )
    behavior_group.add_argument(
        '--no-cleanup',
        action='store_true',
        help='Keep temporary files'
    )
    
    # Performance options
    perf_group = parser.add_argument_group('performance options')
    perf_group.add_argument(
        '-j', '--jobs',
        type=int,
        default=3,
        help='Number of concurrent downloads (default: 3)'
    )
    perf_group.add_argument(
        '--retry',
        type=int,
        default=3,
        help='Number of retry attempts (default: 3)'
    )
    
    # Logging options
    log_group = parser.add_argument_group('logging options')
    log_group.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output (DEBUG level)'
    )
    log_group.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Minimal output (WARNING level only)'
    )
    log_group.add_argument(
        '--log-file',
        type=Path,
        help='Write logs to file'
    )
    
    return parser.parse_args()


def validate_credentials():
    """Validate that Spotify credentials are set."""
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("ERROR: Spotify API credentials not found!", file=sys.stderr)
        print("\nPlease set the following environment variables:", file=sys.stderr)
        print("  SPOTIFY_CLIENT_ID", file=sys.stderr)
        print("  SPOTIFY_CLIENT_SECRET", file=sys.stderr)
        print("\nYou can get credentials at: https://developer.spotify.com/dashboard", file=sys.stderr)
        print("\nOr create a .env file with:", file=sys.stderr)
        print("  SPOTIFY_CLIENT_ID=your_client_id", file=sys.stderr)
        print("  SPOTIFY_CLIENT_SECRET=your_client_secret", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Parse arguments
    args = parse_args()
    
    # Validate credentials
    validate_credentials()
    
    # Setup logging
    log_level = 'INFO'
    if args.verbose:
        log_level = 'DEBUG'
    elif args.quiet:
        log_level = 'WARNING'
    
    # Determine verbose flag for Config
    verbose = args.verbose
    
    logger = setup_logging(
        verbose=verbose,
        log_file=args.log_file
    )
    
    # Create configuration
    try:
        config = Config.from_env(
            output_root=args.output,
            opus_bitrate=args.bitrate,
            opus_sample_rate=args.sample_rate,
            compression_level=args.compression_level,
            max_concurrent_tracks=args.jobs,
            retry_attempts=args.retry,
            dry_run=args.dry_run,
            verbose=verbose,
            skip_existing=not args.no_skip,
            clean_temp_on_exit=not args.no_cleanup,
            filename_template=args.filename_template,
            folder_structure=args.folder_structure,
        )
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    # Print banner
    if not args.quiet:
        print("=" * 70)
        print("  Spotify to Opus Converter")
        print("=" * 70)
        print()
    
    # Create and run orchestrator
    try:
        orchestrator = Orchestrator(config)
        stats = orchestrator.run(args.playlist)
        
        # Print final stats
        if not args.quiet:
            print()
            print("=" * 70)
            print(f"Completed: {stats['success']}/{stats['total']} tracks")
            if stats['total_time'] > 0:
                print(f"Total time: {stats['total_time']:.1f}s")
            print("=" * 70)
        
        # Exit with error code if any failures
        if stats['failed'] > 0:
            sys.exit(1)
        
    except KeyboardInterrupt:
        logger.warning("\nInterrupted by user")
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == '__main__':
    main()
