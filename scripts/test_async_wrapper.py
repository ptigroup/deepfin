"""Test async wrapper for LLMWhisperer SDK."""
import asyncio
import time
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.llm.async_wrapper import AsyncLLMWhispererClient
from app.core.logging import get_logger

logger = get_logger(__name__)


async def test_async_wrapper():
    """Test that async wrapper works correctly with concurrent requests."""
    print("\n" + "="*80)
    print("TESTING ASYNC WRAPPER FOR LLMWHISPERER SDK")
    print("="*80)

    # Use Google PDF
    test_pdf = Path("input/Google 2022-2024.pdf")
    if not test_pdf.exists():
        print(f"ERROR: Test PDF not found: {test_pdf}")
        return

    client = AsyncLLMWhispererClient()

    # Test 1: Single request
    print("\n[TEST 1] Single Async Request")
    print("-" * 80)
    start = time.time()
    result = await client.whisper(
        file_path=test_pdf,
        mode="form",
        output_mode="layout_preserving",
        pages_to_extract="53",  # Balance sheet page
        wait_for_completion=True,
        wait_timeout=60
    )
    duration = time.time() - start
    text = result.get("extraction", {}).get("result_text", "")
    print(f"Duration: {duration:.2f}s")
    print(f"Text length: {len(text)}")
    single_duration = duration

    # Test 2: 3 concurrent async requests
    print("\n[TEST 2] 3 Concurrent Async Requests (True Parallelism)")
    print("-" * 80)
    print("Processing 3 pages concurrently...")
    start = time.time()

    # Run 3 extractions concurrently
    tasks = [
        client.whisper(
            file_path=test_pdf,
            mode="form",
            pages_to_extract="53",  # Balance sheet
            wait_for_completion=True,
            wait_timeout=60
        ),
        client.whisper(
            file_path=test_pdf,
            mode="form",
            pages_to_extract="54",  # Income statement
            wait_for_completion=True,
            wait_timeout=60
        ),
        client.whisper(
            file_path=test_pdf,
            mode="form",
            pages_to_extract="55",  # Comprehensive income
            wait_for_completion=True,
            wait_timeout=60
        )
    ]

    results = await asyncio.gather(*tasks)
    concurrent_duration = time.time() - start

    print(f"Duration: {concurrent_duration:.2f}s")
    print(f"Results: {len(results)} extractions")
    for i, result in enumerate(results, 1):
        text = result.get("extraction", {}).get("result_text", "")
        print(f"  Extraction {i}: {len(text)} chars")

    # Analysis
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)

    sequential_estimate = single_duration * 3
    speedup = sequential_estimate / concurrent_duration

    print(f"Single request:          {single_duration:.2f}s")
    print(f"Sequential (estimated):  {sequential_estimate:.2f}s (3x single)")
    print(f"Concurrent (actual):     {concurrent_duration:.2f}s")
    print(f"\nSpeedup factor:          {speedup:.2f}x")

    if speedup > 2.5:
        print("✓ EXCELLENT - Near-perfect parallelization!")
    elif speedup > 1.8:
        print("✓ GOOD - Significant speedup achieved")
    elif speedup > 1.3:
        print("~ MODERATE - Some speedup but not optimal")
    else:
        print("✗ POOR - Little to no speedup from concurrency")

    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(test_async_wrapper())
