"""Tests for LLMWhisperer client."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.llm.cache import WhisperCache
from app.llm.clients import LLMWhispererClient, LLMWhispererError
from app.llm.schemas import ProcessingMode, WhisperResponse


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch("app.llm.clients.settings") as mock_settings:
        mock_settings.unstract_api_key = "test_api_key"
        mock_settings.cache_dir = ".cache"
        yield mock_settings


@pytest.fixture
def test_pdf_file(tmp_path):
    """Create a temporary test PDF file."""
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 test content")
    return pdf_file


@pytest.fixture
async def client(mock_settings, tmp_path):
    """Create a test client with temporary cache."""
    cache_dir = tmp_path / "cache"
    client = LLMWhispererClient(
        api_key="test_api_key",
        timeout=10.0,
        max_retries=3,
        use_cache=True,
    )
    # Override cache directory
    if client.cache:
        client.cache.cache_dir = cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)
    return client


class TestLLMWhispererClient:
    """Tests for LLMWhispererClient class."""

    def test_init_without_api_key(self):
        """Test that client raises error without API key."""
        with patch("app.llm.clients.settings") as mock_settings:
            mock_settings.unstract_api_key = None
            with pytest.raises(LLMWhispererError, match="UNSTRACT_API_KEY is required"):
                LLMWhispererClient()

    def test_init_with_custom_settings(self):
        """Test client initialization with custom settings."""
        client = LLMWhispererClient(
            api_key="custom_key",
            base_url="https://custom.url",
            timeout=60.0,
            max_retries=5,
            use_cache=False,
        )

        assert client.api_key == "custom_key"
        assert client.base_url == "https://custom.url"
        assert client.timeout == 60.0
        assert client.max_retries == 5
        assert client.cache is None

    @pytest.mark.asyncio
    async def test_whisper_file_not_found(self, client):
        """Test whisper with non-existent file."""
        with pytest.raises(LLMWhispererError, match="File not found"):
            await client.whisper("/nonexistent/file.pdf")

    @pytest.mark.asyncio
    async def test_whisper_success(self, client, test_pdf_file):
        """Test successful whisper call."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "whisper_hash": "abc123",
            "extracted_text": "Test extracted text",
            "page_count": 1,
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await client.whisper(test_pdf_file)

            assert isinstance(result, WhisperResponse)
            assert result.whisper_hash == "abc123"
            assert result.extracted_text == "Test extracted text"
            assert result.page_count == 1
            assert result.status_code == 200

            # Verify API was called
            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args.kwargs
            assert call_kwargs["headers"]["unstract-key"] == "test_api_key"

    @pytest.mark.asyncio
    async def test_whisper_with_cache(self, client, test_pdf_file):
        """Test that second call uses cache."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "whisper_hash": "abc123",
            "extracted_text": "Test extracted text",
            "page_count": 1,
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            # First call - should hit API
            result1 = await client.whisper(test_pdf_file)
            assert mock_post.call_count == 1

            # Second call - should use cache
            result2 = await client.whisper(test_pdf_file)
            assert mock_post.call_count == 1  # Still only 1 API call

            # Results should be the same
            assert result1.whisper_hash == result2.whisper_hash
            assert result1.extracted_text == result2.extracted_text

    @pytest.mark.asyncio
    async def test_whisper_force_reprocess(self, client, test_pdf_file):
        """Test force_reprocess bypasses cache."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "whisper_hash": "abc123",
            "extracted_text": "Test extracted text",
            "page_count": 1,
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            # First call
            await client.whisper(test_pdf_file)
            assert mock_post.call_count == 1

            # Second call with force_reprocess
            await client.whisper(test_pdf_file, force_reprocess=True)
            assert mock_post.call_count == 2  # Should make API call again

    @pytest.mark.asyncio
    async def test_whisper_http_error_4xx(self, client, test_pdf_file):
        """Test that 4xx errors are not retried."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "401", request=MagicMock(), response=mock_response
            )

            with pytest.raises(LLMWhispererError, match="API error: 401"):
                await client.whisper(test_pdf_file)

            # Should only try once (no retries for 4xx)
            assert mock_post.call_count == 1

    @pytest.mark.asyncio
    async def test_whisper_retry_on_5xx(self, client, test_pdf_file):
        """Test retry logic for 5xx errors."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "500", request=MagicMock(), response=mock_response
            )

            # Mock time.sleep to avoid actual waiting
            with (
                patch("time.sleep"),
                pytest.raises(LLMWhispererError, match="All 3 API call attempts failed"),
            ):
                await client.whisper(test_pdf_file)

            # Should retry 3 times
            assert mock_post.call_count == 3

    @pytest.mark.asyncio
    async def test_whisper_with_processing_mode(self, client, test_pdf_file):
        """Test whisper with different processing modes."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "whisper_hash": "abc123",
            "extracted_text": "Test extracted text",
            "page_count": 1,
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            await client.whisper(test_pdf_file, processing_mode=ProcessingMode.HIGH_QUALITY)

            # Verify processing mode was sent
            call_kwargs = mock_post.call_args.kwargs
            assert call_kwargs["data"]["processing_mode"] == "high_quality"

    @pytest.mark.asyncio
    async def test_whisper_with_pages_to_extract(self, client, test_pdf_file):
        """Test whisper with specific pages."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "whisper_hash": "abc123",
            "extracted_text": "Test extracted text",
            "page_count": 3,
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            await client.whisper(test_pdf_file, pages_to_extract="1-3")

            # Verify pages parameter was sent
            call_kwargs = mock_post.call_args.kwargs
            assert call_kwargs["data"]["pages_to_extract"] == "1-3"

    @pytest.mark.asyncio
    async def test_clear_cache(self, client, test_pdf_file):
        """Test cache clearing."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "whisper_hash": "abc123",
            "extracted_text": "Test extracted text",
            "page_count": 1,
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            # First call - caches result
            await client.whisper(test_pdf_file)
            assert mock_post.call_count == 1

            # Clear cache
            cleared = await client.clear_cache(str(test_pdf_file), ProcessingMode.TEXT)
            assert cleared == 1

            # Second call - should hit API again
            await client.whisper(test_pdf_file)
            assert mock_post.call_count == 2

    @pytest.mark.asyncio
    async def test_client_without_cache(self, test_pdf_file):
        """Test client with caching disabled."""
        client = LLMWhispererClient(api_key="test_key", use_cache=False)

        assert client.cache is None

        # clear_cache should return 0
        cleared = await client.clear_cache()
        assert cleared == 0


class TestWhisperCache:
    """Tests for WhisperCache class."""

    @pytest.fixture
    async def cache(self, tmp_path):
        """Create a cache with temporary directory."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        return WhisperCache(cache_dir=cache_dir)

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache):
        """Test cache miss returns None."""
        result = await cache.get("test.pdf", ProcessingMode.TEXT)
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_hit(self, cache):
        """Test cache hit returns stored result."""
        # Store result
        await cache.set(
            file_path="test.pdf",
            processing_mode=ProcessingMode.TEXT,
            whisper_hash="abc123",
            extracted_text="Test text",
            page_count=1,
        )

        # Retrieve result
        result = await cache.get("test.pdf", ProcessingMode.TEXT)

        assert result is not None
        assert result.whisper_hash == "abc123"
        assert result.extracted_text == "Test text"
        assert result.file_path == "test.pdf"
        assert result.page_count == 1

    @pytest.mark.asyncio
    async def test_cache_different_modes(self, cache):
        """Test that different processing modes have separate cache entries."""
        # Store with TEXT mode
        await cache.set(
            file_path="test.pdf",
            processing_mode=ProcessingMode.TEXT,
            whisper_hash="text_hash",
            extracted_text="Text mode result",
        )

        # Store with FORM mode
        await cache.set(
            file_path="test.pdf",
            processing_mode=ProcessingMode.FORM,
            whisper_hash="form_hash",
            extracted_text="Form mode result",
        )

        # Retrieve both
        text_result = await cache.get("test.pdf", ProcessingMode.TEXT)
        form_result = await cache.get("test.pdf", ProcessingMode.FORM)

        assert text_result.whisper_hash == "text_hash"
        assert form_result.whisper_hash == "form_hash"

    @pytest.mark.asyncio
    async def test_clear_all_cache(self, cache):
        """Test clearing all cache entries."""
        # Add multiple entries
        await cache.set("test1.pdf", ProcessingMode.TEXT, "hash1", "text1")
        await cache.set("test2.pdf", ProcessingMode.TEXT, "hash2", "text2")

        # Clear all
        cleared = await cache.clear()
        assert cleared == 2

        # Verify cache is empty
        result1 = await cache.get("test1.pdf", ProcessingMode.TEXT)
        result2 = await cache.get("test2.pdf", ProcessingMode.TEXT)
        assert result1 is None
        assert result2 is None

    @pytest.mark.asyncio
    async def test_clear_specific_entry(self, cache):
        """Test clearing a specific cache entry."""
        # Add entries
        await cache.set("test1.pdf", ProcessingMode.TEXT, "hash1", "text1")
        await cache.set("test2.pdf", ProcessingMode.TEXT, "hash2", "text2")

        # Clear only test1.pdf
        cleared = await cache.clear("test1.pdf", ProcessingMode.TEXT)
        assert cleared == 1

        # Verify test1 is gone but test2 remains
        result1 = await cache.get("test1.pdf", ProcessingMode.TEXT)
        result2 = await cache.get("test2.pdf", ProcessingMode.TEXT)
        assert result1 is None
        assert result2 is not None
