"""Result caching mechanism for AI API calls."""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching of AI API responses."""

    def __init__(self, cache_dir: Optional[Path] = None, max_age_hours: int = 24):
        self.cache_dir = cache_dir or Path("./output/.cache")
        self.max_age_hours = max_age_hours
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _generate_key(self, content: str, provider: str, model: str) -> str:
        """Generate a unique cache key for the content."""
        hash_input = f"{provider}:{model}:{content}"
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()[:16]

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for a key."""
        return self.cache_dir / f"{key}.json"

    def get(self, content: str, provider: str, model: str) -> Optional[str]:
        """
        Get cached response if available and not expired.

        Args:
            content: The input content
            provider: AI provider name
            model: Model name

        Returns:
            Cached response or None if not found/expired
        """
        key = self._generate_key(content, provider, model)
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)

            # Check expiration
            cached_time = datetime.fromisoformat(cached['timestamp'])
            age_hours = (datetime.now() - cached_time).total_seconds() / 3600

            if age_hours > self.max_age_hours:
                logger.debug(f"Cache expired for key {key}")
                return None

            logger.info(f"Cache hit for key {key}")
            return cached['response']

        except Exception as e:
            logger.warning(f"Failed to read cache: {e}")
            return None

    def set(self, content: str, provider: str, model: str, response: str):
        """
        Save response to cache.

        Args:
            content: The input content
            provider: AI provider name
            model: Model name
            response: The AI response to cache
        """
        key = self._generate_key(content, provider, model)
        cache_path = self._get_cache_path(key)

        try:
            cached = {
                'key': key,
                'provider': provider,
                'model': model,
                'content_hash': hashlib.sha256(content.encode('utf-8')).hexdigest()[:8],
                'response': response,
                'timestamp': datetime.now().isoformat(),
            }

            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cached, f, ensure_ascii=False, indent=2)

            logger.debug(f"Cached response for key {key}")

        except Exception as e:
            logger.warning(f"Failed to write cache: {e}")

    def clear_expired(self):
        """Remove all expired cache entries."""
        removed = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)

                cached_time = datetime.fromisoformat(cached['timestamp'])
                age_hours = (datetime.now() - cached_time).total_seconds() / 3600

                if age_hours > self.max_age_hours:
                    cache_file.unlink()
                    removed += 1

            except Exception:
                pass

        if removed > 0:
            logger.info(f"Removed {removed} expired cache entries")

        return removed

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in total_files)

        return {
            'cache_dir': str(self.cache_dir),
            'total_entries': len(total_files),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
        }
