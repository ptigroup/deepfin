#!/usr/bin/env python3
"""
Simple LLMWhisperer API Key Test
Tests if the API key is working with minimal functionality
"""

import os
from dotenv import load_dotenv
from unstract.llmwhisperer import LLMWhispererClient

def test_api_key():
    """Test LLMWhisperer API key with simple calls."""
    print("🔑 LLMWhisperer API Key Test")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv('LLMWHISPERER_API_KEY')
    
    if not api_key:
        print("❌ No API key found in .env file")
        print("   Please set LLMWHISPERER_API_KEY in your .env file")
        return False
    
    print(f"✅ API key loaded: {api_key[:8]}...{api_key[-8:]} (length: {len(api_key)})")
    
    # Initialize client with correct v2 endpoint
    try:
        client = LLMWhispererClient(
            base_url="https://llmwhisperer-api.us-central.unstract.com/api/v2"
        )
        print("✅ Client initialized successfully")
        print(f"   Base URL: {client.base_url}")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False
    
    # Test 1: Check usage info (lightweight call)
    print("\n🔍 Test 1: Checking account usage info...")
    try:
        usage_info = client.get_usage_info()
        print("✅ Usage info retrieved successfully!")
        print(f"   Response: {usage_info}")
        return True
    except Exception as e:
        print(f"❌ Usage info failed: {e}")
        
        # Check error type
        error_str = str(e)
        if "401" in error_str:
            print("   → 401 Error: Invalid or expired API key")
            print("   → Please check your LLMWhisperer account and regenerate the API key")
        elif "403" in error_str:
            print("   → 403 Error: Account access denied (subscription issue)")
        elif "429" in error_str:
            print("   → 429 Error: Rate limit exceeded (try again later)")
        else:
            print(f"   → Unknown error: {error_str}")
    
    # Test 2: Try a simple whisper call with a small test file
    print("\n🔍 Test 2: Testing simple document processing...")
    
    # Create a simple test text file
    test_file = "test_document.txt"
    try:
        with open(test_file, 'w') as f:
            f.write("This is a simple test document.\nLine 2: Testing LLMWhisperer API.\nLine 3: End of test.")
        
        print(f"✅ Created test file: {test_file}")
        
        # Try processing the test file
        result = client.whisper(
            file_path=test_file,
            processing_mode="low_cost"  # Use cheapest mode for testing
        )
        
        print("✅ Document processing successful!")
        print(f"   Result type: {type(result)}")
        print(f"   Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        # Clean up
        os.remove(test_file)
        return True
        
    except Exception as e:
        print(f"❌ Document processing failed: {e}")
        
        # Clean up test file if it exists
        if os.path.exists(test_file):
            os.remove(test_file)
            
        error_str = str(e)
        if "401" in error_str:
            print("   → API key authentication failed")
        elif "404" in error_str:
            print("   → File not found or API endpoint issue")
        elif "429" in error_str:
            print("   → Rate limit exceeded")
        else:
            print(f"   → Error details: {error_str}")
    
    return False

def main():
    """Main test function."""
    print("Starting LLMWhisperer API Key Test...\n")
    
    success = test_api_key()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 API KEY TEST PASSED!")
        print("   Your LLMWhisperer API key is working correctly.")
        print("   You can now use financial_table_extractor.py and structured_extractor.py")
    else:
        print("❌ API KEY TEST FAILED!")
        print("   Possible solutions:")
        print("   1. Check your LLMWhisperer account at https://unstract.com")
        print("   2. Regenerate your API key from the account dashboard")
        print("   3. Verify your account subscription is active")
        print("   4. Make sure you haven't exceeded daily limits (100 calls/day on free plan)")

if __name__ == "__main__":
    main()