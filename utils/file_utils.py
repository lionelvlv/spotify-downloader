"""
File handling utilities for safe file operations.
"""
import re
from pathlib import Path
from typing import Optional
import shutil


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """
    Sanitize filename to be safe across Windows, macOS, and Linux.
    
    Args:
        filename: The original filename
        max_length: Maximum filename length
        
    Returns:
        Sanitized filename safe for all major operating systems
    """
    # Remove or replace invalid characters
    # Windows: < > : " / \ | ? *
    # Also remove control characters
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    filename = re.sub(invalid_chars, '', filename)
    
    # Replace multiple spaces with single space
    filename = re.sub(r'\s+', ' ', filename)
    
    # Strip leading/trailing spaces and periods (Windows issue)
    filename = filename.strip(' .')
    
    # Ensure it's not empty
    if not filename:
        filename = "untitled"
    
    # Truncate if too long (preserve extension)
    if len(filename) > max_length:
        filename = filename[:max_length]
    
    return filename


def build_output_path(
    base_dir: Path,
    track,
    folder_structure: str = "{artist}/{album}",
    filename_template: str = "{track_num:02d} - {title}"
) -> Path:
    """
    Build the complete output path for a track.
    
    Args:
        base_dir: Base output directory
        track: Track object with metadata
        folder_structure: Template for folder organization
        filename_template: Template for filename
        
    Returns:
        Complete Path object for the output file
    """
    # Build folder path
    artist = sanitize_filename(track.artists[0] if track.artists else "Unknown Artist")
    album = sanitize_filename(track.album or "Unknown Album")
    
    folder_path = folder_structure.format(
        artist=artist,
        album=album
    )
    
    # Build filename
    title = sanitize_filename(track.title or "Unknown Title")
    track_num = track.track_number if track.track_number else 0
    
    filename = filename_template.format(
        track_num=track_num,
        title=title
    ) + ".opus"
    
    return base_dir / folder_path / filename


def safe_delete(path: Path) -> bool:
    """
    Safely delete a file or directory.
    
    Args:
        path: Path to delete
        
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        return True
    except Exception:
        return False


def ensure_directory(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        The same Path object
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size_mb(path: Path) -> float:
    """
    Get file size in megabytes.
    
    Args:
        path: File path
        
    Returns:
        File size in MB, or 0 if file doesn't exist
    """
    try:
        return path.stat().st_size / (1024 * 1024)
    except Exception:
        return 0.0


def cleanup_temp_files(temp_dir: Path, pattern: str = "*") -> int:
    """
    Clean up temporary files matching a pattern.
    
    Args:
        temp_dir: Temporary directory
        pattern: Glob pattern for files to delete
        
    Returns:
        Number of files deleted
    """
    count = 0
    for file in temp_dir.glob(pattern):
        if safe_delete(file):
            count += 1
    return count
