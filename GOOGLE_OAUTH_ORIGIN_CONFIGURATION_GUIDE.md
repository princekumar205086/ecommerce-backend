# Google OAuth Origin Configuration Guide

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
