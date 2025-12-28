# Uploads Directory

## Purpose

This directory serves as a **temporary staging area** for PDF files uploaded via the web interface.

## Workflow

```
1. User uploads PDF via web interface
   ↓
2. File saved to: uploads/{uuid}.pdf
   ↓
3. Validation checks:
   - PDF format verification (magic bytes)
   - File size check (max 100MB)
   - Virus scanning (future)
   - Filename sanitization
   ↓
4. If valid: Move to input/{sanitized_name}.pdf
   ↓
5. Auto-delete from uploads/ after processing
```

## Automatic Cleanup

Files in this directory are automatically deleted:
- After successful move to `input/` directory
- After 24 hours if validation fails
- After 7 days as a safety cleanup

## Manual Use (Development)

```bash
# Temporarily place files here for upload simulation
cp test.pdf uploads/test.pdf

# Run validation script (future)
python scripts/validate_upload.py uploads/test.pdf
```

## Security

- Files are assigned random UUID names to prevent conflicts
- Original filenames are sanitized to prevent path traversal attacks
- File type validated by content (not just extension)
- Access restricted to authenticated users only

## Important Notes

1. **Not tracked in git**: All files excluded from version control
2. **Temporary storage only**: Do not use for long-term storage
3. **Auto-cleanup**: Files may be deleted automatically
4. **Web-only**: This folder is primarily for web uploads, not CLI usage

---

**Directory Type**: Temporary Staging
**Git Status**: Excluded (see .gitignore)
**Auto-Cleanup**: 24 hours (configurable)
**Created**: 2025-12-28
