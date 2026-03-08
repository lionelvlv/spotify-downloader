"""
String similarity and matching utilities for audio search.
"""
import re
from typing import List


def normalize_string(text: str) -> str:
    """
    Normalize string for comparison.
    
    Args:
        text: Input string
        
    Returns:
        Normalized lowercase string with extra whitespace removed
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters but keep spaces
    text = re.sub(r'[^\w\s-]', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def simple_similarity(str1: str, str2: str) -> float:
    """
    Calculate simple similarity score between two strings.
    Uses character overlap and length similarity.
    
    Args:
        str1: First string
        str2: Second string
        
    Returns:
        Similarity score between 0 and 100
    """
    # Normalize both strings
    s1 = normalize_string(str1)
    s2 = normalize_string(str2)
    
    if not s1 or not s2:
        return 0.0
    
    # If strings are identical
    if s1 == s2:
        return 100.0
    
    # Calculate overlap
    s1_set = set(s1.split())
    s2_set = set(s2.split())
    
    if not s1_set or not s2_set:
        return 0.0
    
    intersection = len(s1_set & s2_set)
    union = len(s1_set | s2_set)
    
    if union == 0:
        return 0.0
    
    # Jaccard similarity
    jaccard = intersection / union
    
    # Length similarity (penalize very different lengths)
    len_ratio = min(len(s1), len(s2)) / max(len(s1), len(s2))
    
    # Combined score
    score = (jaccard * 0.7 + len_ratio * 0.3) * 100
    
    return score


def partial_ratio(str1: str, str2: str) -> float:
    """
    Calculate partial ratio - checks if one string is contained in another.
    
    Args:
        str1: First string
        str2: Second string
        
    Returns:
        Similarity score between 0 and 100
    """
    s1 = normalize_string(str1)
    s2 = normalize_string(str2)
    
    if not s1 or not s2:
        return 0.0
    
    # Check if shorter string is in longer string
    shorter = s1 if len(s1) <= len(s2) else s2
    longer = s2 if len(s1) <= len(s2) else s1
    
    if shorter in longer:
        # Calculate what percentage of the longer string is matched
        match_ratio = len(shorter) / len(longer)
        return match_ratio * 100
    
    # Otherwise use simple similarity
    return simple_similarity(str1, str2)


def artist_in_title(artists: List[str], title: str) -> bool:
    """
    Check if any artist name appears in the title.
    
    Args:
        artists: List of artist names
        title: Title string to search
        
    Returns:
        True if any artist is found in title
    """
    normalized_title = normalize_string(title)
    
    for artist in artists:
        normalized_artist = normalize_string(artist)
        if normalized_artist and normalized_artist in normalized_title:
            return True
    
    return False


def duration_similarity(duration1_ms: int, duration2_ms: int, tolerance_ms: int = 5000) -> float:
    """
    Calculate similarity based on duration match.
    
    Args:
        duration1_ms: First duration in milliseconds
        duration2_ms: Second duration in milliseconds
        tolerance_ms: Acceptable difference in milliseconds
        
    Returns:
        Score between 0 and 100 based on duration match
    """
    if duration1_ms <= 0 or duration2_ms <= 0:
        return 0.0
    
    diff = abs(duration1_ms - duration2_ms)
    
    if diff <= tolerance_ms:
        # Within tolerance - score based on how close
        score = 100.0 * (1.0 - (diff / tolerance_ms))
        return max(0.0, min(100.0, score))
    
    return 0.0


def calculate_match_score(
    track_title: str,
    track_artists: List[str],
    track_duration_ms: int,
    result_title: str,
    result_duration_s: int
) -> float:
    """
    Calculate comprehensive match score for a search result.
    
    Args:
        track_title: Original track title
        track_artists: List of track artists
        track_duration_ms: Track duration in milliseconds
        result_title: Search result title
        result_duration_s: Search result duration in seconds
        
    Returns:
        Overall match score between 0 and 100
    """
    # Title similarity (50% weight)
    title_score = partial_ratio(track_title, result_title) * 0.5
    
    # Artist presence bonus (30% weight)
    artist_score = 0.0
    if artist_in_title(track_artists, result_title):
        artist_score = 30.0
    
    # Duration similarity (20% weight)
    duration_score = duration_similarity(track_duration_ms, result_duration_s * 1000) * 0.2
    
    # Combined score
    total_score = title_score + artist_score + duration_score
    
    return min(100.0, total_score)
