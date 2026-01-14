"""Simple test to verify LLMWhisperer API works before async conversion."""
import time
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from unstract.llmwhisperer import LLMWhispererClientV2
from app.core.logging import get_logger

logger = get_logger(__name__)


def test_sequential_api_calls():
    """Test sequential API calls as baseline."""
    print("\n" + "="*80)
    print("TESTING LLMWHISPERER API - SEQUENTIAL BASELINE")
    print("="*80)

    # Use balance sheet PDF (single page, fast)
    test_pdf = Path("input/Google 2022-2024.pdf")
    if not test_pdf.exists():
        test_pdf = Path("samples/input/balance sheet.pdf")

    if not test_pdf.exists():
        print(f"ERROR: No test PDF found")
        return

    client = LLMWhispererClientV2()

    # Test: 3 sequential requests
    print(f"\nTest PDF: {test_pdf}")
    print("\n[TEST] 3 Sequential Requests")
    print("-" * 80)

    durations = []
    for i in range(3):
        print(f"Request {i+1}/3...")
        start = time.time()

        result = client.whisper(
            file_path=str(test_pdf),
            mode="form",
            output_mode="layout_preserving",
            pages_to_extract="53",  # Balance sheet page
            wait_for_completion=True,
            wait_timeout=60
        )

        duration = time.time() - start
        durations.append(duration)
        text_len = len(result.get("extraction", {}).get("result_text", ""))
        print(f"  Duration: {duration:.2f}s, Text length: {text_len}")

    # Analysis
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)
    avg_duration = sum(durations) / len(durations)
    total_duration = sum(durations)

    print(f"Individual durations: {[f'{d:.2f}s' for d in durations]}")
    print(f"Average per request:  {avg_duration:.2f}s")
    print(f"Total sequential:     {total_duration:.2f}s")
    print(f"\nIf async works perfectly (3x speedup): ~{total_duration/3:.2f}s")
    print(f"If async works partially (2x speedup): ~{total_duration/2:.2f}s")
    print("\n" + "="*80)


if __name__ == "__main__":
    test_sequential_api_calls()
