# Parallel Extraction Investigation

## Problem Statement

ThreadPoolExecutor made extraction **SLOWER**, not faster:
- **Sequential**: 443 seconds (7.4 minutes)
- **Parallel (5 workers)**: 686 seconds (11.4 minutes) - **54% SLOWER!**

## Root Cause Analysis

### 1. Blocking HTTP Client

The test script uses `LLMWhispererClientV2` from Unstract SDK, which is **synchronous/blocking**:

```python
from unstract.llmwhisperer import LLMWhispererClientV2

result = self.llm_client.whisper(
    file_path=str(pdf_path),
    mode="form",
    wait_for_completion=True,    # BLOCKS for up to 200 seconds!
    wait_timeout=200
)
```

**Issue**: Each thread **blocks** waiting for the API response, preventing true parallelization.

### 2. ThreadPoolExecutor Limitations

Python's `ThreadPoolExecutor` uses **threads**, not async:
- **GIL (Global Interpreter Lock)**: Threads can't run Python code in parallel
- **Blocking I/O**: When a thread makes a blocking HTTP call, it waits idle
- **No true concurrency**: Threads context-switch but don't parallelize I/O

### 3. API-Side Bottleneck

Execution trace shows requests are **queued server-side**:

```
13:27:04 - 5 LLMWhisperer calls start (all for PDF 1)
13:27:21 - First results return (17 seconds later)
13:27:22 - More results (sequential completion)
13:27:29 - More results
13:27:34 - Next batch starts (PDF 2)
```

**Pattern**: Despite 5 concurrent threads, results arrive **sequentially**, indicating:
- API rate limiting (e.g., "max 1 request/second per API key")
- Server-side queueing (processes one at a time)
- No parallelization benefit

### 4. ThreadPoolExecutor Overhead

Additional overhead from threads:
- Thread creation/destruction
- Context switching
- Queue management
- Synchronization primitives

**Result**: Overhead PLUS no actual parallelization = slower performance.

## Why Sequential Was Faster

Sequential execution:
1. Send request → Wait → Process → Next
2. Simple, predictable, no overhead
3. API processes at same rate anyway

Parallel with threads:
1. Create 5 threads → Overhead
2. All send requests → API queues them anyway
3. Threads block waiting → No benefit
4. Context switching → Additional overhead
5. Results arrive at same rate as sequential

**Net effect**: Same work + extra overhead = slower.

## The Solution: Async/Await

### Why Async Would Work

Python's `asyncio` enables **true concurrent I/O**:

```python
import asyncio
import httpx

async def extract_statement(pdf_path, stmt_type, pages):
    # Non-blocking HTTP call
    async with httpx.AsyncClient() as client:
        response = await client.post(...)  # Doesn't block other tasks!
        return response

# Run concurrently
results = await asyncio.gather(
    extract_statement(pdf1, type1, pages1),
    extract_statement(pdf1, type2, pages2),
    extract_statement(pdf1, type3, pages3),
    # ... all run concurrently without blocking
)
```

**Benefits**:
- No thread overhead
- True concurrent I/O (event loop)
- Can handle 100s of concurrent requests
- Single thread, no GIL issues

### Implementation Plan

1. **Use existing async client**: `app/llm/clients.py` already has `async def whisper()`
   ```python
   from app.llm.clients import LLMWhispererClient

   async def whisper(...):  # Already async!
   ```

2. **Convert pipeline to async**:
   ```python
   async def _extract_single_statement(self, pdf_path, stmt_type, pages):
       raw_text = await self.llm_client.whisper(...)  # await instead of blocking
       structured = await self.extractor.extract_from_text(...)
       return result

   async def _phase2_extract_all_statements(self, ...):
       tasks = [
           self._extract_single_statement(pdf, type, pages)
           for pdf, type, pages in extraction_tasks
       ]
       results = await asyncio.gather(*tasks)  # Run concurrently!
   ```

3. **Expected improvement**:
   - **If API allows concurrent processing**: 5x faster (60 seconds vs 300 seconds)
   - **If API rate-limits**: Same speed as sequential, but no overhead
   - **Best case**: Significant speedup if API supports concurrency

## Testing Plan

### Test 1: Verify API Rate Limiting

Send 5 concurrent async requests and measure:
- Do they complete in parallel or sequentially?
- What's the actual API concurrency limit?

```python
import asyncio
import time

async def test_concurrent_requests():
    start = time.time()
    tasks = [llm_client.whisper(...) for _ in range(5)]
    results = await asyncio.gather(*tasks)
    duration = time.time() - start

    # If duration ≈ 1x single request: API allows concurrency
    # If duration ≈ 5x single request: API is sequential
```

### Test 2: Benchmark Async vs Sequential

Compare:
- Sequential (current): 443 seconds
- Async (5 concurrent): ? seconds
- Async (10 concurrent): ? seconds

### Test 3: Optimal Concurrency Level

Find sweet spot:
- Too few workers: Underutilized
- Too many workers: API rejects or queues

## Recommendation

1. **Convert to async/await** (proper solution)
   - Use existing `app.llm.clients.LLMWhispererClient` (already async)
   - Convert pipeline methods to async
   - Use `asyncio.gather()` for concurrent execution

2. **Keep thread-based code as fallback** (compatibility)
   - Some environments don't support async easily
   - ThreadPoolExecutor works everywhere

3. **Make it configurable**:
   ```python
   def run_pipeline(pdfs, use_async=True, max_concurrent=5):
       if use_async:
           return asyncio.run(async_pipeline(pdfs, max_concurrent))
       else:
           return sync_pipeline(pdfs)
   ```

## Alternative: Increase Sequential Speed

If async conversion is complex, optimize sequential execution:
1. **Cache LLMWhisperer results** (already implemented)
2. **Reduce API timeout** from 200s to 60s (fail faster)
3. **Batch process same-page extractions** (deduplicate API calls)
4. **Pipeline GPT calls** (start OpenAI while waiting for next LLMWhisperer)

## Files to Modify

1. **Convert to async**:
   - `scripts/test_end_to_end_pipeline.py`
     - Change `def _extract_single_statement()` → `async def`
     - Change `def _phase2_extract_all_statements()` → `async def`
     - Use `await` for API calls
     - Use `asyncio.gather()` instead of ThreadPoolExecutor

2. **Use existing async client**:
   - Replace `LLMWhispererClientV2` with `app.llm.clients.LLMWhispererClient`
   - Already has `async def whisper()`

3. **Test harness**:
   - Add `async def main()` wrapper
   - Call with `asyncio.run(main())`

## Conclusion

**ThreadPoolExecutor failed because**:
1. Blocking HTTP client (synchronous SDK)
2. API-side rate limiting/queueing
3. Thread overhead without parallelization benefit

**Async/await will succeed because**:
1. True concurrent I/O without blocking
2. No thread overhead
3. Can handle actual API concurrency if available

**Next step**: Convert pipeline to async/await using existing async client in `app/llm/clients.py`.
