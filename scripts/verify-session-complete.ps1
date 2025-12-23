# Verify that a session is fully complete across all systems
param(
    [Parameter(Mandatory=$true)]
    [int]$SessionNum
)

$ErrorActionPreference = "Stop"

$issueId = "BUD-$($SessionNum + 4)"
$passed = 0
$failed = 0

Write-Host ""
Write-Host "Verifying Session $SessionNum completion..." -ForegroundColor Cyan
Write-Host ""

# Check 1: GitHub PR merged
Write-Host "[1/3] Checking GitHub PR..." -ForegroundColor Yellow
try {
    $prJson = & gh pr list --search "Session ${SessionNum}:" --state merged --json number,title,mergedAt --limit 1 | ConvertFrom-Json
    if ($prJson -and $prJson.Count -gt 0) {
        $prNum = $prJson[0].number
        $mergedAt = $prJson[0].mergedAt
        Write-Host "✅ PR #$prNum merged at $mergedAt" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "❌ PR not found or not merged" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "❌ Error checking GitHub: $_" -ForegroundColor Red
    $failed++
    $prNum = $null
}

# Check 2: JOURNEY.md updated
Write-Host "[2/3] Checking JOURNEY.md..." -ForegroundColor Yellow
if ($prNum) {
    $journeyContent = Get-Content "JOURNEY.md" -Raw
    $hasPrLink = $journeyContent -match "\[#$prNum\]"
    $hasLinearStatus = $journeyContent -match "$issueId.*Done"

    if ($hasPrLink -and $hasLinearStatus) {
        Write-Host "✅ JOURNEY.md updated with PR link and Linear status" -ForegroundColor Green
        $passed++
    } else {
        if (-not $hasPrLink) {
            Write-Host "❌ JOURNEY.md missing PR link [#$prNum]" -ForegroundColor Red
        }
        if (-not $hasLinearStatus) {
            Write-Host "❌ JOURNEY.md missing Linear status '$issueId → Done'" -ForegroundColor Red
        }
        $failed++
    }
} else {
    Write-Host "⏭️  Skipped (no PR number)" -ForegroundColor Yellow
}

# Check 3: Linear issue marked Done
Write-Host "[3/3] Checking Linear..." -ForegroundColor Yellow

$env:LINEAR_API_KEY = $env:LINEAR_API_KEY
if (-not $env:LINEAR_API_KEY) {
    Write-Host "⚠️  LINEAR_API_KEY not set, skipping Linear check" -ForegroundColor Yellow
    Write-Host "   Set with: `$env:LINEAR_API_KEY='your_key'" -ForegroundColor Gray
} else {
    try {
        $result = & uv run python scripts/verify-linear.py $SessionNum 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Linear $issueId marked as Done" -ForegroundColor Green
            $passed++
        } else {
            Write-Host "❌ Linear not updated" -ForegroundColor Red
            Write-Host $result -ForegroundColor Gray
            $failed++
        }
    } catch {
        Write-Host "❌ Error checking Linear: $_" -ForegroundColor Red
        $failed++
    }
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Verification Results" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($failed -eq 0) {
    Write-Host "✅ All verifications passed!" -ForegroundColor Green
    Write-Host "Session $SessionNum is complete." -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ Some verifications failed!" -ForegroundColor Red
    Write-Host "Please review and fix the issues above." -ForegroundColor Yellow
    exit 1
}
