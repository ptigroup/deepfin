# Production Folder Structure

## Design Principles

1. **Separation of Concerns**: Sample data vs production data
2. **Web Upload Ready**: Structure supports future web interface
3. **Traceability**: All processing runs tracked with timestamps
4. **Security**: User data excluded from git
5. **Cleanup**: Easy to archive/delete old runs

---

## Folder Structure

```
LLM-1/
│
├── input/                          # PRODUCTION: User PDF files for processing
│   ├── README.md                   # Usage instructions
│   └── .gitkeep                    # Track folder in git
│
├── uploads/                        # STAGING: Temporary upload area (web interface)
│   ├── README.md                   # Explains temp file handling
│   └── .gitkeep
│
├── output/                         # PRODUCTION: All processing outputs
│   ├── runs/                       # Timestamped processing runs
│   │   ├── 20251228_150533_SUCCESS/
│   │   ├── 20251228_160000_PARTIAL/
│   │   └── latest.txt              # Points to latest run ID
│   ├── archive/                    # Old runs (manual move)
│   └── cache/                      # Performance cache (future)
│       ├── llmwhisperer/           # Cached PDF extractions
│       └── page_detection/         # Cached page detection results
│
├── samples/                        # EXAMPLES ONLY: Test data & documentation
│   ├── input/                      # Example PDFs for testing
│   │   ├── NVIDIA 10K 2020-2019.pdf
│   │   ├── NVIDIA 10K 2022-2021.pdf
│   │   └── Alphabet 10K 2024.pdf
│   └── output/                     # Example outputs
│       └── runs/
│
├── scripts/                        # Processing scripts
│   ├── process_pdf_standalone.py
│   ├── test_end_to_end_pipeline.py
│   └── config.py                   # NEW: Path configuration
│
├── app/                            # FastAPI application
│   ├── core/
│   │   └── config.py              # Environment-based config
│   └── ...
│
└── .gitignore                      # Exclude user data

```

---

## Folder Descriptions

### `input/` - Production Input
- **Purpose**: Store PDF files for actual processing
- **Source**: User uploads (CLI or web interface)
- **Git**: Excluded (user data)
- **Cleanup**: Manual deletion after processing
- **Example**: `input/CompanyX_10K_2024.pdf`

### `uploads/` - Temporary Staging
- **Purpose**: Temporary storage for web uploads before validation
- **Source**: Web interface multipart uploads
- **Git**: Excluded
- **Cleanup**: Auto-delete after 24 hours or after move to `input/`
- **Workflow**:
  1. User uploads via web → Saved to `uploads/{uuid}.pdf`
  2. Validation checks (file size, PDF format, virus scan)
  3. Move to `input/{sanitized_name}.pdf`
  4. Delete from `uploads/`

### `output/runs/` - Processing Results
- **Purpose**: All processing outputs organized by run timestamp
- **Git**: Excluded (generated data)
- **Structure**: `YYYYMMDD_HHMMSS_{STATUS}/`
  - STATUS: `SUCCESS`, `PARTIAL`, `FAILED`, `IN_PROGRESS`
- **Contents**:
  ```
  20251228_150533_SUCCESS/
  ├── run_manifest.json          # Metadata, costs, timing
  ├── checksums.md5               # File integrity
  ├── extracted/                  # Per-PDF outputs
  │   └── Company_10K_YYYY/
  │       ├── income_statement.json
  │       ├── balance_sheet.json
  │       ├── raw_text.txt
  │       └── metadata.json
  └── consolidated/               # Multi-PDF consolidation
      ├── all_statements_YYYY-YYYY.xlsx
      └── all_statements_YYYY-YYYY.json
  ```

### `output/archive/` - Completed Runs
- **Purpose**: Manual archival of old runs
- **Git**: Excluded
- **Workflow**: User manually moves runs from `runs/` to `archive/` for long-term storage

### `output/cache/` - Performance Cache
- **Purpose**: Cache API responses to reduce costs and improve performance
- **Git**: Excluded (generated data)
- **Subdirectories**:
  - `llmwhisperer/`: Cached PDF text extractions
  - `page_detection/`: Cached page detection results
- **Status**: Not yet implemented (planned optimization)
- **Benefits**:
  - Reduce LLMWhisperer API calls when re-processing same PDFs
  - Speed up page detection for previously scanned files
  - Lower processing costs for debugging/testing

### `samples/` - Examples & Testing
- **Purpose**: Example data for documentation, testing, demos
- **Git**: **Included** (committed to repository)
- **Usage**:
  - CI/CD testing
  - Documentation examples
  - Developer onboarding
  - Demo purposes

---

## Configuration

### Environment Variables

```bash
# Production
INPUT_DIR=input/
UPLOAD_DIR=uploads/
OUTPUT_DIR=output/runs/
ARCHIVE_DIR=output/archive/

# Development/Testing
INPUT_DIR=samples/input/
OUTPUT_DIR=samples/output/runs/
```

### Script Usage

```bash
# Production: Process from input/ folder
python scripts/process_pdf_standalone.py input/Company_10K_2024.pdf

# Testing: Process from samples/ folder
python scripts/process_pdf_standalone.py samples/input/NVIDIA_10K_2022-2021.pdf

# Auto-detect based on path
python scripts/test_end_to_end_pipeline.py "input/*.pdf"  # Production
python scripts/test_end_to_end_pipeline.py               # Testing (samples)
```

---

## Web Upload Workflow (Future)

### API Endpoints

1. **POST /api/upload**
   - Receives multipart/form-data PDF upload
   - Saves to `uploads/{uuid}.pdf`
   - Returns upload ID
   - Max size: 100MB

2. **POST /api/process**
   - Validates uploaded file
   - Moves to `input/`
   - Starts background job
   - Returns job ID

3. **GET /api/jobs/{job_id}**
   - Returns processing status
   - Links to output when complete

4. **GET /api/download/{run_id}/{file_path}**
   - Downloads specific output file
   - Authenticated access only

### Security Considerations

1. **File Validation**:
   - Check magic bytes (PDF signature: `%PDF-`)
   - Max file size: 100MB
   - Virus scanning (ClamAV integration)
   - Filename sanitization (prevent path traversal)

2. **Access Control**:
   - JWT authentication required
   - Users can only access their own uploads/outputs
   - Rate limiting on uploads (10/hour per user)

3. **Cleanup**:
   - Auto-delete `uploads/` files older than 24 hours
   - Auto-delete `output/runs/` older than 30 days (configurable)
   - User notification before deletion

---

## Migration Plan

### Phase 1: Create Structure (Current)
- Create `input/`, `uploads/`, `output/archive/` folders
- Add README files with usage instructions
- Update `.gitignore`

### Phase 2: Update Scripts
- Add `scripts/config.py` for path configuration
- Update pipeline scripts to use config paths
- Add `--input-dir` and `--output-dir` CLI flags

### Phase 3: Testing
- Test with production paths
- Validate samples still work
- Document usage in README.md

### Phase 4: Web Integration (Future)
- Implement upload endpoints
- Add file validation
- Implement cleanup cron jobs

---

## .gitignore Rules

```gitignore
# User data (never commit)
/input/
/uploads/
/output/runs/
/output/archive/

# Keep folder structure
!**/.gitkeep
!**/README.md

# Keep samples (for testing/examples)
!/samples/
```

---

## Maintenance

### Daily
- Monitor `uploads/` size
- Auto-cleanup stale uploads (>24h)

### Weekly
- Review failed runs in `output/runs/`
- Archive successful runs to `output/archive/`

### Monthly
- Delete `output/archive/` runs older than 90 days (after backup)
- Audit disk usage

---

**Created**: 2025-12-28
**Status**: Ready for implementation
