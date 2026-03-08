"""
Audio search engine using yt-dlp to find matching audio sources.
"""
import logging
from typing import Optional, Dict, Any, List
import yt_dlp
from utils.string_similarity import calculate_match_score


class SearchEngine:
    """Search for audio matches on public platforms."""
    
    def __init__(self, timeout: int = 30, max_results: int = 10):
        """
        Initialize search engine.
        
        Args:
            timeout: Timeout for search operations in seconds
            max_results: Maximum number of search results to consider
        """
        self.logger = logging.getLogger(__name__)
        self.timeout = timeout
        self.max_results = max_results
        
        # yt-dlp options for search (no download)
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'force_generic_extractor': False,
            'socket_timeout': timeout,
            'skip_download': True,
        }
    
    def search_best_match(self, track) -> Optional[Dict[str, Any]]:
        """
        Search for the best matching audio source for a track.
        
        Args:
            track: Track object with metadata
            
        Returns:
            Dictionary with best match info (url, title, duration) or None
        """
        self.logger.debug(f"Searching for: {track}")
        
        # Build search queries in order of specificity
        queries = self._build_queries(track)
        
        all_results = []
        
        # Try each query
        for query in queries:
            results = self._search_youtube(query)
            if results:
                all_results.extend(results)
                # If we have enough results, stop searching
                if len(all_results) >= self.max_results:
                    break
        
        if not all_results:
            self.logger.warning(f"No search results found for: {track}")
            return None
        
        # Rank and select best match
        best = self._rank_results(all_results, track)
        
        if best:
            self.logger.info(f"Found match: {best['title']} (score: {best.get('score', 0):.1f})")
        else:
            self.logger.warning(f"No acceptable match found for: {track}")
        
        return best
    
    def _build_queries(self, track) -> List[str]:
        """
        Build search queries in order of preference.
        
        Args:
            track: Track object
            
        Returns:
            List of search query strings
        """
        queries = []
        artist_str = " ".join(track.artists)
        
        # 1. ISRC (if available) - most specific
        if track.isrc:
            queries.append(track.isrc)
        
        # 2. Artist - Title (most common format)
        queries.append(f"{artist_str} {track.title}")
        
        # 3. Artist - Title with "official audio"
        queries.append(f"{artist_str} {track.title} official audio")
        
        # 4. Artist - Title - Album
        queries.append(f"{artist_str} {track.title} {track.album}")
        
        # 5. Title - Artist (alternative order)
        queries.append(f"{track.title} {artist_str}")
        
        return queries
    
    def _search_youtube(self, query: str) -> List[Dict[str, Any]]:
        """
        Perform YouTube search.
        
        Args:
            query: Search query string
            
        Returns:
            List of search result dictionaries
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Use ytsearch to search YouTube
                search_query = f"ytsearch{self.max_results}:{query}"
                info = ydl.extract_info(search_query, download=False)
                
                if not info or 'entries' not in info:
                    return []
                
                return [entry for entry in info['entries'] if entry]
                
        except Exception as e:
            self.logger.debug(f"Search failed for '{query}': {e}")
            return []
    
    def _rank_results(self, entries: List[Dict[str, Any]], track) -> Optional[Dict[str, Any]]:
        """
        Rank search results and return the best match.
        
        Args:
            entries: List of search result entries
            track: Original track to match against
            
        Returns:
            Best matching entry or None
        """
        scored_results = []
        
        for entry in entries:
            # Skip if missing essential data
            if not entry.get('title') or not entry.get('url'):
                continue
            
            title = entry.get('title', '')
            duration = entry.get('duration', 0)
            
            # Calculate match score
            score = calculate_match_score(
                track_title=track.title,
                track_artists=track.artists,
                track_duration_ms=track.duration_ms,
                result_title=title,
                result_duration_s=duration
            )
            
            # Duration check - reject if too far off
            if duration > 0:
                duration_diff_ms = abs(duration * 1000 - track.duration_ms)
                # Allow 10 second difference
                if duration_diff_ms > 10000:
                    score *= 0.5  # Penalize but don't reject entirely
            
            # Store result with score
            scored_results.append({
                'url': entry['url'],
                'webpage_url': entry.get('webpage_url', entry['url']),
                'title': title,
                'duration': duration,
                'score': score,
                'id': entry.get('id', ''),
            })
        
        if not scored_results:
            return None
        
        # Sort by score (highest first)
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        
        # Return best match if score is acceptable
        best = scored_results[0]
        
        # Minimum score threshold
        if best['score'] < 40:
            self.logger.debug(f"Best match score too low: {best['score']:.1f}")
            return None
        
        return best
    
    def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific video.
        
        Args:
            url: Video URL
            
        Returns:
            Video information dictionary or None
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            self.logger.error(f"Failed to get video info for {url}: {e}")
            return None
