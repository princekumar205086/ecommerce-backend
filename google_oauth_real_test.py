"""
Real Google OAuth Integration Test
This script demonstrates proper Google OAuth integration with the MedixMall backend
"""

import requests
import json
from datetime import datetime

def test_google_oauth_with_correct_client():
    """
    Test Google OAuth with the correct client configuration
    This test demonstrates the proper flow when everything is configured correctly
    """
    print("🧪 GOOGLE OAUTH INTEGRATION TEST")
    print("="*60)
    
    # Endpoint details
    base_url = "https://backend.okpuja.in"
    endpoint = "/api/accounts/login/google/"
    full_url = f"{base_url}{endpoint}"
    
    print(f"📍 Testing endpoint: {full_url}")
    print(f"✅ Expected Client ID: 503326319438-eejn7gtbgl0ko2lgdn5cf6lqfpgpnl2p.apps.googleusercontent.com")
    print()
    
    # Test cases
    test_cases = [
        {
            "name": "Valid User Login",
            "description": "Test with properly generated Google ID token for user role",
            "payload": {
                "id_token": "REPLACE_WITH_REAL_TOKEN_FROM_HTML_GENERATOR",
                "role": "user"
            },
            "expected_status": 200
        },
        {
            "name": "Valid Supplier Login", 
            "description": "Test with properly generated Google ID token for supplier role",
            "payload": {
                "id_token": "REPLACE_WITH_REAL_TOKEN_FROM_HTML_GENERATOR",
                "role": "supplier"
            },
            "expected_status": 200
        },
        {
            "name": "Missing Token",
            "description": "Test with missing id_token",
            "payload": {
                "role": "user"
            },
            "expected_status": 400
        },
        {
            "name": "Invalid Role",
            "description": "Test with invalid role value",
            "payload": {
                "id_token": "dummy_token",
                "role": "invalid_role"
            },
            "expected_status": 400
        },
        {
            "name": "Invalid Token Format",
            "description": "Test with malformed token",
            "payload": {
                "id_token": "invalid.token.format",
                "role": "user"
            },
            "expected_status": 400
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"🧪 Test {i}: {test_case['name']}")
        print(f"   Description: {test_case['description']}")
        
        # Skip tests that need real tokens for demo
        if "REPLACE_WITH_REAL_TOKEN" in str(test_case['payload']):
            print(f"   ⏭️  Skipped - Replace with real token from HTML generator")
            results.append({
                "test": test_case['name'],
                "status": "SKIPPED",
                "reason": "Needs real Google ID token"
            })
            print()
            continue
        
        try:
            # Make the request
            response = requests.post(
                full_url,
                json=test_case['payload'],
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                timeout=10
            )
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            # Check result
            status_match = response.status_code == test_case['expected_status']
            result_status = "PASS" if status_match else "FAIL"
            
            print(f"   📊 Status Code: {response.status_code} (Expected: {test_case['expected_status']})")
            print(f"   🎯 Result: {result_status}")
            
            if response.status_code == 200:
                print(f"   ✅ Response: User login successful")
                if 'user' in response_data:
                    user = response_data['user']
                    print(f"      👤 User: {user.get('email', 'N/A')}")
                    print(f"      🏷️  Role: {user.get('role', 'N/A')}")
                    print(f"      🆔 ID: {user.get('id', 'N/A')}")
            elif response.status_code in [400, 500]:
                error_msg = response_data.get('error', 'Unknown error')
                print(f"   ❌ Error: {error_msg}")
            
            results.append({
                "test": test_case['name'],
                "status": result_status,
                "status_code": response.status_code,
                "response": response_data
            })
            
        except requests.exceptions.RequestException as e:
            print(f"   🔌 Network Error: {str(e)}")
            results.append({
                "test": test_case['name'],
                "status": "ERROR",
                "error": str(e)
            })
        
        print()
    
    # Summary
    print("📋 TEST SUMMARY")
    print("="*40)
    
    passed = len([r for r in results if r['status'] == 'PASS'])
    failed = len([r for r in results if r['status'] == 'FAIL'])
    errors = len([r for r in results if r['status'] == 'ERROR'])
    skipped = len([r for r in results if r['status'] == 'SKIPPED'])
    total = len(results)
    
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"🔌 Errors: {errors}")
    print(f"⏭️  Skipped: {skipped}")
    
    if total > 0:
        success_rate = (passed / (total - skipped)) * 100 if (total - skipped) > 0 else 0
        print(f"📊 Success Rate: {success_rate:.1f}%")
    
    # Save results
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "endpoint": full_url,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped
        },
        "results": results
    }
    
    with open("google_oauth_integration_test_results.json", "w") as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n💾 Results saved to: google_oauth_integration_test_results.json")
    
    return results

def create_test_instructions():
    """Create step-by-step testing instructions"""
    instructions = """
# 🧪 Google OAuth Testing Instructions

## Prerequisites

1. **Google OAuth Client Setup**
   - Client ID: `503326319438-eejn7gtbgl0ko2lgdn5cf6lqfpgpnl2p.apps.googleusercontent.com`
   - Make sure your domain is added to authorized origins in Google Console

2. **Required Files**
   - `google_oauth_token_generator.html` (for generating test tokens)
   - This test script

## Step-by-Step Testing Process

### Step 1: Generate a Valid Google ID Token

1. Open `google_oauth_token_generator.html` in a web browser
2. Make sure you're on HTTPS or localhost
3. Click "Sign in with Google"
4. Complete the Google authentication
5. Copy the generated token

### Step 2: Update Test Script

1. Open this Python script
2. Replace `REPLACE_WITH_REAL_TOKEN_FROM_HTML_GENERATOR` with your actual token
3. Save the file

### Step 3: Run the Tests

```bash
python google_oauth_real_test.py
```

### Step 4: Verify Results

1. Check the console output for test results
2. Review `google_oauth_integration_test_results.json` for detailed results
3. Verify that valid tokens return 200 status with user data

## Expected Results

### ✅ Successful Authentication (200)
```json
{
  "user": {
    "id": 123,
    "email": "test@gmail.com",
    "full_name": "Test User",
    "role": "user",
    "email_verified": true
  },
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "is_new_user": false,
  "message": "Welcome back!"
}
```

### ❌ Token Validation Error (400)
```json
{
  "error": "Invalid Google token",
  "details": "Token verification failed"
}
```

### ⚙️ Configuration Error (500)
```json
{
  "error": "Google OAuth not configured properly"
}
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "redirect_uri_mismatch" | Add your domain to Google Console authorized origins |
| "Token has wrong audience" | Ensure token is generated with correct client ID |
| "Google OAuth not configured properly" | Check server environment variables |
| Network timeout | Check server status and network connectivity |

## Integration with Frontend

After successful testing, integrate the endpoint with your frontend:

1. **HTML/JavaScript**: Use provided examples in documentation
2. **React**: Implement with Google Sign-In library
3. **Vue.js**: Use Vue-specific Google authentication
4. **Angular**: Integrate with Angular Google Sign-In

## API Endpoint Details

- **URL**: `https://backend.okpuja.in/api/accounts/login/google/`
- **Method**: POST
- **Content-Type**: application/json
- **Required**: `id_token` (Google ID token)
- **Optional**: `role` ("user" or "supplier", defaults to "user")

## Security Notes

1. Never log or store Google ID tokens
2. Always validate tokens on the server side
3. Use HTTPS in production
4. Implement proper error handling
5. Monitor authentication attempts
"""
    
    with open("GOOGLE_OAUTH_TESTING_INSTRUCTIONS.md", "w", encoding="utf-8") as f:
        f.write(instructions)
    
    print("📖 Created testing instructions: GOOGLE_OAUTH_TESTING_INSTRUCTIONS.md")

def main():
    """Main function to run tests and create instructions"""
    print("🚀 GOOGLE OAUTH REAL INTEGRATION TEST")
    print("="*50)
    
    # Create testing instructions
    create_test_instructions()
    
    # Run the actual tests
    test_results = test_google_oauth_with_correct_client()
    
    print("\n🎯 NEXT STEPS:")
    print("1. Use the HTML token generator to get a real Google ID token")
    print("2. Replace the placeholder tokens in test cases")
    print("3. Re-run this script to test with real tokens")
    print("4. Use the documentation to integrate with your frontend")
    
    print("\n📄 Generated Files:")
    print("- google_oauth_integration_test_results.json (Test results)")
    print("- GOOGLE_OAUTH_TESTING_INSTRUCTIONS.md (Testing guide)")
    print("- GOOGLE_OAUTH_COMPLETE_DOCUMENTATION.md (Full documentation)")
    print("- google_oauth_token_generator.html (Token generator)")

if __name__ == "__main__":
    main()