#!/usr/bin/env python3

import json

def audit_comprehensive_income():
    with open('output/runs/20250927_064431_SUCCESS/02_comprehensive_income_06_json_multi_pdf_consolidated_2022-2018.json', 'r') as f:
        data = json.load(f)
    
    print("🔍 COMPREHENSIVE INCOME AUDIT")
    print("=" * 50)
    
    # Check document title
    title = data.get('document_title', '')
    print(f"✅ Document Title: '{title}'")
    if 'Consolidated' not in title:
        print("   ✅ Title fix verified - no 'Consolidated' prefix")
    else:
        print("   ❌ Title still has 'Consolidated' prefix")
    
    print()
    
    # Check for duplicates - group by account name and parent section
    print("🔍 Duplicate Detection:")
    accounts_map = {}
    duplicates_found = False
    
    for account in data.get('line_items', []):
        name = account.get('account_name', '')
        parent = account.get('parent_section', '')
        key = f"{name}|{parent}"
        
        if key in accounts_map:
            print(f"   ❌ DUPLICATE: '{name}' (parent: '{parent}')")
            duplicates_found = True
        else:
            accounts_map[key] = account
    
    if not duplicates_found:
        print("   ✅ No duplicates found!")
    
    print()
    
    # Check parent section separation
    print("🔍 Parent Section Separation:")
    
    # Look for accounts with same name but different parents
    name_groups = {}
    for account in data.get('line_items', []):
        name = account.get('account_name', '')
        parent = account.get('parent_section', '')
        
        if name not in name_groups:
            name_groups[name] = []
        name_groups[name].append(parent)
    
    for name, parents in name_groups.items():
        unique_parents = list(set(parents))
        if len(unique_parents) > 1:
            print(f"   ✅ '{name}' appears under {len(unique_parents)} different parents:")
            for parent in unique_parents:
                print(f"      - '{parent}' (parent)")
    
    # Check specific important accounts
    print()
    print("🔍 Key Account Verification:")
    
    # Check Net unrealized gain (loss) separation
    net_unrealized_accounts = []
    for account in data.get('line_items', []):
        name = account.get('account_name', '')
        if 'net unrealized gain' in name.lower():
            parent = account.get('parent_section', '')
            net_unrealized_accounts.append((name, parent))
    
    print(f"   'Net unrealized gain (loss)' accounts: {len(net_unrealized_accounts)}")
    for name, parent in net_unrealized_accounts:
        print(f"      - Parent: '{parent}'")
    
    if len(net_unrealized_accounts) >= 2:
        print("   ✅ Properly separated by parent section")
    else:
        print("   ⚠️  May be over-merged")
    
    # Check reclassification adjustments
    reclas_accounts = []
    for account in data.get('line_items', []):
        name = account.get('account_name', '')
        if 'reclassification' in name.lower():
            parent = account.get('parent_section', '')
            reclas_accounts.append((name, parent))
    
    print(f"   Reclassification accounts: {len(reclas_accounts)}")
    for name, parent in reclas_accounts:
        print(f"      - '{name}' (parent: '{parent}')")

if __name__ == "__main__":
    audit_comprehensive_income()