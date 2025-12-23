# Create PR for a session with auto-generated body and optional auto-merge
param(
    [Parameter(Mandatory=$true)]
    [int]$SessionNum,

    [Parameter(Mandatory=$false)]
    [switch]$AutoMerge
)

$ErrorActionPreference = "Stop"

# Check if gh CLI is available
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "Error: gh CLI not found" -ForegroundColor Red
    Write-Host "Install from: https://cli.github.com/"
    exit 1
}

# Get current branch
$branchName = git branch --show-current
if ($branchName -eq "main") {
    Write-Host "Error: Cannot create PR from main branch" -ForegroundColor Red
    Write-Host "Switch to your session branch first"
    exit 1
}

Write-Host "Creating PR for Session $SessionNum" -ForegroundColor Green
Write-Host "Branch: $branchName"
Write-Host ""

# Extract session title from JOURNEY.md
$sessionTitle = "Unknown"
if (Test-Path "JOURNEY.md") {
    $line = Get-Content "JOURNEY.md" | Where-Object { $_ -match "^## Session ${SessionNum}:" } | Select-Object -First 1
    if ($line) {
        $sessionTitle = $line -replace "^## Session ${SessionNum}: ", ""
    }
}

if ($sessionTitle -eq "Unknown") {
    Write-Host "Warning: Could not extract session title from JOURNEY.md" -ForegroundColor Yellow
    $sessionTitle = Read-Host "Enter session title"
}

Write-Host "Title: Session ${SessionNum}: $sessionTitle"
Write-Host ""

# Generate PR body
$prBody = @"
## Summary

$(
    $stats = git diff main --stat | Select-Object -Last 1
    $files = (git diff --name-only main | Measure-Object).Count
    "- Changed $files files"
)

### Files Changed
``````
$(git diff --name-status main | Select-Object -First 20 | Out-String)
``````

## Test Plan
- [x] All tests passing
- [x] Code formatted with ruff
- [x] Code linted with ruff
$(
    $testFiles = (git diff --name-only main | Where-Object { $_ -match "test_.*\.py$" } | Measure-Object).Count
    if ($testFiles -gt 0) {
        "- [x] $testFiles test files added/modified"
    }
)

## Technical Highlights

$(git log main..HEAD --pretty=format:"- %s" | Select-Object -First 5 | Out-String)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
"@

Write-Host "PR Body Preview:" -ForegroundColor Yellow
Write-Host "---"
Write-Host $prBody
Write-Host "---"
Write-Host ""

# Confirm
$confirm = Read-Host "Create PR? (y/n)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "Cancelled"
    exit 0
}

# Save PR body to temp file
$tempFile = New-TemporaryFile
$prBody | Out-File -FilePath $tempFile.FullName -Encoding UTF8

# Create PR
$prUrl = & gh pr create `
    --title "Session ${SessionNum}: $sessionTitle" `
    --body-file $tempFile.FullName `
    --base main `
    --head $branchName

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error creating PR" -ForegroundColor Red
    Remove-Item $tempFile.FullName
    exit 1
}

Write-Host "✅ PR created: $prUrl" -ForegroundColor Green

# Extract PR number
$prNum = $prUrl -replace '.*/', ''

# Enable auto-merge if requested
if ($AutoMerge) {
    Write-Host ""
    Write-Host "Enabling auto-merge..."
    & gh pr merge $prNum --auto --squash
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Auto-merge enabled (will merge when CI passes)" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Could not enable auto-merge" -ForegroundColor Yellow
    }
}

# Cleanup
Remove-Item $tempFile.FullName

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  PR Created Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "PR: $prUrl"
Write-Host "Number: #$prNum"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Wait for CI to pass"
if ($AutoMerge) {
    Write-Host "2. PR will auto-merge when CI is green ✅"
} else {
    Write-Host "2. Manually merge PR when ready"
}
Write-Host "3. Linear will be auto-updated via GitHub Actions"
Write-Host "4. Update JOURNEY.md manually or run: .\scripts\update-journey.ps1 $SessionNum"
Write-Host ""
