# Next.js 15 Google OAuth Integration Guide

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
