#!/usr/bin/env python3

import json

def audit_balance_sheet():
    with open('output/runs/20250927_064431_SUCCESS/03_balance_sheet_06_json_multi_pdf_consolidated_2022-2019.json', 'r') as f:
        data = json.load(f)
    
    print("🔍 BALANCE SHEET AUDIT")
    print("=" * 50)
    
    # Check document title
    title = data.get('document_title', '')
    print(f"✅ Document Title: '{title}'")
    if 'Consolidated' not in title:
        print("   ✅ Title fix verified - no 'Consolidated' prefix")
    else:
        print("   ❌ Title still has 'Consolidated' prefix")
    
    print()
    
    # Check section headers
    print("🔍 Section Headers Check:")
    section_headers_found = []
    
    for account in data.get('accounts', []):
        name = account.get('account_name', '')
        values = account.get('values', {})
        
        # Check for accounts that are actually marked as section headers
        is_header = account.get('is_section_header', False)
        if is_header:
            section_headers_found.append(name)
            has_values = any(v and str(v).strip() and str(v).strip() != '' for v in values.values())
            
            print(f"   Section: '{name}'")
            print(f"   Has values: {has_values}")
            
            if has_values:
                print(f"   ❌ ERROR: Section header has values: {values}")
            else:
                print(f"   ✅ Correct: Section header is empty")
            print()
    
    if not section_headers_found:
        print("   ⚠️  No major section headers found")
    
    # Check for treasury stock consolidation
    print("🔍 Treasury Stock Consolidation:")
    treasury_accounts = []
    
    for account in data.get('accounts', []):
        name = account.get('account_name', '')
        if 'treasury stock' in name.lower():
            treasury_accounts.append(account)
    
    print(f"   Found {len(treasury_accounts)} treasury stock accounts")
    for account in treasury_accounts:
        name = account.get('account_name', '')
        values = account.get('values', {})
        years_with_values = [k for k, v in values.items() if v and str(v).strip()]
        print(f"   '{name}': {len(years_with_values)} years")
    
    if len(treasury_accounts) == 1:
        print("   ✅ Treasury stock properly consolidated into single account")
    else:
        print(f"   ⚠️  Multiple treasury stock accounts: {len(treasury_accounts)}")

if __name__ == "__main__":
    audit_balance_sheet()