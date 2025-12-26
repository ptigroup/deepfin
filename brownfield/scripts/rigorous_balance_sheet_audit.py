#!/usr/bin/env python3

import json

def rigorous_balance_sheet_audit():
    run_dir = "output/runs/20250927_071801_SUCCESS"
    
    print("🔍 RIGOROUS BALANCE SHEET AUDIT")
    print("=" * 50)
    
    with open(f'{run_dir}/03_balance_sheet_06_json_multi_pdf_consolidated_2022-2019.json', 'r') as f:
        data = json.load(f)
    
    print(f"Document Title: '{data.get('document_title', '')}'")
    print(f"Reporting Periods: {data.get('reporting_periods', [])}")
    print()
    
    accounts = data.get('accounts', [])
    print(f"Total Accounts: {len(accounts)}")
    
    # Check ALL section headers and their values
    print("\n📋 ALL SECTION HEADERS:")
    print("-" * 25)
    
    section_headers = []
    problematic_headers = []
    
    for i, account in enumerate(accounts):
        name = account.get('account_name', '')
        is_header = account.get('is_section_header', False)
        values = account.get('values', {})
        has_values = any(v and str(v).strip() for v in values.values())
        
        if is_header:
            section_headers.append(account)
            print(f"{i+1:2d}. '{name}' (header: {is_header})")
            
            if has_values:
                problematic_headers.append(account)
                print(f"    ❌ HAS VALUES: {dict(list(values.items())[:2])}")
            else:
                print(f"    ✅ Empty (correct)")
    
    print(f"\n📊 SECTION HEADER SUMMARY:")
    print(f"Total section headers: {len(section_headers)}")
    print(f"Headers with values (problems): {len(problematic_headers)}")
    
    if problematic_headers:
        print(f"\n❌ PROBLEMATIC HEADERS:")
        for account in problematic_headers:
            name = account.get('account_name', '')
            values = account.get('values', {})
            print(f"  • '{name}'")
            for period, value in values.items():
                if value and str(value).strip():
                    print(f"    {period}: {value}")
    
    # Check treasury stock consolidation
    print(f"\n💰 TREASURY STOCK CHECK:")
    print("-" * 20)
    
    treasury_accounts = []
    for account in accounts:
        name = account.get('account_name', '')
        if 'treasury stock' in name.lower():
            treasury_accounts.append(account)
    
    print(f"Treasury stock accounts found: {len(treasury_accounts)}")
    for account in treasury_accounts:
        name = account.get('account_name', '')
        values = account.get('values', {})
        years_with_values = [k for k, v in values.items() if v and str(v).strip()]
        print(f"  • '{name}'")
        print(f"    Years with data: {len(years_with_values)}")
        print(f"    Sample values: {dict(list(values.items())[:2])}")
    
    # Check for major section headers that should be empty
    print(f"\n🏗️ MAJOR SECTION VERIFICATION:")
    print("-" * 25)
    
    major_sections = [
        "ASSETS",
        "LIABILITIES AND SHAREHOLDERS' EQUITY", 
        "Shareholders' equity:"
    ]
    
    for section_name in major_sections:
        found = False
        for account in accounts:
            name = account.get('account_name', '')
            if section_name.lower() in name.lower():
                found = True
                is_header = account.get('is_section_header', False)
                values = account.get('values', {})
                has_values = any(v and str(v).strip() for v in values.values())
                
                print(f"  '{name}':")
                print(f"    Marked as header: {is_header}")
                print(f"    Has values: {has_values}")
                
                if is_header and not has_values:
                    print(f"    ✅ Correct")
                elif is_header and has_values:
                    print(f"    ❌ Header with values!")
                elif not is_header and has_values:
                    print(f"    ⚠️  Data account (not header)")
                else:
                    print(f"    ⚠️  Empty data account")
                break
        
        if not found:
            print(f"  '{section_name}': ❌ NOT FOUND!")
    
    return len(problematic_headers) == 0

if __name__ == "__main__":
    success = rigorous_balance_sheet_audit()
    print(f"\n🎯 BALANCE SHEET AUDIT RESULT: {'✅ PASSED' if success else '❌ FAILED'}")