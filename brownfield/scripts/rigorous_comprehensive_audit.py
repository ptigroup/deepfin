#!/usr/bin/env python3

import json
from collections import Counter

def rigorous_comprehensive_audit():
    run_dir = "output/runs/20250927_071801_SUCCESS"
    
    print("🔍 RIGOROUS COMPREHENSIVE INCOME AUDIT")
    print("=" * 55)
    
    with open(f'{run_dir}/02_comprehensive_income_06_json_multi_pdf_consolidated_2022-2018.json', 'r') as f:
        data = json.load(f)
    
    print(f"Document Title: '{data.get('document_title', '')}'")
    print(f"Reporting Periods: {data.get('reporting_periods', [])}")
    print()
    
    line_items = data.get('line_items', [])
    print(f"Total Line Items: {len(line_items)}")
    
    # Check for duplicates by creating (name, parent) tuples
    print("\n🔍 DUPLICATE DETECTION:")
    print("-" * 22)
    
    name_parent_pairs = []
    for item in line_items:
        name = item.get('account_name', '')
        parent = item.get('parent_section', '')
        name_parent_pairs.append((name, parent))
    
    pair_counts = Counter(name_parent_pairs)
    duplicates = [(pair, count) for pair, count in pair_counts.items() if count > 1]
    
    if duplicates:
        print(f"❌ FOUND {len(duplicates)} DUPLICATE ENTRIES:")
        for (name, parent), count in duplicates:
            print(f"  • '{name}' (parent: '{parent}') appears {count} times")
    else:
        print(f"✅ No duplicates found! All {len(line_items)} entries are unique.")
    
    # Check parent section separation for key accounts
    print(f"\n📊 PARENT SECTION SEPARATION ANALYSIS:")
    print("-" * 35)
    
    # Group by account name
    name_groups = {}
    for item in line_items:
        name = item.get('account_name', '')
        parent = item.get('parent_section', '')
        
        if name not in name_groups:
            name_groups[name] = []
        name_groups[name].append(parent)
    
    # Find accounts with multiple parent sections
    multi_parent_accounts = {}
    for name, parents in name_groups.items():
        unique_parents = list(set(parents))
        if len(unique_parents) > 1:
            multi_parent_accounts[name] = unique_parents
    
    print(f"Accounts appearing under multiple parent sections: {len(multi_parent_accounts)}")
    
    for name, parents in multi_parent_accounts.items():
        print(f"  • '{name}' appears under {len(parents)} different parents:")
        for parent in parents:
            print(f"    - '{parent}'")
    
    # Specific key account verification
    print(f"\n🎯 KEY ACCOUNT VERIFICATION:")
    print("-" * 25)
    
    # Check Net unrealized gain (loss)
    net_unrealized_items = []
    for item in line_items:
        name = item.get('account_name', '')
        if 'net unrealized gain' in name.lower():
            parent = item.get('parent_section', '')
            values = item.get('values', {})
            years_with_data = [k for k, v in values.items() if v and str(v).strip()]
            net_unrealized_items.append((name, parent, len(years_with_data)))
    
    print(f"'Net unrealized gain (loss)' entries: {len(net_unrealized_items)}")
    for name, parent, year_count in net_unrealized_items:
        print(f"  • Parent: '{parent}' ({year_count} years of data)")
    
    expected_parents = {"Available-for-sale debt securities", "Cash flow hedges"}
    found_parents = {parent for _, parent, _ in net_unrealized_items}
    
    if expected_parents.issubset(found_parents):
        print(f"  ✅ Both expected parent sections found")
    else:
        missing = expected_parents - found_parents
        print(f"  ❌ Missing parent sections: {missing}")
    
    # Check reclassification adjustments
    print(f"\n💱 RECLASSIFICATION ADJUSTMENTS:")
    print("-" * 30)
    
    reclas_items = []
    for item in line_items:
        name = item.get('account_name', '')
        if 'reclassification' in name.lower():
            parent = item.get('parent_section', '')
            values = item.get('values', {})
            years_with_data = [k for k, v in values.items() if v and str(v).strip()]
            reclas_items.append((name, parent, len(years_with_data)))
    
    print(f"Reclassification adjustment entries: {len(reclas_items)}")
    for name, parent, year_count in reclas_items:
        print(f"  • '{name}'")
        print(f"    Parent: '{parent}' ({year_count} years)")
    
    # Check that both major OCI sections exist
    print(f"\n🏗️ MAJOR OCI SECTIONS:")
    print("-" * 18)
    
    major_oci_sections = ["Available-for-sale debt securities:", "Cash flow hedges:"]
    
    for section_name in major_oci_sections:
        found = False
        for item in line_items:
            name = item.get('account_name', '')
            if section_name.lower() in name.lower():
                found = True
                values = item.get('values', {})
                has_values = any(v and str(v).strip() for v in values.values())
                print(f"  '{section_name}': {'✅ Found' if found else '❌ Missing'}")
                print(f"    Has values: {has_values} (should be False for section headers)")
                break
        
        if not found:
            print(f"  '{section_name}': ❌ NOT FOUND!")
    
    # Final validation
    has_duplicates = len(duplicates) > 0
    has_separation = len(net_unrealized_items) >= 2
    has_both_sections = len([item for item in line_items if item.get('account_name', '') in major_oci_sections]) >= 2
    
    success = not has_duplicates and has_separation and has_both_sections
    
    return success, {
        'duplicates': len(duplicates),
        'net_unrealized_entries': len(net_unrealized_items),
        'reclassification_entries': len(reclas_items),
        'multi_parent_accounts': len(multi_parent_accounts)
    }

if __name__ == "__main__":
    success, stats = rigorous_comprehensive_audit()
    print(f"\n🎯 COMPREHENSIVE INCOME AUDIT RESULT: {'✅ PASSED' if success else '❌ FAILED'}")
    print(f"📊 Stats: {stats}")