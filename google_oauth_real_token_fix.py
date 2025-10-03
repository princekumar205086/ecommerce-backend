"""
Google OAuth Origin Configuration Fix and Real Token Test
This script helps diagnose and fix the "no registered origin" error
"""

import requests
import json
from datetime import datetime

def analyze_oauth_error():
    """Analyze the OAuth configuration error"""
    print("🔍 GOOGLE OAUTH ERROR ANALYSIS")
    print("="*50)
    
    print("❌ ERROR IDENTIFIED:")
    print("   - 'no registered origin' error")
    print("   - Error 401: invalid_client")
    print("   - FedCM get() rejects with NetworkError")
    
    print("\n🎯 ROOT CAUSE:")
    print("   Your frontend domain is not added to Google OAuth authorized origins")
    
    print("\n📋 SOLUTION STEPS:")
    print("1. Go to Google Cloud Console")
    print("2. Navigate to APIs & Services > Credentials")
    print("3. Click on your OAuth 2.0 Client ID")
    print("4. Add your frontend domain to 'Authorized JavaScript origins'")

def create_origin_configuration_guide():
    """Create detailed configuration guide"""
    guide = """# Google OAuth Origin Configuration Guide

## 🚨 Error Analysis

### Current Error:
- **Error**: `no registered origin`
- **Status**: `401: invalid_client`
- **Cause**: Frontend domain not authorized in Google Console

## 🔧 Fix Steps

### Step 1: Access Google Cloud Console
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** > **Credentials**
3. Find your OAuth 2.0 Client ID: `503326319438-eejn7gtbgl0ko2lgdn5cf6lqfpgpnl2p.apps.googleusercontent.com`

### Step 2: Add Authorized Origins
Add these domains to **Authorized JavaScript origins**:

#### For Development:
```
http://localhost:3000
http://127.0.0.1:3000
http://localhost:3001
http://localhost:8080
```

#### For Production:
```
https://yourdomain.com
https://www.yourdomain.com
https://app.yourdomain.com
```

### Step 3: Add Authorized Redirect URIs (if needed)
Add these to **Authorized redirect URIs**:

#### For Development:
```
http://localhost:3000/auth/callback
http://127.0.0.1:3000/auth/callback
```

#### For Production:
```
https://yourdomain.com/auth/callback
https://www.yourdomain.com/auth/callback
```

## 🧪 Testing Configuration

### Test 1: Basic Origin Check
```javascript
// Add this to your frontend console
console.log('Current origin:', window.location.origin);
```

### Test 2: Google Client Initialization
```javascript
window.google.accounts.id.initialize({
    client_id: '503326319438-eejn7gtbgl0ko2lgdn5cf6lqfpgpnl2p.apps.googleusercontent.com',
    callback: (response) => {
        console.log('Token received:', response.credential);
    }
});
```

## 🔍 Common Issues

| Issue | Solution |
|-------|----------|
| `no registered origin` | Add domain to authorized origins |
| `redirect_uri_mismatch` | Add redirect URI to Google Console |
| `invalid_client` | Check client ID is correct |
| `unauthorized_client` | Enable Google+ API |

## 📝 Complete Next.js 15 Integration

### 1. Install Dependencies
```bash
npm install @google-cloud/local-auth googleapis
```

### 2. Create Google Login Component
```jsx
'use client';
import { useEffect, useState } from 'react';

export default function GoogleLogin() {
    const [isLoaded, setIsLoaded] = useState(false);
    
    useEffect(() => {
        const loadGoogleScript = () => {
            if (window.google) {
                initializeGoogle();
                return;
            }
            
            const script = document.createElement('script');
            script.src = 'https://accounts.google.com/gsi/client';
            script.async = true;
            script.defer = true;
            script.onload = initializeGoogle;
            document.body.appendChild(script);
        };
        
        const initializeGoogle = () => {
            window.google.accounts.id.initialize({
                client_id: '503326319438-eejn7gtbgl0ko2lgdn5cf6lqfpgpnl2p.apps.googleusercontent.com',
                callback: handleCredentialResponse,
                auto_select: false,
                cancel_on_tap_outside: true
            });
            
            window.google.accounts.id.renderButton(
                document.getElementById('google-signin-button'),
                {
                    theme: 'outline',
                    size: 'large',
                    type: 'standard',
                    text: 'signin_with',
                    shape: 'rectangular',
                    logo_alignment: 'left'
                }
            );
            
            setIsLoaded(true);
        };
        
        loadGoogleScript();
    }, []);
    
    const handleCredentialResponse = async (response) => {
        try {
            console.log('ID Token received:', response.credential);
            
            // Test token with backend
            const backendResponse = await fetch('https://backend.okpuja.in/api/accounts/login/google/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    id_token: response.credential,
                    role: 'user'
                })
            });
            
            const data = await backendResponse.json();
            
            if (backendResponse.ok) {
                console.log('✅ Login successful:', data);
                
                // Store tokens
                localStorage.setItem('access_token', data.access);
                localStorage.setItem('refresh_token', data.refresh);
                localStorage.setItem('user', JSON.stringify(data.user));
                
                // Redirect or update app state
                window.location.href = '/dashboard';
            } else {
                console.error('❌ Login failed:', data);
                alert(`Login failed: ${data.error}`);
            }
        } catch (error) {
            console.error('❌ Network error:', error);
            alert('Login failed due to network error');
        }
    };
    
    return (
        <div className="google-login-container">
            <h2>Sign in to MedixMall</h2>
            {isLoaded ? (
                <div id="google-signin-button"></div>
            ) : (
                <div>Loading Google Sign-In...</div>
            )}
        </div>
    );
}
```

### 3. Add to Your Page
```jsx
// app/login/page.js or pages/login.js
import GoogleLogin from '../components/GoogleLogin';

export default function LoginPage() {
    return (
        <div className="login-page">
            <GoogleLogin />
        </div>
    );
}
```

## 🌐 Origin Configuration by Environment

### Development (localhost)
```
http://localhost:3000
http://127.0.0.1:3000
```

### Staging
```
https://staging.yourdomain.com
```

### Production
```
https://yourdomain.com
https://www.yourdomain.com
```

## 🔒 Security Best Practices

1. **Use HTTPS in production**
2. **Add only necessary origins**
3. **Regularly review authorized domains**
4. **Monitor authentication logs**
5. **Implement proper error handling**

---

**Note**: After adding origins to Google Console, changes may take up to 5 minutes to propagate.
"""
    
    with open("GOOGLE_OAUTH_ORIGIN_CONFIGURATION_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(guide)
    
    print("✅ Created GOOGLE_OAUTH_ORIGIN_CONFIGURATION_GUIDE.md")

def create_real_token_tester():
    """Create a real token testing tool"""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real Google OAuth Token Tester</title>
    <script src="https://accounts.google.com/gsi/client" async defer></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 900px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        h1 {
            color: #4285f4;
            text-align: center;
            margin-bottom: 30px;
        }
        .status-card {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        .success { border-left: 4px solid #28a745; background: #d4edda; }
        .error { border-left: 4px solid #dc3545; background: #f8d7da; }
        .warning { border-left: 4px solid #ffc107; background: #fff3cd; }
        .info { border-left: 4px solid #17a2b8; background: #d1ecf1; }
        
        .google-btn {
            margin: 20px 0;
            text-align: center;
        }
        
        .token-display {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            word-break: break-all;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .btn {
            background: #4285f4;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
            font-size: 14px;
        }
        .btn:hover { background: #3367d6; }
        .btn:disabled { background: #ccc; cursor: not-allowed; }
        
        .test-results {
            background: #f8f9fa;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
        }
        
        .step {
            background: #e3f2fd;
            border-radius: 5px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #2196f3;
        }
        
        pre {
            background: #2d3748;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔑 Real Google OAuth Token Tester</h1>
        
        <div class="status-card info">
            <h3>📋 Current Status</h3>
            <p><strong>Origin:</strong> <span id="current-origin"></span></p>
            <p><strong>Client ID:</strong> 503326319438-eejn7gtbgl0ko2lgdn5cf6lqfpgpnl2p.apps.googleusercontent.com</p>
            <p><strong>Backend:</strong> https://backend.okpuja.in/api/accounts/login/google/</p>
        </div>
        
        <div class="step">
            <h3>Step 1: Check Origin Configuration</h3>
            <p>Make sure your current origin is added to Google Console authorized origins.</p>
            <button class="btn" onclick="checkOriginConfig()">Check Configuration</button>
            <div id="origin-check-result"></div>
        </div>
        
        <div class="step">
            <h3>Step 2: Initialize Google Sign-In</h3>
            <div id="g_id_onload"
                 data-client_id="503326319438-eejn7gtbgl0ko2lgdn5cf6lqfpgpnl2p.apps.googleusercontent.com"
                 data-callback="handleCredentialResponse"
                 data-auto_prompt="false">
            </div>
            
            <div class="google-btn">
                <div class="g_id_signin" 
                     data-type="standard"
                     data-size="large"
                     data-theme="outline"
                     data-text="sign_in_with"
                     data-shape="rectangular"
                     data-logo_alignment="left">
                </div>
            </div>
        </div>
        
        <div class="step">
            <h3>Step 3: Token Information</h3>
            <div id="token-info" style="display: none;">
                <h4>🎫 Generated Token:</h4>
                <div class="token-display" id="token-display"></div>
                <button class="btn" onclick="copyToken()">📋 Copy Token</button>
                <button class="btn" onclick="decodeToken()">🔍 Decode Token</button>
                <button class="btn" onclick="testWithBackend()">🧪 Test with Backend</button>
            </div>
        </div>
        
        <div class="step">
            <h3>Step 4: Test Results</h3>
            <div id="test-results"></div>
        </div>
        
        <div class="status-card warning">
            <h3>⚠️ Troubleshooting</h3>
            <ul>
                <li><strong>Error 401:</strong> Add your origin to Google Console</li>
                <li><strong>Network Error:</strong> Check internet connection</li>
                <li><strong>Invalid Client:</strong> Verify client ID configuration</li>
                <li><strong>CORS Error:</strong> Ensure backend allows your origin</li>
            </ul>
        </div>
    </div>

    <script>
        let currentToken = '';
        
        // Display current origin
        document.getElementById('current-origin').textContent = window.location.origin;
        
        function handleCredentialResponse(response) {
            currentToken = response.credential;
            
            document.getElementById('token-display').textContent = currentToken;
            document.getElementById('token-info').style.display = 'block';
            
            showResult('success', 'Token Generated Successfully!', 'You can now test this token with the backend.');
            
            // Auto-decode and test
            decodeToken();
            setTimeout(() => testWithBackend(), 1000);
        }
        
        function checkOriginConfig() {
            const origin = window.location.origin;
            const resultDiv = document.getElementById('origin-check-result');
            
            const allowedOrigins = [
                'http://localhost:3000',
                'http://127.0.0.1:3000',
                'http://localhost:3001',
                'http://localhost:8080',
                'https://yourdomain.com'
            ];
            
            if (allowedOrigins.some(allowed => origin.includes('localhost') || origin.includes('127.0.0.1'))) {
                resultDiv.innerHTML = `
                    <div class="status-card success">
                        <strong>✅ Local Development Detected</strong><br>
                        Add this origin to Google Console: <code>${origin}</code>
                    </div>
                `;
            } else {
                resultDiv.innerHTML = `
                    <div class="status-card warning">
                        <strong>⚠️ Production Domain Detected</strong><br>
                        Make sure <code>${origin}</code> is added to Google Console authorized origins.
                    </div>
                `;
            }
        }
        
        function copyToken() {
            navigator.clipboard.writeText(currentToken).then(() => {
                showResult('success', 'Token Copied!', 'Token has been copied to clipboard.');
            });
        }
        
        function decodeToken() {
            if (!currentToken) {
                showResult('error', 'No Token', 'Please sign in first to generate a token.');
                return;
            }
            
            try {
                const parts = currentToken.split('.');
                const payload = JSON.parse(atob(parts[1]));
                
                const decoded = `
<h4>📊 Decoded Token Information:</h4>
<pre>${JSON.stringify(payload, null, 2)}</pre>
<div class="status-card info">
    <strong>Key Information:</strong><br>
    • Email: ${payload.email}<br>
    • Audience: ${payload.aud}<br>
    • Issuer: ${payload.iss}<br>
    • Expires: ${new Date(payload.exp * 1000).toLocaleString()}<br>
    • Subject: ${payload.sub}
</div>
                `;
                
                document.getElementById('test-results').innerHTML = decoded;
                
            } catch (error) {
                showResult('error', 'Decode Error', `Failed to decode token: ${error.message}`);
            }
        }
        
        async function testWithBackend() {
            if (!currentToken) {
                showResult('error', 'No Token', 'Please sign in first to generate a token.');
                return;
            }
            
            showResult('info', 'Testing...', 'Sending token to backend for verification...');
            
            try {
                const response = await fetch('https://backend.okpuja.in/api/accounts/login/google/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        id_token: currentToken,
                        role: 'user'
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showResult('success', '🎉 Backend Test Successful!', `
                        <strong>User Login Successful!</strong><br>
                        • User ID: ${data.user.id}<br>
                        • Email: ${data.user.email}<br>
                        • Role: ${data.user.role}<br>
                        • New User: ${data.is_new_user}<br>
                        • Message: ${data.message}<br><br>
                        <strong>Tokens Received:</strong><br>
                        • Access Token: ${data.access.substring(0, 50)}...<br>
                        • Refresh Token: ${data.refresh.substring(0, 50)}...
                    `);
                } else {
                    showResult('error', 'Backend Test Failed', `
                        <strong>Status:</strong> ${response.status}<br>
                        <strong>Error:</strong> ${data.error}<br>
                        <strong>Details:</strong> ${data.details || 'No additional details'}
                    `);
                }
                
            } catch (error) {
                showResult('error', 'Network Error', `Failed to connect to backend: ${error.message}`);
            }
        }
        
        function showResult(type, title, message) {
            const resultDiv = document.getElementById('test-results');
            resultDiv.innerHTML = `
                <div class="status-card ${type}">
                    <h4>${title}</h4>
                    <div>${message}</div>
                </div>
            `;
        }
        
        // Auto-check origin on load
        window.onload = () => {
            checkOriginConfig();
        };
    </script>
</body>
</html>"""
    
    with open("REAL_GOOGLE_OAUTH_TOKEN_TESTER.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("✅ Created REAL_GOOGLE_OAUTH_TOKEN_TESTER.html")
    print("   This is a comprehensive testing tool with step-by-step guidance")

def create_nextjs_integration_guide():
    """Create Next.js specific integration guide"""
    guide = """# Next.js 15 Google OAuth Integration Guide

## 🚨 Fixing Current Error

### Error Analysis:
- `FedCM get() rejects with NetworkError`
- `no registered origin`
- `Error 401: invalid_client`

### Root Cause:
Your Next.js application domain is not registered in Google OAuth client configuration.

## 🔧 Step-by-Step Fix

### Step 1: Add Origins to Google Console
1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Find OAuth 2.0 Client ID: `503326319438-eejn7gtbgl0ko2lgdn5cf6lqfpgpnl2p`
3. Add these to **Authorized JavaScript origins**:

#### Development:
```
http://localhost:3000
http://localhost:3001
http://127.0.0.1:3000
```

#### Production:
```
https://yourdomain.com
https://www.yourdomain.com
```

### Step 2: Complete Next.js Component

Create `components/GoogleAuth.jsx`:

```jsx
'use client';
import { useEffect, useState } from 'react';

export default function GoogleAuth() {
    const [isGoogleLoaded, setIsGoogleLoaded] = useState(false);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const initializeGoogleSignIn = () => {
            if (typeof window !== 'undefined' && window.google) {
                window.google.accounts.id.initialize({
                    client_id: '503326319438-eejn7gtbgl0ko2lgdn5cf6lqfpgpnl2p.apps.googleusercontent.com',
                    callback: handleCredentialResponse,
                    auto_select: false,
                    cancel_on_tap_outside: true,
                    use_fedcm_for_prompt: true
                });

                window.google.accounts.id.renderButton(
                    document.getElementById('google-signin-button'),
                    {
                        theme: 'outline',
                        size: 'large',
                        type: 'standard',
                        shape: 'rectangular',
                        text: 'signin_with',
                        logo_alignment: 'left'
                    }
                );

                setIsGoogleLoaded(true);
            }
        };

        const loadGoogleScript = () => {
            if (document.getElementById('google-script')) {
                initializeGoogleSignIn();
                return;
            }

            const script = document.createElement('script');
            script.id = 'google-script';
            script.src = 'https://accounts.google.com/gsi/client';
            script.async = true;
            script.defer = true;
            script.onload = initializeGoogleSignIn;
            document.head.appendChild(script);
        };

        loadGoogleScript();
    }, []);

    const handleCredentialResponse = async (response) => {
        setLoading(true);
        
        try {
            console.log('📩 Received Google credential:', response.credential);
            
            const backendResponse = await fetch('https://backend.okpuja.in/api/accounts/login/google/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    id_token: response.credential,
                    role: 'user'
                })
            });

            const data = await backendResponse.json();

            if (backendResponse.ok) {
                console.log('✅ Authentication successful:', data);
                
                // Store authentication data
                localStorage.setItem('access_token', data.access);
                localStorage.setItem('refresh_token', data.refresh);
                
                setUser(data.user);
                
                // Show success message
                alert(`Welcome ${data.user.full_name || data.user.email}!`);
                
                // Redirect to dashboard or handle success
                window.location.href = '/dashboard';
                
            } else {
                console.error('❌ Authentication failed:', data);
                alert(`Authentication failed: ${data.error}`);
            }
        } catch (error) {
            console.error('❌ Network error:', error);
            alert('Authentication failed due to network error');
        } finally {
            setLoading(false);
        }
    };

    const handleSignOut = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setUser(null);
        
        if (window.google) {
            window.google.accounts.id.disableAutoSelect();
        }
    };

    if (user) {
        return (
            <div className="user-profile">
                <h3>Welcome, {user.full_name || user.email}!</h3>
                <p>Email: {user.email}</p>
                <p>Role: {user.role}</p>
                <button onClick={handleSignOut}>Sign Out</button>
            </div>
        );
    }

    return (
        <div className="google-auth-container">
            <h2>Sign in to MedixMall</h2>
            
            {loading && <div>Authenticating...</div>}
            
            {isGoogleLoaded ? (
                <div id="google-signin-button"></div>
            ) : (
                <div>Loading Google Sign-In...</div>
            )}
            
            <div style={{ marginTop: '20px', fontSize: '12px', color: '#666' }}>
                <p>Current origin: {typeof window !== 'undefined' ? window.location.origin : 'Unknown'}</p>
            </div>
        </div>
    );
}
```

### Step 3: Use in Your Page

```jsx
// app/login/page.js
import GoogleAuth from '../../components/GoogleAuth';

export default function LoginPage() {
    return (
        <div style={{ padding: '50px', textAlign: 'center' }}>
            <h1>MedixMall Login</h1>
            <GoogleAuth />
        </div>
    );
}
```

### Step 4: Add to Layout (Optional)

```jsx
// app/layout.js
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export default function RootLayout({ children }) {
    return (
        <html lang="en">
            <head>
                <meta name="google-signin-client_id" content="503326319438-eejn7gtbgl0ko2lgdn5cf6lqfpgpnl2p.apps.googleusercontent.com" />
            </head>
            <body className={inter.className}>
                {children}
            </body>
        </html>
    )
}
```

## 🧪 Testing Steps

### 1. Local Testing
```bash
npm run dev
# Open http://localhost:3000/login
```

### 2. Check Browser Console
Look for these messages:
- ✅ `📩 Received Google credential: ...`
- ✅ `✅ Authentication successful: ...`

### 3. Network Tab
Check for successful requests to:
- `https://accounts.google.com/gsi/client`
- `https://backend.okpuja.in/api/accounts/login/google/`

## 🔍 Debugging Tips

### Check Current Origin
```javascript
// In browser console
console.log('Current origin:', window.location.origin);
```

### Verify Google Script Load
```javascript
// In browser console
console.log('Google loaded:', typeof window.google !== 'undefined');
```

### Test Token Manually
```javascript
// After sign-in, in console
localStorage.getItem('access_token');
```

## 🚨 Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| `no registered origin` | Domain not in Google Console | Add domain to authorized origins |
| `FedCM NetworkError` | Browser blocking third-party | Try different browser or incognito |
| `invalid_client` | Wrong client ID | Verify client ID matches |
| Script load error | Network/CORS issue | Check internet connection |

## 🔒 Production Deployment

### 1. Environment Variables
```bash
# .env.local
NEXT_PUBLIC_GOOGLE_CLIENT_ID=503326319438-eejn7gtbgl0ko2lgdn5cf6lqfpgpnl2p.apps.googleusercontent.com
NEXT_PUBLIC_API_URL=https://backend.okpuja.in
```

### 2. Update Google Console
Add your production domain to authorized origins:
```
https://yourproductiondomain.com
https://www.yourproductiondomain.com
```

### 3. Security Headers
```javascript
// next.config.js
module.exports = {
    async headers() {
        return [
            {
                source: '/(.*)',
                headers: [
                    {
                        key: 'Content-Security-Policy',
                        value: "script-src 'self' 'unsafe-inline' accounts.google.com;"
                    }
                ]
            }
        ];
    }
};
```

---

**Next.js Version**: 15.3.0  
**Google OAuth Version**: Latest GSI  
**Last Updated**: October 2025
"""
    
    with open("NEXTJS_15_GOOGLE_OAUTH_INTEGRATION.md", "w", encoding="utf-8") as f:
        f.write(guide)
    
    print("✅ Created NEXTJS_15_GOOGLE_OAUTH_INTEGRATION.md")
    print("   Complete Next.js 15 integration guide with error fixes")

def main():
    """Main function"""
    print("🔧 GOOGLE OAUTH REAL TOKEN TEST & ERROR FIX")
    print("="*50)
    
    # Analyze the error
    analyze_oauth_error()
    
    print("\n🛠️ CREATING SOLUTION FILES...")
    
    # Create comprehensive guides and tools
    create_origin_configuration_guide()
    create_real_token_tester()
    create_nextjs_integration_guide()
    
    print("\n✅ SOLUTION PACKAGE CREATED:")
    print("="*40)
    print("📄 Files Created:")
    print("1. GOOGLE_OAUTH_ORIGIN_CONFIGURATION_GUIDE.md - Fix origin errors")
    print("2. REAL_GOOGLE_OAUTH_TOKEN_TESTER.html - Real token testing tool")
    print("3. NEXTJS_15_GOOGLE_OAUTH_INTEGRATION.md - Complete Next.js guide")
    
    print("\n🎯 IMMEDIATE ACTION ITEMS:")
    print("1. ✅ Go to Google Cloud Console")
    print("2. ✅ Add your frontend domain to authorized origins")
    print("3. ✅ Open REAL_GOOGLE_OAUTH_TOKEN_TESTER.html to test")
    print("4. ✅ Use Next.js integration guide for your frontend")
    
    print("\n📋 GOOGLE CONSOLE STEPS:")
    print("1. Visit: https://console.cloud.google.com/apis/credentials")
    print("2. Click on OAuth 2.0 Client ID")
    print("3. Add these origins:")
    print("   - http://localhost:3000 (for development)")
    print("   - https://yourdomain.com (for production)")
    print("4. Save changes and wait 5 minutes")
    
    print("\n🧪 TESTING:")
    print("Open REAL_GOOGLE_OAUTH_TOKEN_TESTER.html after adding origins")
    print("It will guide you through the complete testing process")

if __name__ == "__main__":
    main()