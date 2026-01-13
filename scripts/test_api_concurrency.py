"""Test if LLMWhisperer API supports concurrent requests."""
import asyncio
import time
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.llm.clients import LLMWhispererClient
from app.core.logging import get_logger

logger = get_logger(__name__)


async def test_concurrent_api_calls():
    """Test if API processes requests concurrently or sequentially."""
    print("\n" + "="*80)
    print("TESTING LLMWHISPERER API CONCURRENCY")
    print("="*80)

    # Use a test PDF (balance sheet - small single page)
    test_pdf = Path("samples/input/balance sheet.pdf")
    if not test_pdf.exists():
        print(f"ERROR: Test PDF not found: {test_pdf}")
        return

    client = LLMWhispererClient()

    # Test 1: Single request baseline
    print("\n[TEST 1] Single Request Baseline")
    print("-" * 80)
    start = time.time()
    result = await client.whisper(
        file_path=test_pdf,
        processing_mode="form",
        pages_to_extract="1"
    )
    single_duration = time.time() - start
    print(f"Duration: {single_duration:.2f}s")
    print(f"Extracted text length: {len(result.extracted_text)}")

    # Test 2: 3 concurrent requests (same page, should use cache)
    print("\n[TEST 2] 3 Concurrent Requests (Same Page - Should Use Cache)")
    print("-" * 80)
    start = time.time()
    tasks = [
        client.whisper(file_path=test_pdf, processing_mode="form", pages_to_extract="1")
        for _ in range(3)
    ]
    results = await asyncio.gather(*tasks)
    concurrent_cached_duration = time.time() - start
    print(f"Duration: {concurrent_cached_duration:.2f}s")
    print(f"Results: {len(results)} extractions")
    print(f"Expected: ~{single_duration:.2f}s (cache hit)")

    # Test 3: Force reprocess to test true API concurrency
    print("\n[TEST 3] 3 Concurrent Requests (Force Reprocess - No Cache)")
    print("-" * 80)
    print("WARNING: This will hit the API 3 times!")
    start = time.time()
    tasks = [
        client.whisper(
            file_path=test_pdf,
            processing_mode="form",
            pages_to_extract="1",
            force_reprocess=True
        )
        for _ in range(3)
    ]
    results = await asyncio.gather(*tasks)
    concurrent_no_cache_duration = time.time() - start
    print(f"Duration: {concurrent_no_cache_duration:.2f}s")
    print(f"Results: {len(results)} extractions")

    # Analysis
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)

    sequential_estimate = single_duration * 3
    print(f"Single request:             {single_duration:.2f}s")
    print(f"Sequential (3x):            {sequential_estimate:.2f}s (estimated)")
    print(f"Concurrent (cached):        {concurrent_cached_duration:.2f}s")
    print(f"Concurrent (no cache):      {concurrent_no_cache_duration:.2f}s")

    # Determine if API supports concurrency
    speedup = sequential_estimate / concurrent_no_cache_duration
    print(f"\nSpeedup factor:             {speedup:.2f}x")

    if speedup > 2.5:
        print("✓ API SUPPORTS CONCURRENCY - Async will provide significant speedup!")
    elif speedup > 1.5:
        print("~ API PARTIALLY SUPPORTS CONCURRENCY - Modest speedup expected")
    else:
        print("✗ API DOES NOT SUPPORT CONCURRENCY - Sequential processing recommended")
        print("  (API likely has rate limiting or processes requests sequentially)")

    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(test_concurrent_api_calls())
