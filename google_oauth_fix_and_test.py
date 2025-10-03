"""
Google OAuth Client ID Fix and Token Generator
This script helps generate proper Google OAuth tokens for testing
"""

import os
import requests
import json
from datetime import datetime

class GoogleOAuthFixer:
    def __init__(self):
        self.correct_client_id = "503326319438-eejn7gtbgl0ko2lgdn5cf6lqfpgpnl2p.apps.googleusercontent.com"
        self.wrong_client_id = "618104708054-9r9s1c4alg36erliucho9t52n32n6dgq.apps.googleusercontent.com"
        
    def analyze_problem(self):
        """Analyze the OAuth configuration problem"""
        print("🔍 GOOGLE OAUTH CONFIGURATION ANALYSIS")
        print("="*60)
        print(f"✅ Correct Client ID (in .env): {self.correct_client_id}")
        print(f"❌ Wrong Client ID (in token):   {self.wrong_client_id}")
        print("\n📋 PROBLEM IDENTIFIED:")
        print("- The Google ID token was generated for a different OAuth client")
        print("- This causes 'audience mismatch' error during verification")
        print("- Production server returns generic 'Google OAuth not configured properly'")
        print("- Local server shows the actual error with details")
        
    def create_test_html(self):
        """Create HTML test file for generating correct tokens"""
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google OAuth Token Generator for MedixMall</title>
    <script src="https://accounts.google.com/gsi/client" async defer></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .client-info {{
            background: #e3f2fd;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .token-area {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            border: 1px solid #dee2e6;
        }}
        #token-display {{
            width: 100%;
            min-height: 150px;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-family: monospace;
            font-size: 12px;
            background: #fff;
        }}
        .btn {{
            background: #4285f4;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin: 10px 5px;
        }}
        .btn:hover {{
            background: #3367d6;
        }}
        .warning {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .success {{
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔑 Google OAuth Token Generator</h1>
        <p>This tool generates Google ID tokens for testing the MedixMall OAuth implementation.</p>
        
        <div class="client-info">
            <h3>📋 OAuth Client Configuration</h3>
            <p><strong>Client ID:</strong> {self.correct_client_id}</p>
            <p><strong>Purpose:</strong> Generate tokens for MedixMall backend testing</p>
        </div>
        
        <div class="warning">
            <h4>⚠️ Important Setup Instructions:</h4>
            <ol>
                <li>Make sure this HTML file is served over HTTPS or from localhost</li>
                <li>Add the serving domain to your Google OAuth client's authorized origins</li>
                <li>For localhost testing, add: <code>http://localhost:3000</code> and <code>http://127.0.0.1:3000</code></li>
                <li>For production testing, add your domain to authorized origins</li>
            </ol>
        </div>
        
        <div id="g_id_onload"
             data-client_id="{self.correct_client_id}"
             data-callback="handleCredentialResponse"
             data-auto_prompt="false">
        </div>
        
        <div class="g_id_signin" 
             data-type="standard"
             data-size="large"
             data-theme="outline"
             data-text="sign_in_with"
             data-shape="rectangular"
             data-logo_alignment="left">
        </div>
        
        <div class="token-area">
            <h3>🎫 Generated Token</h3>
            <textarea id="token-display" placeholder="Click 'Sign in with Google' above to generate a token..."></textarea>
            <br>
            <button class="btn" onclick="copyToken()">📋 Copy Token</button>
            <button class="btn" onclick="testToken()">🧪 Test Token</button>
            <button class="btn" onclick="decodeToken()">🔍 Decode Token</button>
        </div>
        
        <div id="token-info" style="display: none;">
            <h3>📊 Token Information</h3>
            <pre id="decoded-info"></pre>
        </div>
        
        <div id="test-results" style="display: none;">
            <h3>🧪 Test Results</h3>
            <pre id="test-output"></pre>
        </div>
    </div>

    <script>
        let currentToken = '';
        
        function handleCredentialResponse(response) {{
            currentToken = response.credential;
            document.getElementById('token-display').value = currentToken;
            
            const successDiv = document.createElement('div');
            successDiv.className = 'success';
            successDiv.innerHTML = '<h4>✅ Token Generated Successfully!</h4><p>You can now copy this token and test it with the MedixMall API.</p>';
            
            const container = document.querySelector('.container');
            const existingSuccess = container.querySelector('.success');
            if (existingSuccess) {{
                existingSuccess.remove();
            }}
            container.appendChild(successDiv);
            
            // Auto-decode the token
            decodeToken();
        }}
        
        function copyToken() {{
            const tokenDisplay = document.getElementById('token-display');
            tokenDisplay.select();
            tokenDisplay.setSelectionRange(0, 99999);
            document.execCommand('copy');
            alert('Token copied to clipboard!');
        }}
        
        function decodeToken() {{
            if (!currentToken) {{
                alert('No token to decode. Please sign in first.');
                return;
            }}
            
            try {{
                const parts = currentToken.split('.');
                const payload = JSON.parse(atob(parts[1]));
                
                document.getElementById('decoded-info').textContent = JSON.stringify(payload, null, 2);
                document.getElementById('token-info').style.display = 'block';
                
                // Check expiration
                const now = Math.floor(Date.now() / 1000);
                const exp = payload.exp;
                const timeLeft = exp - now;
                
                if (timeLeft > 0) {{
                    console.log(`Token expires in ${{timeLeft}} seconds`);
                }} else {{
                    console.log('Token is expired!');
                }}
                
            }} catch (error) {{
                alert('Error decoding token: ' + error.message);
            }}
        }}
        
        function testToken() {{
            if (!currentToken) {{
                alert('No token to test. Please sign in first.');
                return;
            }}
            
            const testData = {{
                id_token: currentToken,
                role: 'user'
            }};
            
            // Test both local and production
            Promise.all([
                testEndpoint('http://127.0.0.1:8000/api/accounts/login/google/', testData, 'Local'),
                testEndpoint('https://backend.okpuja.in/api/accounts/login/google/', testData, 'Production')
            ]).then(results => {{
                const output = results.join('\\n\\n');
                document.getElementById('test-output').textContent = output;
                document.getElementById('test-results').style.display = 'block';
            }});
        }}
        
        async function testEndpoint(url, data, label) {{
            try {{
                const response = await fetch(url, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify(data)
                }});
                
                const result = await response.json();
                return `${{label}} Server (${{url}}):
Status: ${{response.status}}
Response: ${{JSON.stringify(result, null, 2)}}`;
                
            }} catch (error) {{
                return `${{label}} Server (${{url}}):
Error: ${{error.message}}`;
            }}
        }}
    </script>
</body>
</html>"""
        
        with open("google_oauth_token_generator.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print("✅ Created google_oauth_token_generator.html")
        print("📝 To use this file:")
        print("1. Open it in a web browser (preferably Chrome)")
        print("2. Make sure you're serving it over HTTPS or localhost")
        print("3. Click 'Sign in with Google' to generate a token")
        print("4. Copy the token and test it with the API")
        
    def create_curl_examples(self):
        """Create curl examples for testing"""
        examples = f"""
# Google OAuth Testing Examples for MedixMall

## 1. Basic Login Test
```bash
curl -X POST 'https://backend.okpuja.in/api/accounts/login/google/' \\
  -H 'accept: application/json' \\
  -H 'Content-Type: application/json' \\
  -d '{{
    "id_token": "YOUR_GOOGLE_ID_TOKEN_HERE",
    "role": "user"
  }}'
```

## 2. Supplier Login Test
```bash
curl -X POST 'https://backend.okpuja.in/api/accounts/login/google/' \\
  -H 'accept: application/json' \\
  -H 'Content-Type: application/json' \\
  -d '{{
    "id_token": "YOUR_GOOGLE_ID_TOKEN_HERE",
    "role": "supplier"
  }}'
```

## 3. Local Server Test
```bash
curl -X POST 'http://127.0.0.1:8000/api/accounts/login/google/' \\
  -H 'accept: application/json' \\
  -H 'Content-Type: application/json' \\
  -d '{{
    "id_token": "YOUR_GOOGLE_ID_TOKEN_HERE",
    "role": "user"
  }}'
```

## Expected Responses

### Success Response (200)
```json
{{
  "user": {{
    "id": 123,
    "email": "user@gmail.com",
    "full_name": "User Name",
    "role": "user",
    "email_verified": true
  }},
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "is_new_user": false,
  "message": "Welcome back!"
}}
```

### Error Responses

#### Invalid Token (400)
```json
{{
  "error": "Invalid Google token",
  "details": "Token verification failed"
}}
```

#### Configuration Error (500)
```json
{{
  "error": "Google OAuth not configured properly"
}}
```

## Client ID Information
- Correct Client ID: {self.correct_client_id}
- Make sure your Google ID token is generated for this client ID
- Add your domain to authorized origins in Google Console
"""
        
        with open("google_oauth_curl_examples.md", "w", encoding="utf-8") as f:
            f.write(examples)
        
        print("✅ Created google_oauth_curl_examples.md")

def main():
    fixer = GoogleOAuthFixer()
    
    print("🔧 GOOGLE OAUTH CONFIGURATION FIXER")
    print("="*50)
    
    fixer.analyze_problem()
    
    print("\n🛠️ GENERATING SOLUTION FILES...")
    fixer.create_test_html()
    fixer.create_curl_examples()
    
    print("\n✅ SOLUTION SUMMARY:")
    print("1. The token you provided was for the wrong OAuth client")
    print("2. Use the HTML file to generate a correct token")
    print("3. Test with the curl examples provided")
    print("4. Make sure your domain is in Google Console authorized origins")
    
    print("\n📋 NEXT STEPS:")
    print("1. Open google_oauth_token_generator.html in a browser")
    print("2. Sign in with Google to get a new token")
    print("3. Test the new token with the API")
    print("4. Update your frontend to use the correct client ID")

if __name__ == "__main__":
    main()