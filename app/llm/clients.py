"""LLMWhisperer API client implementation."""

import time
from pathlib import Path

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.llm.cache import WhisperCache
from app.llm.schemas import ProcessingMode, WhisperRequest, WhisperResponse

logger = get_logger(__name__)
settings = get_settings()


class LLMWhispererError(Exception):
    """Base exception for LLMWhisperer client errors."""

    pass


class LLMWhispererClient:
    """Async HTTP client for LLMWhisperer API."""

    BASE_URL = "https://llmwhisperer-api.us-central.unstract.com/api/v2"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 300.0,
        max_retries: int = 3,
        use_cache: bool = True,
    ) -> None:
        """Initialize the LLMWhisperer client.

        Args:
            api_key: Unstract API key. Defaults to settings.unstract_api_key
            base_url: API base URL. Defaults to official Unstract URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            use_cache: Whether to use file caching
        """
        self.api_key = api_key or settings.unstract_api_key
        self.base_url = base_url or self.BASE_URL
        self.timeout = timeout
        self.max_retries = max_retries
        self.use_cache = use_cache

        if not self.api_key:
            raise LLMWhispererError("UNSTRACT_API_KEY is required")

        self.cache = WhisperCache() if use_cache else None

        logger.info(
            "LLMWhispererClient initialized",
            extra={
                "base_url": self.base_url,
                "timeout": timeout,
                "max_retries": max_retries,
                "use_cache": use_cache,
            },
        )

    async def whisper(
        self,
        file_path: str | Path,
        processing_mode: ProcessingMode = ProcessingMode.TEXT,
        force_reprocess: bool = False,
        **kwargs,
    ) -> WhisperResponse:
        """Extract text from PDF using LLMWhisperer API.

        Args:
            file_path: Path to the PDF file
            processing_mode: Processing mode for extraction
            force_reprocess: Force reprocessing even if cached
            **kwargs: Additional parameters for WhisperRequest

        Returns:
            WhisperResponse with extracted text

        Raises:
            LLMWhispererError: If API call fails
        """
        file_path_str = str(file_path)

        # Check cache first
        if self.cache and not force_reprocess:
            cached = await self.cache.get(file_path_str, processing_mode)
            if cached:
                logger.info("Returning cached result", extra={"file_path": file_path_str})
                return WhisperResponse(
                    whisper_hash=cached.whisper_hash,
                    extracted_text=cached.extracted_text,
                    status_code=200,
                    processing_time=0.0,
                    page_count=cached.page_count,
                )

        # Validate file exists
        if not Path(file_path).exists():
            raise LLMWhispererError(f"File not found: {file_path}")

        # Create request
        request = WhisperRequest(
            file_path=file_path_str,
            processing_mode=processing_mode,
            **kwargs,
        )

        # Call API with retries
        start_time = time.time()
        response = await self._call_api_with_retry(request)
        processing_time = time.time() - start_time

        # Cache the result
        if self.cache:
            await self.cache.set(
                file_path=file_path_str,
                processing_mode=processing_mode,
                whisper_hash=response.whisper_hash,
                extracted_text=response.extracted_text,
                page_count=response.page_count,
            )

        response.processing_time = processing_time
        logger.info(
            "Whisper completed",
            extra={
                "file_path": file_path_str,
                "processing_time": round(processing_time, 2),
                "text_length": len(response.extracted_text),
                "page_count": response.page_count,
            },
        )

        return response

    async def _call_api_with_retry(self, request: WhisperRequest) -> WhisperResponse:
        """Call LLMWhisperer API with exponential backoff retry.

        Args:
            request: Whisper request parameters

        Returns:
            WhisperResponse from API

        Raises:
            LLMWhispererError: If all retries fail
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return await self._call_api(request)
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code in {400, 401, 403, 404}:
                    # Don't retry client errors
                    raise LLMWhispererError(
                        f"API error: {e.response.status_code} - {e.response.text}"
                    ) from e

                # Exponential backoff for server errors
                if attempt < self.max_retries - 1:
                    wait_time = 2**attempt
                    logger.warning(
                        "API call failed, retrying",
                        extra={
                            "attempt": attempt + 1,
                            "max_retries": self.max_retries,
                            "wait_time": wait_time,
                            "status_code": e.response.status_code,
                        },
                    )
                    await httpx.AsyncClient().aclose()  # Clean up
                    time.sleep(wait_time)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2**attempt
                    logger.warning(
                        "API call failed, retrying",
                        extra={
                            "attempt": attempt + 1,
                            "max_retries": self.max_retries,
                            "wait_time": wait_time,
                            "error": str(e),
                        },
                    )
                    time.sleep(wait_time)

        # All retries failed
        raise LLMWhispererError(f"All {self.max_retries} API call attempts failed") from last_error

    async def _call_api(self, request: WhisperRequest) -> WhisperResponse:
        """Make a single API call to LLMWhisperer.

        Args:
            request: Whisper request parameters

        Returns:
            WhisperResponse from API

        Raises:
            httpx.HTTPStatusError: If API returns error status
            LLMWhispererError: If file cannot be read
        """
        # Read file
        try:
            with open(request.file_path, "rb") as f:
                file_content = f.read()
        except Exception as e:
            raise LLMWhispererError(f"Failed to read file: {request.file_path}") from e

        # Prepare request
        url = f"{self.base_url}/whisper"
        headers = {"unstract-key": self.api_key}
        files = {"file": (Path(request.file_path).name, file_content, "application/pdf")}
        data = {
            "processing_mode": request.processing_mode.value,
            "output_format": request.output_format,
            "page_separator": request.page_separator,
            "force_text_processing": str(request.force_text_processing).lower(),
        }

        if request.pages_to_extract:
            data["pages_to_extract"] = request.pages_to_extract

        # Make API call
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()

            # Parse response
            result = response.json()

            # Debug: Log response structure
            logger.debug(
                "API response received",
                extra={"response_keys": list(result.keys()), "status": response.status_code}
            )

            return WhisperResponse(
                whisper_hash=result.get("whisper_hash", ""),
                extracted_text=result.get("extracted_text", ""),
                status_code=response.status_code,
                processing_time=0.0,  # Will be set by caller
                page_count=result.get("page_count"),
            )

    async def clear_cache(
        self, file_path: str | None = None, processing_mode: ProcessingMode | None = None
    ) -> int:
        """Clear cache entries.

        Args:
            file_path: If provided, clear only this file's cache
            processing_mode: If provided (with file_path), clear only this mode

        Returns:
            Number of cache entries cleared
        """
        if not self.cache:
            logger.warning("Cache not enabled")
            return 0

        return await self.cache.clear(file_path, processing_mode)
