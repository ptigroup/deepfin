# Session 17.6 REVISED: Fix Pydantic Extraction to Preserve Hierarchy

**Date**: 2025-12-28
**Status**: Ready to Begin
**Linear**: BUD-24 (will update)
**Priority**: 🔴 URGENT
**Estimated Effort**: 8 hours (down from 17!)

---

## Critical Insight

**The raw text from LLMWhisperer IS CORRECT** ✅

The problem is in our **Pydantic extraction layer** which flattens the hierarchy:
- LLMWhisperer gives us: Tree structure with sections
- Our Pydantic schema asks for: Flat list of line items
- OpenAI obediently flattens it: Loses section context

**Fix**: Update Pydantic schema + prompt to preserve sections

---

## Root Cause (Confirmed)

### LLMWhisperer Output (raw_text.txt) ✅ CORRECT

```
Assets                                         ← SECTION HEADER
Current assets:                                ← SUB-SECTION
    Cash and cash equivalents      $ 23,466   ← INDENTED ITEM
    Marketable securities             72,191
         Total current assets        163,711

Non-marketable securities              37,982  ← TOP-LEVEL (under Assets)
Deferred income taxes                  17,180  ← TOP-LEVEL (under Assets)

Liabilities                                    ← SECTION HEADER
...
Deferred income taxes                     514  ← TOP-LEVEL (under Liabilities)
```

**Structure preserved**: Sections, indentation, hierarchy all present!

### Our Pydantic Schema ❌ WRONG

```python
class FinancialStatement(BaseModel):
    line_items: list[FinancialLineItem]  # FLAT LIST - loses section context!
```

### What OpenAI Extracts

```python
line_items = [
    {"account_name": "Assets", "values": [], "indent": 0},
    {"account_name": "Deferred income taxes", "values": ["17,180"], "indent": 1},  # Assets
    {"account_name": "Liabilities", "values": [], "indent": 0},
    {"account_name": "Deferred income taxes", "values": ["514"], "indent": 1},      # Liabilities
]
```

**Problem**: Both have same name and indent! No way to tell them apart!

---

## The Fix: Hierarchical Pydantic Schema

### New Schema Structure

```python
class FinancialLineItem(BaseModel):
    """A line item with section context."""
    account_name: str
    values: list[str]
    indent_level: int
    section_path: str | None = None  # NEW: "Assets/Non-current"

class FinancialSection(BaseModel):
    """A section with nested items and subsections."""
    name: str  # "Assets", "Liabilities", "Operating activities"
    line_items: list[FinancialLineItem] = []
    subsections: list['FinancialSection'] = []  # Nested sections

class FinancialStatement(BaseModel):
    """Statement with hierarchical sections."""
    company_name: str
    statement_type: str
    fiscal_year: str | None
    currency: str
    periods: list[str]
    sections: list[FinancialSection]  # NEW: Hierarchical, not flat!
```

### Updated Extraction Prompt

```python
system_prompt="""You are a financial data extraction expert.

Your task: Extract financial statement data PRESERVING HIERARCHICAL STRUCTURE.

CRITICAL RULES:
1. Identify SECTION HEADERS (Assets, Liabilities, Equity, Operating/Investing/Financing activities)
2. Group line items under their parent section
3. Preserve subsections (e.g., "Current assets" under "Assets")
4. Track section path for each item (e.g., "Assets/Current/Cash")
5. Preserve exact account names, values, indentation

HIERARCHICAL STRUCTURE EXAMPLE:

Raw text:
Assets
Current assets:
    Cash and cash equivalents      $ 23,466
    Marketable securities             72,191
Non-marketable securities              37,982
Deferred income taxes                  17,180

Liabilities
Deferred income taxes                     514

Extract as:
{
  "sections": [
    {
      "name": "Assets",
      "subsections": [
        {
          "name": "Current assets",
          "line_items": [
            {"account_name": "Cash and cash equivalents", "values": ["$ 23,466"], "section_path": "Assets/Current assets"},
            {"account_name": "Marketable securities", "values": ["72,191"], "section_path": "Assets/Current assets"}
          ]
        }
      ],
      "line_items": [
        {"account_name": "Non-marketable securities", "values": ["37,982"], "section_path": "Assets"},
        {"account_name": "Deferred income taxes", "values": ["17,180"], "section_path": "Assets"}
      ]
    },
    {
      "name": "Liabilities",
      "line_items": [
        {"account_name": "Deferred income taxes", "values": ["514"], "section_path": "Liabilities"}
      ]
    }
  ]
}

KEY: "Deferred income taxes" appears in TWO sections with DIFFERENT paths:
- "Assets/Deferred income taxes" (value: 17,180)
- "Liabilities/Deferred income taxes" (value: 514)

These are DIFFERENT accounts!
"""
```

---

## Implementation Plan

### Phase 1: Update Pydantic Schema (3 hours)

**Task 1.1**: Define Hierarchical Schema (1h)
- Create `FinancialSection` class
- Update `FinancialLineItem` to include `section_path`
- Update `FinancialStatement` to use sections

**Task 1.2**: Update System Prompt (1h)
- Add section detection instructions
- Add hierarchical structure examples
- Emphasize section path importance

**Task 1.3**: Test on Single PDF (1h)
- Extract Google balance sheet
- Verify sections created correctly
- Check "Deferred income taxes" has different paths

**Files**:
- `app/extraction/schemas.py` - Update schemas
- `app/extraction/pydantic_extractor.py` - Update prompt

---

### Phase 2: Update Consolidation (3 hours)

**Task 2.1**: Section-Aware Merger (2h)

```python
def consolidate_by_section_path(statements: list[FinancialStatement]) -> dict:
    """
    Consolidate by section_path instead of fuzzy name matching.

    Example:
    PDF1: "Assets/Deferred taxes" = 5,261
    PDF2: "Assets/Deferred taxes" = 12,169
    → Match by path, merge values

    PDF1: "Assets/Deferred taxes" = 5,261
    PDF2: "Liabilities/Deferred taxes" = 514
    → Different paths, DON'T merge
    """

    merged = {}

    for statement in statements:
        for section in statement.sections:
            for item in section.get_all_items():  # Flattens tree to get all items
                path = item.section_path

                if path in merged:
                    # Same path = same account → merge values
                    merged[path].merge_values(item.values)
                else:
                    # New path = new account → add
                    merged[path] = item

    return merged
```

**Task 2.2**: Remove Fuzzy Matching (1h)
- Remove confidence scoring (not needed!)
- Remove section detection (already in schema!)
- Simplify merger logic

**Files**:
- `app/consolidation/consolidator.py` - Update merge logic
- Remove `app/consolidation/confidence_scorer.py` (not needed anymore!)

---

### Phase 3: Add Accounting Validation (1 hour)

**Task 3.1**: Balance Sheet Equation

```python
class AccountingValidator:
    def validate_balance_sheet(self, bs: FinancialStatement) -> ValidationResult:
        """Assets = Liabilities + Equity."""

        # Sum all items in Assets section
        assets = sum_section(bs.get_section("Assets"))

        # Sum all items in Liabilities section
        liabilities = sum_section(bs.get_section("Liabilities"))

        # Sum all items in Equity section
        equity = sum_section(bs.get_section("Stockholders' equity") or
                           bs.get_section("Shareholders' equity"))

        diff = abs(assets - (liabilities + equity))

        if diff > 1.0:  # Allow $1 rounding
            return ValidationResult(
                passed=False,
                error=f"Accounting equation failed: {assets:,.0f} != {liabilities:,.0f} + {equity:,.0f}"
            )

        return ValidationResult(passed=True)
```

**Files**:
- `app/validation/accounting_validator.py` - NEW

---

### Phase 4: Re-validate & Test (1 hour)

**Task 4.1**: Re-run Google PDFs (30 min)
```bash
python scripts/test_end_to_end_pipeline.py --mode production \
  "input/Google 2021-2023.pdf" \
  "input/Google 2022-2024.pdf"
```

**Task 4.2**: Manual Verification (30 min)
- Check consolidated balance sheet
- Verify "Assets/Deferred income taxes" = 5,261 (2022)
- Verify "Liabilities/Deferred income taxes" = 514 (2022)
- These should be SEPARATE entries now!

**Acceptance Criteria**:
- [ ] Consolidated output shows BOTH deferred tax accounts
- [ ] "Assets/Deferred income taxes" has correct values (5,261, 12,169, 17,180)
- [ ] "Liabilities/Deferred income taxes" has correct values (514, 485)
- [ ] Accounting equation balances (Assets = Liabilities + Equity)
- [ ] No consolidation errors

---

## Why This is Better Than Original Plan

### Original Plan (17 hours):
- ❌ Keep flat schema
- ❌ Add 5 defensive layers
- ❌ Complex confidence scoring
- ❌ Section detection post-extraction
- ❌ Quality gates (6 stages)
- Total: 17 hours of defensive programming

### Revised Plan (8 hours):
- ✅ Fix Pydantic schema (hierarchical)
- ✅ Update extraction prompt
- ✅ Simple path-based consolidation
- ✅ Lightweight validation (accounting equations)
- Total: 8 hours to fix root cause

**Savings**: 9 hours + simpler architecture!

---

## Expected Outcome

### Before Fix

**Extraction**:
```json
{
  "line_items": [
    {"account_name": "Deferred income taxes", "values": ["5,261"], "indent": 1},
    {"account_name": "Deferred income taxes", "values": ["514"], "indent": 1}
  ]
}
```

**Consolidation**:
- Fuzzy matches both "Deferred income taxes"
- Merges them incorrectly
- Shows 514 instead of 5,261

### After Fix

**Extraction**:
```json
{
  "sections": [
    {
      "name": "Assets",
      "line_items": [
        {
          "account_name": "Deferred income taxes",
          "values": ["5,261"],
          "section_path": "Assets/Deferred income taxes"
        }
      ]
    },
    {
      "name": "Liabilities",
      "line_items": [
        {
          "account_name": "Deferred income taxes",
          "values": ["514"],
          "section_path": "Liabilities/Deferred income taxes"
        }
      ]
    }
  ]
}
```

**Consolidation**:
- Matches by path (exact, not fuzzy)
- "Assets/Deferred income taxes" only matches "Assets/Deferred income taxes"
- Both accounts preserved separately
- Shows correct values

---

## Success Metrics

### Phase 1 Complete When:
- [ ] Pydantic schema supports hierarchical sections
- [ ] Extraction prompt asks for section preservation
- [ ] Single PDF extraction produces sections

### Phase 2 Complete When:
- [ ] Consolidation uses path matching
- [ ] Fuzzy matching removed
- [ ] No more confidence scoring needed

### Phase 3 Complete When:
- [ ] Accounting validator checks balance sheet equation
- [ ] Run fails if Assets != Liabilities + Equity

### Phase 4 Complete When:
- [ ] Google PDFs show correct values
- [ ] "Assets/Deferred taxes" = 5,261 (not 514)
- [ ] Both deferred tax accounts preserved
- [ ] Accounting equations balance

---

## Deliverables

### New Files:
- [ ] `app/validation/accounting_validator.py` (1 file)

### Updated Files:
- [ ] `app/extraction/schemas.py` (add sections)
- [ ] `app/extraction/pydantic_extractor.py` (update prompt)
- [ ] `app/consolidation/consolidator.py` (path matching)

### Removed Complexity:
- ❌ No confidence_scorer.py needed
- ❌ No quality_gates.py needed (yet)
- ❌ No section detection post-extraction
- ❌ No fuzzy matching complexity

---

## Risk Assessment

### Low Risk:
- Schema change is additive (add sections, keep line_items for now)
- Can test on single PDF before full pipeline
- Raw text from LLMWhisperer unchanged

### Mitigation:
- Keep old schema as fallback
- Test extraction on all 5 statement types
- Verify with both NVIDIA and Google PDFs

---

## Time Breakdown

| Phase | Task | Hours |
|-------|------|-------|
| 1 | Hierarchical schema | 1 |
| 1 | Update prompt | 1 |
| 1 | Test extraction | 1 |
| 2 | Path-based merger | 2 |
| 2 | Remove fuzzy matching | 1 |
| 3 | Accounting validation | 1 |
| 4 | Re-validate | 1 |
| **Total** | | **8** |

---

## Next Steps After 17.6

**If Successful**:
- ✅ 514 vs 5,261 bug fixed
- ✅ Simpler architecture than defensive approach
- ✅ Production unblocked
- → Move to deployment (Session 18)

**Future Enhancements** (Nice to have):
- Quality gates for confidence levels
- Source traceability metadata
- Advanced tree validation

---

**Key Insight**: We don't need to change LLMWhisperer. We don't need 5 defensive layers. We just need to stop throwing away the hierarchy that LLMWhisperer already gives us.

**The fix is simple: Update Pydantic extraction to preserve what's already there.**

---

**Prepared by**: Claude Sonnet 4.5
**Date**: 2025-12-28
**Status**: Ready to Begin
**Estimated**: 8 hours (down from 17!)
