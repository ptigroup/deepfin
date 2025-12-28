#!/usr/bin/env python3
"""
Hybrid Output Consolidator - Session 17.5

Merges multiple JSON outputs from hybrid pipeline into a single consolidated statement,
preserving brownfield's proven fuzzy matching and consolidation logic.

Usage:
    python scripts/consolidate_hybrid_outputs.py output1.json output2.json [output3.json ...]
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from difflib import SequenceMatcher
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.export.excel_exporter import SchemaBasedExcelExporter
from app.schemas.income_statement_schema import IncomeStatementSchema, IncomeStatementLineItem


class YearNormalizer:
    """Extract and normalize years from reporting periods."""

    @staticmethod
    def extract_year(date_string: str) -> Optional[str]:
        """Extract 4-digit year from any date format."""
        year_match = re.search(r'(\d{4})', date_string)
        return year_match.group(1) if year_match else None

    @staticmethod
    def extract_all_years(data: Dict) -> List[str]:
        """Extract all unique years from financial data."""
        years = set()

        # Try reporting_periods first
        if "reporting_periods" in data:
            for period in data["reporting_periods"]:
                year = YearNormalizer.extract_year(period)
                if year:
                    years.add(year)

        # Extract from line items as fallback
        if not years and "line_items" in data:
            for item in data["line_items"]:
                if "values" in item:
                    for period_key in item["values"]:
                        year = YearNormalizer.extract_year(period_key)
                        if year:
                            years.add(year)

        return sorted(list(years), reverse=True)  # Newest first


class FuzzyAccountMatcher:
    """Fuzzy match account names for intelligent consolidation."""

    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold
        self.merge_tracking = {}

    def find_matching_account(
        self,
        account_name: str,
        parent_section: str,
        existing_accounts: Dict[str, Dict],
        statement_type: str = "income_statement",
        section: Optional[str] = None
    ) -> Optional[str]:
        """Find best matching account using fuzzy matching AND section matching.

        CRITICAL: Both name AND section must match to merge accounts.
        This prevents merging "Deferred income taxes" from Assets with
        "Deferred income taxes" from Liabilities.
        """

        # Check for exact matches first
        for existing_key, existing_account in existing_accounts.items():
            existing_name = existing_account.get("account_name", "")
            existing_parent = existing_account.get("parent_section", "")
            existing_section = existing_account.get("section")

            # Exact match with same parent AND same section
            # Section match required if both have sections
            section_match = (
                section == existing_section or  # Both same section
                section is None or              # Current item has no section (backward compat)
                existing_section is None        # Existing item has no section (backward compat)
            )

            if account_name == existing_name and parent_section == existing_parent and section_match:
                return existing_key

        # Fuzzy matching for income statements
        if statement_type == "income_statement":
            # Define consolidatable patterns
            consolidatable_patterns = {
                'total operating expenses': 'Operating expenses',
                'operating expenses': 'Operating expenses',
                'income tax expense': 'Income tax expense',
                'other income': 'Other income (expense), net',
                'total other income': 'Other income (expense), net'
            }

            name_lower = account_name.lower()

            # Check consolidation patterns
            for pattern, canonical in consolidatable_patterns.items():
                if pattern in name_lower:
                    # Find if canonical name exists
                    for existing_key, existing_account in existing_accounts.items():
                        if canonical.lower() in existing_account.get("account_name", "").lower():
                            return existing_key

                    # If canonical doesn't exist, create key from pattern
                    if pattern in name_lower:
                        # Return the canonical name for new entry
                        return None  # Will be created with canonical name

            # Fuzzy string matching for close names
            best_match = None
            best_ratio = 0.0

            for existing_key, existing_account in existing_accounts.items():
                existing_name = existing_account.get("account_name", "")
                existing_section = existing_account.get("section")

                # Check section compatibility FIRST
                section_match = (
                    section == existing_section or
                    section is None or
                    existing_section is None
                )

                # Only fuzzy match if sections are compatible
                if section_match:
                    ratio = SequenceMatcher(None, account_name.lower(), existing_name.lower()).ratio()

                    if ratio > self.threshold and ratio > best_ratio:
                        best_match = existing_key
                        best_ratio = ratio

            if best_match:
                return best_match

        return None


class HybridOutputConsolidator:
    """Consolidate multiple hybrid pipeline JSON outputs into one."""

    def __init__(self, threshold: float = 0.85):
        self.matcher = FuzzyAccountMatcher(threshold)
        self.consolidation_summary = {"merged_accounts": []}

    def consolidate_json_files(self, json_paths: List[str]) -> Dict:
        """Consolidate multiple JSON files into one."""

        print(f"\n{'='*80}")
        print(f"MULTI-PDF CONSOLIDATION - Session 17.5")
        print(f"{'='*80}\n")

        # Load all JSON files
        all_data = []
        for path in json_paths:
            print(f"Loading: {Path(path).name}")
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_data.append({
                    "path": path,
                    "name": Path(path).stem,
                    "data": data
                })

        print(f"\nLoaded {len(all_data)} files\n")

        # Detect format (hybrid pipeline has metadata wrapper, brownfield doesn't)
        first_raw = all_data[0]["data"]
        if isinstance(first_raw, str):
            # Brownfield format (JSON string needs parsing)
            for item in all_data:
                item["data"] = json.loads(item["data"])
            first_raw = all_data[0]["data"]

        # Extract metadata from first file
        if "data" in first_raw and isinstance(first_raw["data"], dict):
            # Hybrid pipeline format
            first_data = first_raw["data"]
        else:
            # Brownfield format (flat structure)
            first_data = first_raw

        company_name = first_data.get("company_name", "")
        statement_type = first_data.get("statement_type", first_data.get("document_type", "income_statement"))
        currency = first_data.get("currency", "USD")

        # Collect all unique years
        all_years = set()
        for item in all_data:
            # Handle both hybrid and brownfield formats
            data_to_check = item["data"].get("data", item["data"])
            years = YearNormalizer.extract_all_years(data_to_check)
            all_years.update(years)

        all_years = sorted(list(all_years), reverse=True)
        reporting_periods = [f"Year Ended {year}" for year in all_years]

        print(f"Years found: {', '.join(all_years)}")
        print(f"Periods: {len(reporting_periods)}\n")

        # Build consolidated line items
        consolidated_accounts = {}
        account_counter = 0

        for source_item in all_data:
            source_name = source_item["name"]
            # Handle both hybrid and brownfield formats
            data_source = source_item["data"].get("data", source_item["data"])
            line_items = data_source.get("line_items", [])

            print(f"Processing {source_name}: {len(line_items)} items")

            for item in line_items:
                account_name = item.get("account_name", "")
                parent_section = item.get("parent_section", "")
                indent_level = item.get("indent_level", 0)
                values = item.get("values", [])
                section = item.get("section")  # NEW: Get section field

                # Find matching account (checks both name AND section)
                matched_key = self.matcher.find_matching_account(
                    account_name,
                    parent_section,
                    consolidated_accounts,
                    statement_type,
                    section  # NEW: Pass section for matching
                )

                if matched_key:
                    # Merge into existing account
                    existing_account = consolidated_accounts[matched_key]

                    # Add values for new periods
                    if isinstance(values, dict):
                        for period, value in values.items():
                            year = YearNormalizer.extract_year(period)
                            if year:
                                normalized_period = f"Year Ended {year}"
                                existing_account["values"][normalized_period] = value
                    elif isinstance(values, list):
                        # Handle list format [value1, value2]
                        source_data = source_item["data"].get("data", source_item["data"])
                        source_periods = source_data.get("periods", source_data.get("reporting_periods", []))
                        for i, value in enumerate(values):
                            if i < len(source_periods):
                                period = source_periods[i]
                                year = YearNormalizer.extract_year(period)
                                if year:
                                    normalized_period = f"Year Ended {year}"
                                    existing_account["values"][normalized_period] = value

                    # Track merge
                    self._track_merge(existing_account["account_name"], account_name, source_name)

                else:
                    # Create new account
                    account_counter += 1
                    new_key = f"account_{account_counter}"

                    # Initialize values dict
                    values_dict = {}
                    if isinstance(values, dict):
                        for period, value in values.items():
                            year = YearNormalizer.extract_year(period)
                            if year:
                                normalized_period = f"Year Ended {year}"
                                values_dict[normalized_period] = value
                    elif isinstance(values, list):
                        source_data = source_item["data"].get("data", source_item["data"])
                        source_periods = source_data.get("periods", source_data.get("reporting_periods", []))
                        for i, value in enumerate(values):
                            if i < len(source_periods):
                                period = source_periods[i]
                                year = YearNormalizer.extract_year(period)
                                if year:
                                    normalized_period = f"Year Ended {year}"
                                    values_dict[normalized_period] = value

                    consolidated_accounts[new_key] = {
                        "account_name": account_name,
                        "values": values_dict,
                        "indent_level": indent_level,
                        "parent_section": parent_section,
                        "section": section,  # NEW: Preserve section field
                        "account_category": item.get("account_category", ""),
                        "is_calculated": item.get("is_calculated", False)
                    }

                    # Track as new
                    self._track_merge(account_name, account_name, source_name)

        # Build final line items list
        consolidated_line_items = []
        for account in consolidated_accounts.values():
            # Convert values dict to list ordered by reporting_periods
            values_list = [account["values"].get(period, "") for period in reporting_periods]

            consolidated_line_items.append({
                "account_name": account["account_name"],
                "values": values_list,
                "indent_level": account["indent_level"]
            })

        # Determine year range for title
        year_range = f"{all_years[0]}-{all_years[-1]}" if len(all_years) > 1 else all_years[0]

        # Add summary fields to consolidation_summary
        self.consolidation_summary["total_consolidated"] = len(consolidated_line_items)
        self.consolidation_summary["source_pdfs"] = [Path(item["path"]).name for item in all_data]

        # Build consolidated result
        consolidated = {
            "company_name": company_name,
            "document_title": f"Income Statement ({year_range})",
            "document_type": statement_type,
            "reporting_periods": reporting_periods,
            "units_note": "In millions, except per share data",
            "consolidation_summary": self.consolidation_summary,
            "data": {
                "company_name": company_name,
                "statement_type": statement_type,
                "currency": currency,
                "periods": reporting_periods,
                "line_items": consolidated_line_items
            }
        }

        print(f"\nConsolidation complete:")
        print(f"  Total line items: {len(consolidated_line_items)}")
        print(f"  Merged accounts: {len(self.consolidation_summary['merged_accounts'])}")
        print(f"  Time periods: {len(reporting_periods)}")

        return consolidated

    def _track_merge(self, consolidated_name: str, source_name: str, source_file: str):
        """Track which accounts were merged."""
        # Find existing consolidation entry
        for entry in self.consolidation_summary["merged_accounts"]:
            if entry["consolidated_name"] == consolidated_name:
                # Add to existing
                entry["merged_from"].append({
                    "name": source_name,
                    "source": source_file
                })
                return

        # Create new entry
        self.consolidation_summary["merged_accounts"].append({
            "consolidated_name": consolidated_name,
            "merged_from": [{
                "name": source_name,
                "source": source_file
            }]
        })


def create_schema_from_consolidated(consolidated_data: Dict) -> IncomeStatementSchema:
    """Convert consolidated JSON data to IncomeStatementSchema for Excel export."""

    # Extract data section
    data = consolidated_data.get("data", consolidated_data)

    # Create line items
    line_items = []
    for item in data.get("line_items", []):
        # Convert list of values to dict keyed by period
        periods = data.get("periods", [])
        values_dict = {}

        if isinstance(item.get("values"), list):
            # Convert list to dict keyed by period
            for i, value in enumerate(item["values"]):
                if i < len(periods):
                    values_dict[periods[i]] = value
        elif isinstance(item.get("values"), dict):
            values_dict = item["values"]

        line_item = IncomeStatementLineItem(
            account_name=item.get("account_name", ""),
            values=values_dict,
            indent_level=item.get("indent_level", 0)
        )
        line_items.append(line_item)

    # Create schema instance
    schema = IncomeStatementSchema(
        company_name=consolidated_data.get("company_name", ""),
        document_type=consolidated_data.get("document_type", "income_statement"),
        document_title=consolidated_data.get("document_title", "Income Statement"),
        fiscal_year=None,  # Not applicable for multi-year consolidated
        reporting_periods=consolidated_data.get("reporting_periods", data.get("periods", [])),
        line_items=line_items,
        units_note=consolidated_data.get("units_note", "In millions"),
        consolidation_summary=consolidated_data.get("consolidation_summary")
    )

    return schema


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: python scripts/consolidate_hybrid_outputs.py output1.json output2.json [output3.json ...]")
        print("\nExample:")
        print('  python scripts/consolidate_hybrid_outputs.py \\')
        print('    "samples/output/json/NVIDIA 10K 2020-2019.json" \\')
        print('    "samples/output/json/NVIDIA 10K 2022-2021.json"')
        sys.exit(1)

    json_paths = sys.argv[1:]

    # Verify all files exist
    for path in json_paths:
        if not os.path.exists(path):
            print(f"ERROR: File not found: {path}")
            sys.exit(1)

    try:
        # Consolidate
        consolidator = HybridOutputConsolidator()
        result = consolidator.consolidate_json_files(json_paths)

        # Generate output filename
        output_dir = Path("samples/output/consolidated")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Extract years from result
        years = [YearNormalizer.extract_year(p) for p in result["reporting_periods"]]
        years = [y for y in years if y]
        year_range = f"{years[0]}-{years[-1]}" if len(years) > 1 else years[0]

        output_json = output_dir / f"consolidated_income_statement_{year_range}.json"
        output_excel = output_dir / f"consolidated_income_statement_{year_range}.xlsx"

        # Save JSON
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)

        # Save Excel
        try:
            # Create schema instance from consolidated data
            schema = create_schema_from_consolidated(result)

            # Export to Excel
            exporter = SchemaBasedExcelExporter()
            exporter.export_to_excel(schema, str(output_excel))

            print(f"\nOutput saved:")
            print(f"  JSON: {output_json}")
            print(f"  Excel: {output_excel}")
            print(f"\nConsolidation successful!\n")

        except Exception as e:
            print(f"\nJSON saved successfully: {output_json}")
            print(f"WARNING: Excel export failed: {e}")
            print(f"Consolidation completed (JSON only)\n")

    except Exception as e:
        print(f"\nERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
