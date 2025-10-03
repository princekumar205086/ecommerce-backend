
# Google OAuth Testing Examples for MedixMall

## 1. Basic Login Test
```bash
curl -X POST 'https://backend.okpuja.in/api/accounts/login/google/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "id_token": "YOUR_GOOGLE_ID_TOKEN_HERE",
    "role": "user"
  }'
```

## 2. Supplier Login Test
```bash
curl -X POST 'https://backend.okpuja.in/api/accounts/login/google/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "id_token": "YOUR_GOOGLE_ID_TOKEN_HERE",
    "role": "supplier"
  }'
```

## 3. Local Server Test
```bash
curl -X POST 'http://127.0.0.1:8000/api/accounts/login/google/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "id_token": "YOUR_GOOGLE_ID_TOKEN_HERE",
    "role": "user"
  }'
```

## Expected Responses

### Success Response (200)
```json
{
  "user": {
    "id": 123,
    "email": "user@gmail.com",
    "full_name": "User Name",
    "role": "user",
    "email_verified": true
  },
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "is_new_user": false,
  "message": "Welcome back!"
}
```

### Error Responses

#### Invalid Token (400)
```json
{
  "error": "Invalid Google token",
  "details": "Token verification failed"
}
```

#### Configuration Error (500)
```json
{
  "error": "Google OAuth not configured properly"
}
```

## Client ID Information
- Correct Client ID: 503326319438-eejn7gtbgl0ko2lgdn5cf6lqfpgpnl2p.apps.googleusercontent.com
- Make sure your Google ID token is generated for this client ID
- Add your domain to authorized origins in Google Console
