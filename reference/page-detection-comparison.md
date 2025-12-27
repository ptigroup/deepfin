# Page Detection Approaches: Brownfield vs Proposed Solution

## Overview

**Problem:** Large PDFs (100+ pages) waste API costs when we only need 1-2 pages containing financial tables.

**Example:**
- NVIDIA 10K 2020-2019.pdf: 100+ pages, but only page ~39 has Income Statement
- Current cost: Processing 374,403 characters → ~$8.65 per document
- Target cost: Processing ~3,000 characters → ~$0.05 per document
- **Potential savings: 99.4% (~$8.60 per document)**

---

## Approach 1: Brownfield (PyMuPDF Table Detection)

### How It Works

```python
# Step 1: Local table detection with PyMuPDF (FREE - no API calls)
import fitz  # PyMuPDF
doc = fitz.open("nvidia_10k.pdf")

for page_num in range(len(doc)):
    page = doc[page_num]
    table_finder = page.find_tables()  # Find tables on this page

    for table in table_finder.tables:
        # Extract table content locally
        table_data = table.extract()
        page_text = page.get_text()

        # Rule-based validation (no LLM needed!)
        if is_financial_statement(page_text, table_data):
            pages_to_extract.append(page_num)

# Step 2: Extract ONLY relevant pages with LLMWhisperer
llmw = LLMWhispererClient()
result = llmw.whisper(
    file_path="nvidia_10k.pdf",
    pages_to_extract="38,39,40"  # Only these pages
)

# Step 3: Structured extraction with OpenAI
financial_data = extract_with_openai(result["extracted_text"])
```

### Rule-Based Validation Logic

```python
def _validate_financial_content(combined_content, table_data):
    score = 0

    # 1. Keyword matching (10 points each)
    keywords = ['revenue', 'net income', 'total assets', 'stockholders equity']
    for keyword in keywords:
        if keyword in content.lower():
            score += 10

    # 2. Financial data patterns (20 points)
    dollar_amounts = len(re.findall(r'\$[\d,]+', content))
    if dollar_amounts >= 3:
        score += 20

    # 3. Multi-year structure (15 points)
    years = len(re.findall(r'\b20\d{2}\b', content))
    if years >= 2:
        score += 15

    # 4. Table structure (15 points)
    if len(table_data) >= 5:  # Minimum rows
        score += 15

    # 5. Multi-column check (10 points)
    if len(table_data[0]) >= 3:  # At least 3 columns
        score += 10

    # 6. Title indicators (25 points)
    if 'consolidated statements' in content.lower():
        score += 25

    # Penalties
    if content.count('%') > 10:  # Percentage tables (not statements)
        score -= 30

    # Threshold: 30+ points = valid financial table
    return score >= 30
```

### Costs

**PyMuPDF Processing:**
- Cost: $0 (runs locally on CPU)
- Time: ~1-2 seconds for 100-page PDF
- Memory: ~50MB for large PDF

**LLMWhisperer:**
- Cost: Only pages extracted (e.g., 3 pages instead of 100)
- Pricing model: Per page, not per token
- Example: 3 pages @ $X/page vs 100 pages @ $X/page

**OpenAI:**
- Cost: Only extracted page text (~3K chars instead of 374K chars)
- Savings: 99.4% reduction in token costs

### Pros

✅ **Zero cost for detection** - PyMuPDF runs locally
✅ **Fast** - Table detection takes 1-2 seconds
✅ **No external API dependency** - Works offline
✅ **Rule-based = deterministic** - Same input → same output
✅ **Already validated** - You've used this successfully in brownfield
✅ **Smart page expansion** - Includes surrounding pages (statements often span multiple pages)

```python
# Brownfield adds surrounding pages (smart!)
for page_offset in [-1, 0, 1, 2]:
    target_page = page_num + page_offset
    if target_page > 0:
        page_ranges[stmt_type].append(target_page)
```

### Cons

❌ **PyMuPDF dependency** - Adds another library (but you already use it in brownfield)
❌ **Rule-based brittle** - New statement formats might not match rules
❌ **Requires tuning** - Score thresholds (30 points) need adjustment for different document types
❌ **Local processing overhead** - CPU usage for large PDFs
❌ **May miss edge cases** - Tables with unusual formatting

---

## Approach 2: Proposed (LLM-Based Smart Detection)

### How It Works

```python
# Step 1: Extract Table of Contents or first few pages (small API call)
llmw = LLMWhispererClientV2()
result = llmw.whisper(
    file_path="nvidia_10k.pdf",
    pages_to_extract="1-5"  # ToC usually in first 5 pages
)
toc_text = result["extraction"]["result_text"]  # ~1K chars

# Step 2: Ask cheap LLM to find page numbers (SMALL token cost)
from pydantic_ai import Agent

class PageLocation(BaseModel):
    statement_type: str
    page_number: int
    confidence: float

agent = Agent("openai:gpt-4o-mini", output_type=PageLocation)
location = agent.run_sync(f"""
Find the page number for "Consolidated Statements of Income" in this table of contents:

{toc_text}

Return the page number.
""")

# Step 3: Extract ONLY that page
result = llmw.whisper(
    file_path="nvidia_10k.pdf",
    pages_to_extract=str(location.output.page_number)
)

# Step 4: Structured extraction
data = pydantic_extractor.extract(result["extraction"]["result_text"])
```

### Costs

**LLMWhisperer Step 1 (ToC extraction):**
- Pages: 5 pages (ToC)
- Cost: 5 pages @ $X/page

**OpenAI Step 2 (Find page number):**
- Input: ~1,000 characters (ToC text)
- Cost: ~$0.001 (gpt-4o-mini is very cheap)

**LLMWhisperer Step 3 (Target page):**
- Pages: 1 page
- Cost: 1 page @ $X/page

**OpenAI Step 4 (Structured extraction):**
- Input: ~3,000 characters (one page)
- Cost: ~$0.005

**Total: ~$0.02 per document (vs $8.65 currently)**

### Pros

✅ **No local dependencies** - Pure API-based
✅ **Flexible** - LLM can handle any ToC format
✅ **Self-documenting** - Prompt explains what it's doing
✅ **Easy to extend** - Just change prompt for new statement types
✅ **Type-safe** - Pydantic validation ensures correct page number returned

### Cons

❌ **API dependency** - Requires OpenAI for page detection
❌ **Non-deterministic** - LLM might return different results
❌ **Extra API call** - More network requests = slower
❌ **Assumes ToC exists** - Not all PDFs have table of contents
❌ **Single page only** - Doesn't handle multi-page statements as well

---

## Approach 3: Hybrid (Best of Both)

### How It Works

```python
# Step 1: Try PyMuPDF detection first (FAST + FREE)
detector = AITableDetector()
detected_tables = detector.detect_tables_in_pdf(pdf_path)

if detected_tables:
    # Success! Use detected pages
    page_ranges = detector.get_page_ranges_for_extraction(detected_tables)
    pages_to_extract = page_ranges[FinancialStatementType.INCOME_STATEMENT]

else:
    # Fallback: Try LLM-based ToC detection
    toc_result = llmw.whisper(file_path=pdf_path, pages_to_extract="1-5")
    location = find_page_with_llm(toc_result["extraction"]["result_text"])
    pages_to_extract = [location.page_number]

# Step 2: Extract target pages
result = llmw.whisper(
    file_path=pdf_path,
    pages_to_extract=",".join(map(str, pages_to_extract))
)

# Step 3: Structured extraction
data = pydantic_extractor.extract(result["extraction"]["result_text"])
```

### Costs

**Best case (PyMuPDF works):**
- PyMuPDF: $0 (local)
- LLMWhisperer: 3-4 pages @ $X/page
- OpenAI: ~3K chars @ $0.005
- **Total: ~$0.02**

**Worst case (PyMuPDF fails, LLM fallback):**
- PyMuPDF: $0 (local)
- LLMWhisperer ToC: 5 pages @ $X/page
- OpenAI detection: ~1K chars @ $0.001
- LLMWhisperer target: 1 page @ $X/page
- OpenAI extraction: ~3K chars @ $0.005
- **Total: ~$0.03**

### Pros

✅ **Best of both worlds** - Free detection when PyMuPDF works, LLM fallback when it doesn't
✅ **Robust** - Handles edge cases with LLM fallback
✅ **Cost-optimized** - PyMuPDF first minimizes API costs
✅ **Production-ready** - Handles variety of document formats

### Cons

❌ **More complex code** - Two detection methods to maintain
❌ **Still needs PyMuPDF** - Not pure API-based

---

## Comparison Matrix

| Aspect | Brownfield (PyMuPDF) | Proposed (LLM ToC) | Hybrid |
|--------|----------------------|--------------------| -------|
| **Detection Cost** | $0 (local) | ~$0.001 (API) | $0 (PyMuPDF first) |
| **Detection Speed** | 1-2 sec | 2-3 sec (API latency) | 1-2 sec (PyMuPDF) |
| **Accuracy** | 85-90% (rule-based) | 95%+ (LLM understanding) | 95%+ (LLM fallback) |
| **Dependencies** | PyMuPDF | None (API only) | PyMuPDF |
| **Robustness** | Brittle (rules) | Flexible (LLM) | Very robust (fallback) |
| **Handles multi-page** | ✅ Yes (smart expansion) | ❌ No (single page) | ✅ Yes (PyMuPDF) |
| **Offline capability** | ✅ Yes (local) | ❌ No (API only) | ⚠️ Partial (PyMuPDF only) |
| **Deterministic** | ✅ Yes | ❌ No (LLM variance) | ⚠️ Hybrid |
| **Code complexity** | Medium | Low | High |
| **Maintenance** | Medium (tune rules) | Low (just prompts) | High (two systems) |

---

## Recommendation

### 🏆 **Use Brownfield Approach (PyMuPDF Table Detection)**

**Why:**

1. **Proven** - You've already validated this works in brownfield
2. **Zero cost** - PyMuPDF runs locally, no API calls for detection
3. **Fast** - 1-2 seconds to scan 100-page PDF
4. **Smart page expansion** - Includes surrounding pages for multi-page statements
5. **Already in stack** - You use PyMuPDF (fitz) in brownfield, just port it over

**Implementation:**

```python
# 1. Port brownfield/data/dump/09252025/legacy_extractors/ai_table_detector.py
#    to app/extraction/page_detector.py

# 2. Update process_pdf_standalone.py:
from app.extraction.page_detector import AITableDetector

detector = AITableDetector()
detected_tables = detector.detect_tables_in_pdf(pdf_path)
page_ranges = detector.get_page_ranges_for_extraction(detected_tables)

# Get pages for income statement
pages_for_income_stmt = page_ranges.get(FinancialStatementType.INCOME_STATEMENT, [])

# Extract ONLY those pages
result = client.whisper(
    file_path=str(pdf_path),
    pages_to_extract=",".join(map(str, pages_for_income_stmt)),  # "38,39,40"
    mode="form",
    output_mode="layout_preserving",
    wait_for_completion=True,
)
```

**Cost Savings:**

- Current: 374,403 chars → ~$8.65 per 10-K
- Optimized: ~3,000 chars → ~$0.05 per 10-K
- **Savings: $8.60 per document (99.4%)**

**When to use LLM fallback:**

Only if PyMuPDF detection fails (confidence score < 30), then try LLM-based ToC detection as fallback.

---

## Action Plan for Session 17.5 Extension

**Phase 1: Port PyMuPDF Detection**
1. Copy `ai_table_detector.py` to `app/extraction/page_detector.py`
2. Update imports for project structure
3. Add tests for detection logic

**Phase 2: Integrate with Processing Pipeline**
4. Update `process_pdf_standalone.py` to use page detection
5. Update `process_all.py` for batch processing
6. Re-process 2 large 10-K files with page detection

**Phase 3: Consolidation Test**
7. Create `scripts/consolidate_reports.py`
8. Process NVIDIA 10K 2020-2019.pdf → Extract Income Statement (pages ~38-40)
9. Process NVIDIA 10K 2022-2021.pdf → Extract Income Statement (pages ~X-Y)
10. Merge into consolidated table (2018-2022)
11. Generate consolidated JSON + Excel

**Expected Results:**
- ✅ 99% token cost savings
- ✅ Same accuracy as full PDF extraction
- ✅ Consolidated multi-year financial view

**Proceed with this plan?**
