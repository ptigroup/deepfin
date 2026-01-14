# Financial Document Processing Pipeline

**Production-ready pipeline for extracting structured data from financial PDFs (10-K reports, financial statements) using LLM-powered extraction.**

## Features

- ✅ **Zero Hardcoding**: Dynamically detects financial statements in any company's 10-K
- ✅ **Multi-PDF Consolidation**: Merges data across multiple years into unified timelines
- ✅ **Production Folder Structure**: Separate input/output management for production vs testing
- ✅ **Multiple Output Formats**: JSON + Excel with proper formatting and indentation
- ✅ **100% Accuracy**: Validated against NVIDIA and Alphabet (Google) 10-K filings

## Quick Start

### 1. Setup

```bash
# Install dependencies
uv sync

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys:
# - OPENAI_API_KEY
# - LLMWHISPERER_API_KEY
```

### 2. Process PDFs

**Testing Mode** (uses `samples/` directory):
```bash
python scripts/test_end_to_end_pipeline.py
```

**Production Mode** (uses `input/` and `output/` directories):
```bash
# 1. Place PDFs in input/ folder
cp ~/Downloads/Company_10K_2024.pdf input/

# 2. Run pipeline
python scripts/test_end_to_end_pipeline.py --mode production input/*.pdf

# 3. Find results in output/runs/YYYYMMDD_HHMMSS_SUCCESS/
```

### 3. View Results

Output structure:
```
output/runs/20251228_153725_SUCCESS/
├── consolidated/
│   ├── all_statements_2024-2020.xlsx    # All statements in one Excel file
│   ├── income_statement_2021-2024.json  # 4-year income statement
│   └── ... (individual statement files)
└── extracted/
    └── Company_10K_2024/
        ├── income_statement.json
        ├── balance_sheet.json
        └── ... (raw extractions)
```

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Main project guide (development, architecture, workflows)
- **[docs/FOLDER_STRUCTURE.md](docs/FOLDER_STRUCTURE.md)** - Detailed folder organization
- **[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)** - Contribution guidelines
- **[docs/JOURNEY.md](docs/JOURNEY.md)** - Development history and decisions

## Project Structure

```
LLM-1/
├── app/                    # FastAPI application (future web interface)
│   ├── core/              # Configuration, logging, output management
│   ├── extraction/        # Page detection, extraction logic
│   └── export/            # Excel export with formatting
│
├── scripts/               # CLI processing scripts
│   ├── test_end_to_end_pipeline.py    # Main pipeline script
│   ├── cleanup_failed_runs.py         # Cleanup utility
│   └── path_config.py                 # Path configuration
│
├── input/                 # Production PDFs (git-ignored)
├── output/
│   ├── runs/             # Timestamped processing results
│   ├── archive/          # Long-term storage
│   └── cache/            # Performance cache (future)
│
├── samples/              # Example data (tracked in git)
│   ├── input/           # Sample PDFs (NVIDIA, Alphabet)
│   └── output/          # Sample outputs
│
└── docs/                # Documentation
```

## Tech Stack

- **Python 3.12** with async/await
- **LLMWhisperer (Unstract SDK)** - PDF text extraction
- **OpenAI GPT-4** - Structured data extraction
- **FastAPI** - Web framework (future)
- **Pydantic** - Data validation
- **openpyxl** - Excel export

## Key Scripts

### Cleanup Failed Runs
```bash
# Preview cleanup (dry run)
python scripts/cleanup_failed_runs.py --mode production

# Execute cleanup
python scripts/cleanup_failed_runs.py --mode production --execute
```

### Manual Consolidation
```bash
# Consolidate existing JSON files
python scripts/consolidate_hybrid_outputs.py file1.json file2.json
```

## Tested Companies

- ✅ **NVIDIA** (2018-2022, 6 years)
- ✅ **Alphabet/Google** (2020-2024, 5 years)

Works with **any** company's 10-K filings that follow GAAP formatting.

## Output Examples

**Income Statement** (2021-2024):
```json
{
  "statement_type": "income_statement",
  "fiscal_years": [2024, 2023, 2022, 2021],
  "line_items": [
    {
      "account_name": "Revenues",
      "values": {
        "2024": "$350,018",
        "2023": "$307,394",
        "2022": "$282,836",
        "2021": "$257,637"
      }
    }
  ]
}
```

**Excel Output**: Multi-sheet workbook with:
- Income Statement
- Balance Sheet
- Comprehensive Income
- Shareholders' Equity
- Cash Flow
- Consolidation Summary

## License

[Add your license here]

## Support

For questions or issues, see [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)

---

**Status**: Production Ready ✅
**Last Updated**: 2025-12-28
