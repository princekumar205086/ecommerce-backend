
import base64
import json
import requests
from datetime import datetime, timezone

def validate_google_token(id_token):
    '''Validate a Google ID token without server-side verification'''
    try:
        # Decode the payload (this doesn't verify the signature)
        parts = id_token.split('.')
        if len(parts) != 3:
            return False, "Invalid token format"
        
        # Decode payload
        payload = parts[1]
        padding = len(payload) % 4
        if padding:
            payload += '=' * (4 - padding)
        
        decoded_bytes = base64.urlsafe_b64decode(payload)
        payload_data = json.loads(decoded_bytes.decode('utf-8'))
        
        # Check basic fields
        required_fields = ['iss', 'aud', 'sub', 'email', 'exp', 'iat']
        for field in required_fields:
            if field not in payload_data:
                return False, f"Missing required field: {field}"
        
        # Check issuer
        if payload_data['iss'] != 'accounts.google.com':
            return False, f"Invalid issuer: {payload_data['iss']}"
        
        # Check audience (should match our client ID)
        expected_audience = "503326319438-eejn7gtbgl0ko2lgdn5cf6lqfpgpnl2p.apps.googleusercontent.com"
        if payload_data['aud'] != expected_audience:
            return False, f"Wrong audience: {payload_data['aud']}, expected: {expected_audience}"
        
        # Check expiration
        exp_time = payload_data['exp']
        current_time = datetime.now(timezone.utc).timestamp()
        if current_time > exp_time:
            return False, "Token is expired"
        
        return True, payload_data
        
    except Exception as e:
        return False, str(e)

def test_token_with_backend(id_token, role="user"):
    '''Test token with actual backend'''
    url = "https://backend.okpuja.in/api/accounts/login/google/"
    
    data = {
        "id_token": id_token,
        "role": role
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        return response.status_code, response.json()
    except Exception as e:
        return 0, {"error": str(e)}

if __name__ == "__main__":
    print("Google OAuth Token Validator")
    print("="*40)
    
    # You can paste a real token here for testing
    test_token = input("Enter Google ID token (or press Enter to skip): ").strip()
    
    if test_token:
        print("\n🔍 Validating token structure...")
        is_valid, result = validate_google_token(test_token)
        
        if is_valid:
            print("✅ Token structure is valid")
            print(f"   Email: {result['email']}")
            print(f"   Audience: {result['aud']}")
            print(f"   Expires: {datetime.fromtimestamp(result['exp'])}")
            
            print("\n🧪 Testing with backend...")
            status_code, response = test_token_with_backend(test_token)
            
            if status_code == 200:
                print("✅ Backend authentication successful!")
                print(f"   User: {response.get('user', {}).get('email', 'N/A')}")
            else:
                print(f"❌ Backend authentication failed (Status: {status_code})")
                print(f"   Error: {response.get('error', 'Unknown error')}")
        else:
            print(f"❌ Token validation failed: {result}")
    else:
        print("No token provided. Use the HTML generator to create a test token.")
