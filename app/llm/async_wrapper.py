"""Async wrapper for LLMWhisperer sync SDK using asyncio.to_thread()."""

import asyncio
from pathlib import Path

from unstract.llmwhisperer import LLMWhispererClientV2

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class AsyncLLMWhispererClient:
    """Async wrapper for LLMWhisperer sync SDK.

    Uses asyncio.to_thread() to run blocking SDK calls in a thread pool,
    enabling true concurrent async/await without blocking the event loop.
    """

    def __init__(self):
        """Initialize the async wrapper with sync SDK client."""
        self.client = LLMWhispererClientV2()
        logger.info("AsyncLLMWhispererClient initialized (wrapper around sync SDK)")

    async def whisper(
        self,
        file_path: str | Path,
        mode: str = "form",
        output_mode: str = "layout_preserving",
        pages_to_extract: str | None = None,
        wait_for_completion: bool = True,
        wait_timeout: int = 200,
        **kwargs
    ) -> dict:
        """Extract text from PDF asynchronously.

        Args:
            file_path: Path to PDF file
            mode: Processing mode ("form", "text", etc.)
            output_mode: Output mode ("layout_preserving", etc.)
            pages_to_extract: Comma-separated page numbers (e.g., "1,2,3")
            wait_for_completion: Wait for API to finish processing
            wait_timeout: Max wait time in seconds
            **kwargs: Additional parameters passed to SDK

        Returns:
            Dict with extraction result from LLMWhisperer API

        Raises:
            LLMWhispererClientException: If API call fails
        """
        logger.debug(
            "Starting async whisper",
            extra={
                "file_path": str(file_path),
                "mode": mode,
                "pages": pages_to_extract
            }
        )

        # Run blocking SDK call in thread pool
        result = await asyncio.to_thread(
            self.client.whisper,
            file_path=str(file_path),
            mode=mode,
            output_mode=output_mode,
            pages_to_extract=pages_to_extract or "",
            wait_for_completion=wait_for_completion,
            wait_timeout=wait_timeout,
            **kwargs
        )

        logger.debug("Async whisper completed")
        return result

    async def whisper_status(self, whisper_hash: str) -> dict:
        """Check status of a whisper job asynchronously.

        Args:
            whisper_hash: Hash returned from whisper() call

        Returns:
            Dict with status information
        """
        return await asyncio.to_thread(self.client.whisper_status, whisper_hash)

    async def whisper_retrieve(self, whisper_hash: str) -> dict:
        """Retrieve results of a completed whisper job asynchronously.

        Args:
            whisper_hash: Hash returned from whisper() call

        Returns:
            Dict with extraction results
        """
        return await asyncio.to_thread(self.client.whisper_retrieve, whisper_hash)
