# Financial Document Processing Samples

This directory contains sample PDFs and outputs from Session 17.5 End-to-End Validation.

## Purpose

Session 17.5 validates that the refactored `/app` codebase can process real financial documents end-to-end, producing the same quality outputs as the brownfield implementation.

## Directory Structure

```
samples/
├── input/              # Sample PDF files (7 financial statements)
├── output/
│   ├── json/          # Structured JSON outputs
│   ├── excel/         # Formatted Excel spreadsheets
│   ├── metadata/      # Processing metadata (timing, confidence)
│   └── raw_text/      # LLMWhisperer raw text extraction
└── README.md          # This file
```

## Sample Documents

### 1. Single Statement PDFs (5 files)
From NVIDIA's 2020 10-K Annual Report:

- **balance_sheet.pdf** (158 KB)
  - Document type: balance_sheet
  - Periods: 2 (2020, 2019)
  - Line items: 34

- **cashflow_statement.pdf** (179 KB)
  - Document type: cash_flow
  - Periods: 3 (2020, 2019, 2018)
  - Line items: 35

- **comprehensive_income.pdf** (72 KB)
  - Document type: comprehensive_income
  - Periods: 3 (2020, 2019, 2018)
  - Line items: 12

- **income_statement.pdf** (96 KB)
  - Document type: income_statement
  - Periods: 3 (2020, 2019, 2018)
  - Line items: 21

- **shareholder_equity.pdf** (196 KB)
  - Document type: shareholders_equity
  - Periods: 4 (beginning balance, changes, ending balance)
  - Line items: 35

### 2. Complete 10-K Reports (2 files)
Full annual reports with multiple financial statements:

- **NVIDIA 10K 2020-2019.pdf** (747 KB)
  - 374,403 characters of text extracted
  - Extracting: Income statement section
  - Processing time: ~63 seconds

- **NVIDIA 10K 2022-2021.pdf** (1.0 MB)
  - 577,496 characters of text extracted
  - Extracting: Income statement section
  - Processing time: ~186 seconds

## Processing Pipeline

### Step 1: LLMWhisperer V2 Extraction
- **API**: Unstract LLMWhisperer V2
- **Mode**: `form` (table-aware extraction)
- **Output**: Layout-preserving plain text
- **Average time**: 15-20 seconds per PDF

### Step 2: Pydantic AI Structured Extraction
- **Model**: OpenAI GPT-4o-mini
- **Framework**: Pydantic AI 0.8.1
- **Output**: Type-safe validated financial data
- **Average time**: 10-50 seconds (depends on document size)

### Step 3: Output Generation
- **JSON**: Structured data with metadata
- **Excel**: Formatted spreadsheet with indentation
- **Metadata**: Processing stats and confidence scores

## Usage

### Process Single PDF

```bash
# From project root
uv run python scripts/process_pdf_standalone.py "samples/input/income statement.pdf"

# Outputs:
# - samples/output/json/income statement.json
# - samples/output/excel/income statement.xlsx
# - samples/output/metadata/income statement_metadata.json
# - samples/output/raw_text/income statement_raw.txt
```

### Process All Samples (Batch)

```bash
# From project root
uv run python scripts/process_all.py

# Results:
# - All 7 PDFs processed sequentially
# - Summary report with statistics
# - Total time: ~8 minutes for all 7 PDFs
```

## Validation Results

### Session 17.5 Summary (2025-12-27)

**Processing Stats:**
- Total PDFs: 7
- Successful: 7 (100%)
- Failed: 0
- Total time: 479.94 seconds (~8 minutes)
- Average time: 68.53 seconds per PDF

**Extraction Stats:**
- Total periods extracted: 21
- Total line items extracted: 173
- Document types detected: 5 unique types
- Indentation levels preserved: 0-2 (main, sub, totals)

**Document Type Distribution:**
- balance_sheet: 1 PDF
- cash_flow: 1 PDF
- comprehensive_income: 1 PDF
- income_statement: 3 PDFs
- shareholders_equity: 1 PDF

### Key Achievements

1. **LLMWhisperer V2 Integration**
   - Successfully migrated from V1 to V2 API
   - Correct endpoint: `https://llmwhisperer-api.us-central.unstract.com/api/v2`
   - Proper response parsing: `result["extraction"]["result_text"]`

2. **Pydantic AI Extraction**
   - Type-safe extraction with validation
   - Automatic document type detection
   - Proper indentation level inference
   - Data preservation (account names, values, formatting)

3. **Output Quality**
   - JSON: Structured data with metadata
   - Excel: Formatted with visual indentation
   - Metadata: Processing time, confidence, line counts

4. **Scalability**
   - Handles large documents (577K characters)
   - Batch processing with summary reports
   - Error handling with retries

## Output Format Examples

### JSON Output

```json
{
  "metadata": {
    "pdf_name": "income statement.pdf",
    "document_type": "income_statement",
    "company_name": "NVIDIA CORPORATION AND SUBSIDIARIES",
    "fiscal_year": "2020",
    "processing_time_seconds": 49.93,
    "periods_count": 3,
    "line_items_count": 21
  },
  "data": {
    "company_name": "NVIDIA CORPORATION AND SUBSIDIARIES",
    "statement_type": "income_statement",
    "periods": ["January 26, 2020", "January 27, 2019", "January 28, 2018"],
    "line_items": [
      {
        "account_name": "Revenue",
        "values": ["$        10,918", "$        11,716", "$           9,714"],
        "indent_level": 0
      },
      {
        "account_name": "     Cost of revenue",
        "values": ["4,150", "4,545", "3,892"],
        "indent_level": 1
      }
    ]
  }
}
```

### Excel Output

The Excel files contain formatted spreadsheets with:
- **Header row**: Period labels (dates)
- **Account column**: Account names with visual indentation
- **Value columns**: Financial values aligned right
- **Formatting**: Bold headers, proper column widths

## Technology Stack

- **Python**: 3.12+
- **LLMWhisperer**: Unstract SDK 0.79+ (V2 API)
- **Pydantic AI**: 0.8.1
- **OpenAI**: gpt-4o-mini
- **openpyxl**: Excel generation
- **Pydantic**: 2.10+ data validation

## Environment Variables Required

```bash
# .env file
OPENAI_API_KEY=sk-...           # OpenAI API key for Pydantic AI
LLMWHISPERER_API_KEY=...        # Unstract LLMWhisperer API key
```

## Troubleshooting

### Issue: Import errors
**Solution**: Run `uv sync` to install all dependencies

### Issue: API authentication failures
**Solution**: Check `.env` file has both API keys set

### Issue: Empty extractions
**Solution**: Verify using correct response key (`result_text` not `result`)

### Issue: Unicode encoding errors (Windows)
**Status**: Known issue with Windows console, does not affect output files

## Next Steps

After Session 17.5 validation:
- Session 18: Production deployment setup
- CI/CD pipeline configuration
- Docker containerization
- API endpoint integration with `/app/main.py`

## References

- **LLMWhisperer Docs**: `reference/llmwhisperer/`
- **Project Guide**: `CLAUDE.md`
- **Session History**: `JOURNEY.md`
- **Pydantic AI Docs**: https://ai.pydantic.dev/

---

**Session**: 17.5 (End-to-End Validation)
**Date**: 2025-12-27
**Status**: ✅ Complete - All 7 PDFs processed successfully
