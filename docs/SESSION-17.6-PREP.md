# Session 17.6 Preparation: System Architecture Redesign

**Date**: 2025-12-28
**Status**: Ready to Begin
**Linear**: BUD-24
**Priority**: 🔴 URGENT (Production Blocked)
**Estimated Effort**: 17 hours

---

## Session Overview

**Objective**: Redesign system architecture to prevent data accuracy bugs through 5-layer defense mechanism

**Critical Problem**: Consolidation merges wrong accounts (514 vs 5,261 error)

**Root Cause**: System treats statements as flat lists, ignoring section context and accounting rules

---

## What We're Building

### The 5-Layer Defense Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Layer 5: Confidence Scoring                             │
│ ├─ Different sections = 0.0 confidence                  │
│ └─ Value overlap check                                  │
├─────────────────────────────────────────────────────────┤
│ Layer 4: Quality Gates                                  │
│ ├─ 6 validation stages                                  │
│ └─ Graduated confidence levels                          │
├─────────────────────────────────────────────────────────┤
│ Layer 3: Source Traceability                            │
│ ├─ Track PDF, page, section for every value             │
│ └─ Verify values exist in source                        │
├─────────────────────────────────────────────────────────┤
│ Layer 2: Accounting Rules Validation                    │
│ ├─ Assets = Liabilities + Equity                        │
│ ├─ Beginning Cash + Change = Ending Cash                │
│ └─ Profit margin reasonableness                         │
├─────────────────────────────────────────────────────────┤
│ Layer 1: Hierarchical Data Model                        │
│ ├─ Extract as trees (not flat lists)                    │
│ ├─ Preserve section structure                           │
│ └─ Track parent-child relationships                     │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Roadmap

### Phase 1: Critical Data Integrity (6 hours) 🔴 IMMEDIATE

**Goal**: Prevent wrong data from being output

**Tasks**:

#### Task 1.1: Accounting Rules Validation (2h)
**Create**: `app/validation/accounting_validator.py`

```python
class AccountingValidator:
    """Validate financial statements against accounting principles."""

    def validate_balance_sheet(self, bs: BalanceSheet) -> ValidationResult:
        """Assets must equal Liabilities + Equity."""
        assets = bs.get_total("Total assets")
        liabilities = bs.get_total("Total liabilities")
        equity = bs.get_total("Total stockholders' equity")

        difference = assets - (liabilities + equity)

        if abs(difference) > 1.0:  # Allow $1 rounding
            return ValidationResult(
                passed=False,
                error=f"Accounting equation failed: Assets != Liabilities + Equity"
            )

        return ValidationResult(passed=True)

    def validate_cash_flow(self, cf: CashFlow) -> ValidationResult:
        """Beginning cash + net change = ending cash."""
        # Implementation

    def validate_income_statement(self, is_: IncomeStatement) -> ValidationResult:
        """Profit margin reasonableness check."""
        # Implementation
```

**When to run**:
- After extraction (validate individual PDF)
- After consolidation (validate merged timeline)
- Before marking run as SUCCESS

#### Task 1.2: Source Value Verification (2h)
**Update**: `app/consolidation/consolidator.py`

```python
def verify_source_values(consolidated: dict, sources: list[dict]) -> dict:
    """
    Verify each consolidated value exists in at least one source.

    Returns:
        {
            'errors': [list of values not found in sources],
            'status': 'PASS' or 'FAIL'
        }
    """
    errors = []

    for item in consolidated['line_items']:
        for period, value in item['values'].items():
            found = any(
                value_exists_in_source(value, source, item['account_name'])
                for source in sources
            )

            if not found:
                errors.append({
                    'account': item['account_name'],
                    'period': period,
                    'value': value
                })

    return {
        'errors': errors,
        'status': 'PASS' if not errors else 'FAIL'
    }
```

#### Task 1.3: Quality Gates Implementation (2h)
**Create**: `app/validation/quality_gates.py`

```python
class QualityGate:
    """Multi-stage validation gates."""

    GATES = [
        {
            "name": "Statement Detection",
            "check": lambda run: run.statements_detected >= 5,
            "severity": "CRITICAL"
        },
        {
            "name": "Extraction Completion",
            "check": lambda run: run.failed_extractions == 0,
            "severity": "CRITICAL"
        },
        {
            "name": "Accounting Validation",  # NEW
            "check": lambda run: all(v.passed for v in run.accounting_validations),
            "severity": "CRITICAL"
        },
        {
            "name": "Consolidation Integrity",  # NEW
            "check": lambda run: run.duplicate_section_matches == 0,
            "severity": "CRITICAL"
        },
        {
            "name": "Source Value Verification",  # NEW
            "check": lambda run: all(
                value_exists_in_source(v) for v in run.consolidated_values
            ),
            "severity": "CRITICAL"
        }
    ]

    def evaluate(self, run) -> tuple[RunStatus, str]:
        """Evaluate run against all gates."""
        # Implementation
```

**Update**: `scripts/test_end_to_end_pipeline.py`
- Integrate QualityGate evaluation
- Update SUCCESS criteria
- Add NEEDS_REVIEW and SUCCESS_WITH_WARNINGS statuses

**Acceptance Criteria**:
- [ ] 514 vs 5,261 bug would be caught automatically
- [ ] Run fails if accounting equations don't balance
- [ ] Run fails if consolidated value not in source

---

### Phase 2: Section-Aware Matching (8 hours) 🟡 HIGH PRIORITY

**Goal**: Fix consolidation to respect sections

**Tasks**:

#### Task 2.1: Section Detection (3h)
**Update**: `app/extraction/schemas.py`

```python
class LineItem(BaseModel):
    account_name: str
    values: list[str] | dict[str, str]
    indent_level: int
    section: str | None = None  # NEW
```

**Update**: `app/extraction/pydantic_extractor.py`

```python
def detect_section(account_name: str, previous_accounts: list) -> str:
    """
    Detect which section an account belongs to:
    - Assets
    - Liabilities
    - Equity
    - Operating activities (cash flow)
    - Investing activities
    - Financing activities
    """

    # Section headers
    if re.match(r'^\s*assets?\s*$', account_name, re.I):
        return 'Assets'
    if re.match(r'^\s*liabilities', account_name, re.I):
        return 'Liabilities'
    if re.match(r'^\s*(stockholders?|shareholders?).*equity', account_name, re.I):
        return 'Equity'

    # Inherit from previous accounts
    for prev in reversed(previous_accounts):
        if prev.get('section'):
            return prev['section']

    return 'Unknown'
```

**Update extraction flow**: Add section detection during line item creation

#### Task 2.2: Confidence Scoring (3h)
**Create**: `app/consolidation/confidence_scorer.py`

```python
class ConfidenceScorer:
    """Calculate confidence scores for account matching."""

    def score_match(
        self,
        source_account: dict,
        target_account: dict,
        context: dict
    ) -> tuple[float, dict]:
        """
        Calculate confidence score (0.0-1.0) for matching.

        Factors:
        1. Name similarity (40%)
        2. Section compatibility (30%) - CRITICAL
        3. Indent level (10%)
        4. Value overlap verification (20%)
        """

        scores = {}

        # 1. Name similarity
        name_similarity = fuzz.ratio(
            source_account['account_name'],
            target_account['account_name']
        ) / 100.0
        scores['name'] = name_similarity * 0.40

        # 2. Section match - CRITICAL
        if source_account.get('section') == target_account.get('section'):
            scores['section'] = 0.30
        elif source_account.get('section') and target_account.get('section'):
            # Different sections = ZERO confidence
            scores['section'] = 0.0
        else:
            # Unknown section = medium
            scores['section'] = 0.15

        # 3. Indent level
        indent_diff = abs(
            source_account.get('indent_level', 0) -
            target_account.get('indent_level', 0)
        )
        scores['indent'] = max(0, (1 - indent_diff * 0.2)) * 0.10

        # 4. Value overlap verification
        overlap_score = self._check_value_overlap(source_account, target_account)
        scores['value_overlap'] = overlap_score * 0.20

        total = sum(scores.values())
        return total, scores

    def _check_value_overlap(self, source: dict, target: dict) -> float:
        """If periods overlap, values should match."""
        # Implementation
```

**Confidence Thresholds**:
- >= 0.90: High confidence → auto-merge
- 0.70-0.89: Medium → merge with warning
- < 0.70: Low → manual review required

#### Task 2.3: Update Consolidator (2h)
**Update**: `app/consolidation/consolidator.py`

```python
def find_matching_account(
    target_account: dict,
    source_accounts: list[dict],
    scorer: ConfidenceScorer
) -> dict | None:
    """Find matching account with confidence scoring."""

    candidates = []

    for source_account in source_accounts:
        confidence, scores = scorer.score_match(
            source_account,
            target_account,
            context={}
        )

        if confidence >= 0.70:  # Minimum threshold
            candidates.append({
                'account': source_account,
                'confidence': confidence,
                'scores': scores
            })

    if not candidates:
        return None

    # Return highest confidence match
    best = max(candidates, key=lambda x: x['confidence'])

    # Log if low confidence
    if best['confidence'] < 0.85:
        logger.warning(
            "Low confidence match",
            extra={
                'target': target_account['account_name'],
                'source': best['account']['account_name'],
                'confidence': best['confidence'],
                'scores': best['scores']
            }
        )

    return best['account']
```

**Acceptance Criteria**:
- [ ] Assets "Deferred taxes" != Liabilities "Deferred taxes"
- [ ] Consolidation uses section + name for matching
- [ ] Low confidence matches flagged for review

---

### Phase 3: Re-validation (1 hour) 🔴 CRITICAL

**Goal**: Verify fixes work on real data

**Tasks**:

1. **Re-run Google PDFs** (15 min)
   ```bash
   python scripts/test_end_to_end_pipeline.py --mode production \
     "input/Google 2021-2023.pdf" \
     "input/Google 2022-2024.pdf"
   ```

2. **Manual Verification** (30 min)
   - Check consolidated balance sheet
   - Verify "Deferred income taxes" (Assets) = 5,261 for 2022
   - Verify "Deferred income taxes" (Liabilities) = 514 for 2022 (separate)
   - Check accounting equations balance

3. **Quality Gate Review** (15 min)
   - Review quality gate report
   - Check all gates passed
   - Verify confidence scores

**Acceptance Criteria**:
- [ ] Google consolidated balance sheet shows 5,261 for 2022 (Assets)
- [ ] Assets = Liabilities + Equity (within $1)
- [ ] All quality gates pass
- [ ] Run status = SUCCESS

---

### Phase 4: Automated Tests (2 hours) 🟡 HIGH PRIORITY

**Goal**: Prevent regression

**Test Files to Create**:

#### 1. `tests/validation/test_accounting_validator.py`
```python
def test_balance_sheet_equation():
    """Assets must equal Liabilities + Equity."""

def test_balance_sheet_equation_fails_on_imbalance():
    """Validator catches imbalanced sheets."""

def test_cash_flow_continuity():
    """Beginning + Change = Ending."""
```

#### 2. `tests/consolidation/test_confidence_scorer.py`
```python
def test_different_sections_zero_confidence():
    """Different sections = 0.0 confidence."""

def test_same_section_high_confidence():
    """Same section + similar name = high confidence."""

def test_value_overlap_verification():
    """Overlapping periods with different values = low confidence."""
```

#### 3. `tests/integration/test_quality_gates.py`
```python
def test_quality_gates_block_bad_data():
    """Wrong data results in FAILED status."""

def test_accounting_validation_gate():
    """Imbalanced sheets fail quality gate."""

def test_source_verification_gate():
    """Values not in source fail quality gate."""
```

**Acceptance Criteria**:
- [ ] 10+ new tests covering validation layers
- [ ] All tests pass
- [ ] Coverage >= 80% for new code

---

## Pre-Session Checklist

### Environment Setup
- [ ] Python 3.12 environment active
- [ ] All dependencies installed (`uv sync`)
- [ ] `.env` configured (API keys)
- [ ] Git working directory clean

### Reference Materials
- [ ] `docs/SYSTEM-REDESIGN-data-integrity.md` reviewed
- [ ] `docs/critical-bug-consolidation-duplicate-accounts.md` reviewed
- [ ] Google PDFs available in `input/`
- [ ] Previous run outputs available for comparison

### Tools & Scripts
- [ ] `scripts/test_end_to_end_pipeline.py` functional
- [ ] `scripts/cleanup_failed_runs.py` available
- [ ] Test framework setup (pytest)

---

## Success Criteria

### Phase 1 Complete When:
- [ ] Accounting validator catches imbalanced sheets
- [ ] Source verification catches non-existent values
- [ ] Quality gates block runs with bad data
- [ ] 514 vs 5,261 bug would be caught automatically

### Phase 2 Complete When:
- [ ] Section field added to all line items
- [ ] Confidence scorer gives 0.0 for different sections
- [ ] Consolidator uses confidence >= 0.70 threshold
- [ ] Assets "Deferred taxes" not matched with Liabilities "Deferred taxes"

### Phase 3 Complete When:
- [ ] Google PDFs re-run with new validation
- [ ] Consolidated balance sheet shows correct values
- [ ] All quality gates pass
- [ ] Run status = SUCCESS (not NEEDS_REVIEW)

### Phase 4 Complete When:
- [ ] 10+ tests written and passing
- [ ] Test coverage >= 80%
- [ ] CI/CD integration ready

---

## Expected Deliverables

### New Files
- [ ] `app/validation/accounting_validator.py`
- [ ] `app/validation/quality_gates.py`
- [ ] `app/consolidation/confidence_scorer.py`
- [ ] `tests/validation/test_accounting_validator.py`
- [ ] `tests/consolidation/test_confidence_scorer.py`
- [ ] `tests/integration/test_quality_gates.py`

### Updated Files
- [ ] `app/extraction/schemas.py` (add section field)
- [ ] `app/extraction/pydantic_extractor.py` (section detection)
- [ ] `app/consolidation/consolidator.py` (confidence-based matching)
- [ ] `scripts/test_end_to_end_pipeline.py` (quality gates integration)

### Documentation
- [ ] Update `docs/CLAUDE.md` with validation architecture
- [ ] Update `README.md` with quality gates info
- [ ] Create `docs/SESSION-17.6-SUMMARY.md` when complete

---

## Risk Assessment

### High Risk Items
- [ ] **Breaking changes**: Schema changes may break existing code
- [ ] **Performance**: Additional validation may slow pipeline
- [ ] **False positives**: Too strict validation may reject valid data

### Mitigation Strategies
- **Schema changes**: Update all affected code, add migration if needed
- **Performance**: Profile validation code, optimize if needed
- **False positives**: Use confidence thresholds, manual review for edge cases

---

## Time Allocation

| Phase | Task | Hours | Priority |
|-------|------|-------|----------|
| 1 | Accounting Validator | 2 | 🔴 Critical |
| 1 | Source Verification | 2 | 🔴 Critical |
| 1 | Quality Gates | 2 | 🔴 Critical |
| 2 | Section Detection | 3 | 🟡 High |
| 2 | Confidence Scorer | 3 | 🟡 High |
| 2 | Update Consolidator | 2 | 🟡 High |
| 3 | Re-validation | 1 | 🔴 Critical |
| 4 | Automated Tests | 2 | 🟡 High |
| **Total** | | **17** | |

---

## Next Steps After 17.6

**If Phase 1+2 Complete**:
- ✅ Production deployment unblocked
- → Move to deployment preparation (Session 18?)

**If Only Phase 1 Complete**:
- ⚠️ Production still blocked (section-aware matching needed)
- → Continue with Phase 2 in follow-up session

**Future Enhancements** (Session 18+):
- Hierarchical tree data model (Layer 1)
- Source traceability metadata (Layer 3)
- Advanced confidence weighting
- Machine learning for pattern recognition

---

**Prepared by**: Claude Sonnet 4.5
**Date**: 2025-12-28
**Status**: Ready to Begin
**Linear**: BUD-24 (Todo)
**Previous Session**: 17.5 (BUD-23, Done)
