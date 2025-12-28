# Archive Directory

## Purpose

Long-term storage for completed processing runs from `output/runs/`.

## When to Archive

Archive runs when:
1. Processing is complete and verified
2. Results have been delivered to stakeholders
3. Need to free up space in `output/runs/`
4. Want to preserve historical runs for audit purposes

## How to Archive

### Manual Archive

```bash
# Move completed run to archive
mv output/runs/20251228_150533_SUCCESS output/archive/

# Or copy to preserve in both locations
cp -r output/runs/20251228_150533_SUCCESS output/archive/
```

### Automated Archival (Future)

```bash
# Archive all runs older than 30 days
python scripts/archive_old_runs.py --days 30

# Archive all successful runs
python scripts/archive_old_runs.py --status SUCCESS
```

## Archive Structure

```
output/archive/
├── 20251201_100000_SUCCESS/
├── 20251215_140000_SUCCESS/
└── 20251228_150533_SUCCESS/
    ├── run_manifest.json
    ├── checksums.md5
    ├── extracted/
    └── consolidated/
```

## Cleanup Policy

**Recommended retention**:
- Keep all runs: 90 days
- Keep successful runs: 1 year
- Keep failed runs: 30 days (for debugging)

**After retention period**:
1. Create backup (optional)
2. Delete from archive
3. Document deletion in audit log

## Disk Space Management

```bash
# Check archive size
du -sh output/archive/

# List largest runs
du -h output/archive/* | sort -h | tail -10

# Delete specific archived run
rm -rf output/archive/20251201_100000_SUCCESS
```

## Important Notes

1. **Not tracked in git**: Excluded from version control
2. **Manual management**: No automatic cleanup by default
3. **Backup recommended**: Consider backing up to cloud storage before deletion
4. **Audit trail**: Document what was archived/deleted and when

## Restoration

To restore an archived run for review:

```bash
# Copy back to runs/ folder
cp -r output/archive/20251228_150533_SUCCESS output/runs/

# Update latest.txt if needed
echo "20251228_150533" > output/runs/latest.txt
```

---

**Directory Type**: Long-term Storage
**Git Status**: Excluded (see .gitignore)
**Retention**: 90 days (recommended)
**Created**: 2025-12-28
