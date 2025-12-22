"""Async file caching for LLMWhisperer API responses."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import aiofiles

from app.core.config import get_settings
from app.core.logging import get_logger
from app.llm.schemas import CachedWhisperResult, ProcessingMode

logger = get_logger(__name__)
settings = get_settings()


class WhisperCache:
    """Async file-based cache for LLMWhisperer API responses."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        """Initialize the cache.

        Args:
            cache_dir: Directory to store cache files. Defaults to settings.cache_dir
        """
        self.cache_dir = cache_dir or Path(settings.cache_dir) / "llmwhisperer"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info("WhisperCache initialized", extra={"cache_dir": str(self.cache_dir)})

    def _get_cache_key(self, file_path: str, processing_mode: ProcessingMode) -> str:
        """Generate a unique cache key for a file and processing mode.

        Args:
            file_path: Path to the PDF file
            processing_mode: Processing mode used

        Returns:
            SHA256 hash as cache key
        """
        key_str = f"{file_path}:{processing_mode.value}"
        return hashlib.sha256(key_str.encode()).hexdigest()

    def _get_cache_file_path(self, cache_key: str) -> Path:
        """Get the file path for a cache key.

        Args:
            cache_key: Cache key hash

        Returns:
            Path to cache file
        """
        return self.cache_dir / f"{cache_key}.json"

    async def get(
        self, file_path: str, processing_mode: ProcessingMode
    ) -> CachedWhisperResult | None:
        """Retrieve cached result if available.

        Args:
            file_path: Path to the PDF file
            processing_mode: Processing mode used

        Returns:
            Cached result or None if not found
        """
        cache_key = self._get_cache_key(file_path, processing_mode)
        cache_file = self._get_cache_file_path(cache_key)

        if not cache_file.exists():
            logger.debug("Cache miss", extra={"file_path": file_path, "cache_key": cache_key})
            return None

        try:
            async with aiofiles.open(cache_file, encoding="utf-8") as f:
                content = await f.read()
                data = json.loads(content)
                result = CachedWhisperResult(**data)
                logger.info(
                    "Cache hit",
                    extra={
                        "file_path": file_path,
                        "cache_key": cache_key,
                        "cached_at": result.cached_at.isoformat(),
                    },
                )
                return result
        except Exception as e:
            logger.error(
                "Cache read error",
                extra={"file_path": file_path, "cache_key": cache_key, "error": str(e)},
                exc_info=True,
            )
            return None

    async def set(
        self,
        file_path: str,
        processing_mode: ProcessingMode,
        whisper_hash: str,
        extracted_text: str,
        page_count: int | None = None,
    ) -> None:
        """Store result in cache.

        Args:
            file_path: Path to the PDF file
            processing_mode: Processing mode used
            whisper_hash: Whisper hash from API
            extracted_text: Extracted text content
            page_count: Number of pages processed
        """
        cache_key = self._get_cache_key(file_path, processing_mode)
        cache_file = self._get_cache_file_path(cache_key)

        result = CachedWhisperResult(
            whisper_hash=whisper_hash,
            extracted_text=extracted_text,
            file_path=file_path,
            cached_at=datetime.now(UTC),
            processing_mode=processing_mode,
            page_count=page_count,
        )

        try:
            async with aiofiles.open(cache_file, "w", encoding="utf-8") as f:
                content = result.model_dump_json(indent=2)
                await f.write(content)
                logger.info(
                    "Cache write successful",
                    extra={
                        "file_path": file_path,
                        "cache_key": cache_key,
                        "text_length": len(extracted_text),
                    },
                )
        except Exception as e:
            logger.error(
                "Cache write error",
                extra={"file_path": file_path, "cache_key": cache_key, "error": str(e)},
                exc_info=True,
            )

    async def clear(
        self, file_path: str | None = None, processing_mode: ProcessingMode | None = None
    ) -> int:
        """Clear cache entries.

        Args:
            file_path: If provided, clear only this file's cache
            processing_mode: If provided (with file_path), clear only this mode

        Returns:
            Number of cache entries cleared
        """
        if file_path and processing_mode:
            # Clear specific cache entry
            cache_key = self._get_cache_key(file_path, processing_mode)
            cache_file = self._get_cache_file_path(cache_key)
            if cache_file.exists():
                cache_file.unlink()
                logger.info(
                    "Cache entry cleared", extra={"file_path": file_path, "cache_key": cache_key}
                )
                return 1
            return 0

        # Clear all cache
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1

        logger.info("Cache cleared", extra={"entries_cleared": count})
        return count
