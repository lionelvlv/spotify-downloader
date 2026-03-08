"""Utility modules for the Spotify to Opus converter."""

from .file_utils import (
    sanitize_filename,
    build_output_path,
    safe_delete,
    ensure_directory,
    cleanup_temp_files,
)
from .logging_utils import setup_logging, ProgressLogger
from .string_similarity import (
    normalize_string,
    simple_similarity,
    partial_ratio,
    artist_in_title,
    calculate_match_score,
)

__all__ = [
    'sanitize_filename',
    'build_output_path',
    'safe_delete',
    'ensure_directory',
    'cleanup_temp_files',
    'setup_logging',
    'ProgressLogger',
    'normalize_string',
    'simple_similarity',
    'partial_ratio',
    'artist_in_title',
    'calculate_match_score',
]
