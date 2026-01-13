"""
Simple in-memory cache to avoid repeated searches
"""
import time
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class SearchCache:
    _cache: Dict[str, tuple] = {}  # {query: (results, timestamp)}
    CACHE_DURATION = 300  
    
    @classmethod
    def get(cls, query: str) -> Optional[List[dict]]:
        """Get cached results if still valid"""
        key = query.lower().strip()
        
        if key in cls._cache:
            results, timestamp = cls._cache[key]
            
            # Check if still valid
            if time.time() - timestamp < cls.CACHE_DURATION:
                return results
            else:
                # Expired, remove
                del cls._cache[key]
        
        return None
    
    @classmethod
    def set(cls, query: str, results: List[dict]) -> None:
        """Cache search results"""
        key = query.lower().strip()
        cls._cache[key] = (results, time.time())
        
        # Limit cache size
        if len(cls._cache) > 100:
            # Remove oldest
            try:
                oldest_key = min(cls._cache.keys(), key=lambda k: cls._cache[k][1])
                del cls._cache[oldest_key]
            except Exception:
                # Fallback if sorting fails
                cls._cache.clear()
    
    @classmethod
    def clear(cls) -> None:
        """Clear all cache"""
        cls._cache.clear()
