# Input Directory

## Purpose

This directory stores **production PDF files** for processing by the financial statement extraction pipeline.

## Usage

### CLI Processing

```bash
# Place your PDF in this folder
cp /path/to/company_10k.pdf input/

# Run processing
python scripts/process_pdf_standalone.py input/company_10k.pdf

# Or process multiple PDFs
python scripts/test_end_to_end_pipeline.py input/*.pdf
```

### Web Upload (Future)

When the web interface is available, uploaded PDFs will automatically be moved here after validation.

## File Naming

**Recommended format**: `CompanyName_10K_YYYY.pdf`

Examples:
- `NVIDIA_10K_2024.pdf`
- `Alphabet_10K_2023.pdf`
- `Apple_10K_2022.pdf`

## Important Notes

1. **Not tracked in git**: Files in this directory are ignored by version control
2. **Manual cleanup**: Delete PDFs after processing to save disk space
3. **Security**: Do not store confidential PDFs if sharing this repository
4. **File size**: Keep PDFs under 100MB for optimal processing

## Output Location

Processing results are saved to: `output/runs/YYYYMMDD_HHMMSS_STATUS/`

See `output/runs/latest.txt` for the most recent run.

---

**Directory Type**: Production Data
**Git Status**: Excluded (see .gitignore)
**Created**: 2025-12-28
