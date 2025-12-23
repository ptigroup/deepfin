# Master script to complete a session - ONE command does everything
param(
    [Parameter(Mandatory=$true)]
    [int]$SessionNum,

    [Parameter(Mandatory=$false)]
    [switch]$SkipValidation,

    [Parameter(Mandatory=$false)]
    [switch]$NoAutoMerge
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Session $SessionNum Completion Workflow" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$startTime = Get-Date

# Step 1: Run validation
if (-not $SkipValidation) {
    Write-Host "[1/6] Running validation..." -ForegroundColor Yellow
    Write-Host ""

    # Format check
    Write-Host "  → Running ruff format..." -ForegroundColor Gray
    & uv run ruff format app/ --check
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[X] Format check failed" -ForegroundColor Red
        Write-Host "Run: uv run ruff format app/" -ForegroundColor Yellow
        exit 1
    }

    # Linting
    Write-Host "  → Running ruff check..." -ForegroundColor Gray
    & uv run ruff check app/
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[X] Linting failed" -ForegroundColor Red
        Write-Host "Run: uv run ruff check app/ --fix" -ForegroundColor Yellow
        exit 1
    }

    # Tests
    Write-Host "  → Running pytest..." -ForegroundColor Gray
    & uv run pytest app/ -v --tb=short
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[X] Tests failed" -ForegroundColor Red
        exit 1
    }

    Write-Host "[OK] Validation passed" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[1/6] Skipping validation (--SkipValidation)" -ForegroundColor Yellow
    Write-Host ""
}

# Step 2: Create PR
Write-Host "[2/6] Creating PR..." -ForegroundColor Yellow
Write-Host ""

if ($NoAutoMerge) {
    & .\scripts\create-session-pr.ps1 -SessionNum $SessionNum
} else {
    & .\scripts\create-session-pr.ps1 -SessionNum $SessionNum -AutoMerge
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] PR creation failed" -ForegroundColor Red
    exit 1
}

# Extract PR number from gh CLI
$prJson = & gh pr list --head $(git branch --show-current) --json number --limit 1 | ConvertFrom-Json
if (-not $prJson -or $prJson.Count -eq 0) {
    Write-Host "[X] Could not find PR" -ForegroundColor Red
    exit 1
}
$prNum = $prJson[0].number

Write-Host "[OK] PR #$prNum created" -ForegroundColor Green
Write-Host ""

# Step 3: Wait for CI
Write-Host "[3/6] Waiting for CI to pass..." -ForegroundColor Yellow
Write-Host ""

$maxWait = 300  # 5 minutes
$waited = 0
$checkInterval = 10

while ($waited -lt $maxWait) {
    $checks = & gh pr checks $prNum --json state,name,conclusion 2>&1 | ConvertFrom-Json

    if ($checks) {
        $allPassed = $true
        $anyFailed = $false

        foreach ($check in $checks) {
            if ($check.state -eq "COMPLETED") {
                if ($check.conclusion -eq "SUCCESS") {
                    Write-Host "  ✓ $($check.name)" -ForegroundColor Green
                } else {
                    Write-Host "  ✗ $($check.name): $($check.conclusion)" -ForegroundColor Red
                    $anyFailed = $true
                }
            } else {
                Write-Host "  ⋯ $($check.name): $($check.state)" -ForegroundColor Yellow
                $allPassed = $false
            }
        }

        if ($anyFailed) {
            Write-Host ""
            Write-Host "[X] CI failed - aborting" -ForegroundColor Red
            Write-Host "View details: gh pr checks $prNum" -ForegroundColor Yellow
            exit 1
        }

        if ($allPassed) {
            Write-Host ""
            Write-Host "[OK] CI passed" -ForegroundColor Green
            break
        }
    }

    Start-Sleep -Seconds $checkInterval
    $waited += $checkInterval

    if ($waited % 30 -eq 0) {
        Write-Host "  ... still waiting ($waited seconds)" -ForegroundColor Gray
    }
}

if ($waited -ge $maxWait) {
    Write-Host "[WARNING] CI timeout after $maxWait seconds" -ForegroundColor Yellow
    Write-Host "Check status manually: gh pr checks $prNum" -ForegroundColor Yellow
}

Write-Host ""

# Step 4: Wait for auto-merge (if enabled)
if (-not $NoAutoMerge) {
    Write-Host "[4/6] Waiting for auto-merge..." -ForegroundColor Yellow
    Write-Host ""

    $maxWait = 60  # 1 minute
    $waited = 0

    while ($waited -lt $maxWait) {
        $prState = & gh pr view $prNum --json state -q '.state'

        if ($prState -eq "MERGED") {
            Write-Host "[OK] PR auto-merged" -ForegroundColor Green
            break
        }

        Start-Sleep -Seconds 5
        $waited += 5
    }

    if ($prState -ne "MERGED") {
        Write-Host "[WARNING] PR not auto-merged yet" -ForegroundColor Yellow
        Write-Host "You may need to merge manually" -ForegroundColor Yellow
    }

    Write-Host ""
} else {
    Write-Host "[4/6] Skipping auto-merge (--NoAutoMerge)" -ForegroundColor Yellow
    Write-Host ""
}

# Step 5: Update local main
Write-Host "[5/6] Updating local main branch..." -ForegroundColor Yellow
& git checkout main
& git pull
Write-Host "[OK] Local main updated" -ForegroundColor Green
Write-Host ""

# Step 6: Verify completion
Write-Host "[6/6] Verifying completion..." -ForegroundColor Yellow
Write-Host ""

Start-Sleep -Seconds 5  # Wait for GitHub Actions to trigger

& .\scripts\verify-session-complete.ps1 -SessionNum $SessionNum

$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Session $SessionNum Complete!" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Time taken: $([math]::Round($duration, 1)) seconds" -ForegroundColor Gray
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Verify Linear was updated (may take 1-2 minutes)"
Write-Host "2. Update JOURNEY.md with detailed content"
Write-Host "3. Start Session $($SessionNum + 1)" -ForegroundColor Green
Write-Host ""
