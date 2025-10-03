
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
