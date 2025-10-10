# Profile Update API (PATCH) - `/api/accounts/me/`

This document describes the new PATCH endpoint on `/api/accounts/me/` to partially update a user's profile. It includes payload shapes, validation rules, examples (PowerShell, fetch, axios), file upload notes for `profile_pic`, and expected responses.

---

## Overview

- Endpoint: `PATCH /api/accounts/me/`
- Authentication: Required (JWT access token in `Authorization: Bearer <token>` header)
- Purpose: Partially update the authenticated user's profile fields such as `full_name`, `contact`, and `profile_pic`.
- Parsers supported: `application/json` and `multipart/form-data` (image upload)

---

## Allowed fields

- `full_name` (string) — optional
- `contact` (string) — optional
  - Must be exactly 10 digits
  - Must start with 6, 7, 8, or 9
  - Must NOT include a country code (e.g., no leading `+91` or `91`)
  - Uniqueness: contact must be unique across users. Attempting to set a contact already used by another user will return a validation error.
- `profile_pic` (file/image) — optional
  - Nullable: you can upload a new picture or send `null` to keep/remove (behavior depends on frontend usage).
  - Maximum allowed size: 200 KB (server-side enforced). Frontend should also validate before upload for better UX.

---

## Validation Rules (Server-side)

1. Contact format:
   - Normalized to digits (non-digit characters removed). After normalization, the number must be exactly 10 digits.
   - Must start with one of: `6`, `7`, `8`, `9`.
2. Contact uniqueness:
   - When updating, the server checks other users' `contact` fields and rejects duplicates.
3. Profile picture size:
   - Must be <= 200 KB. Otherwise 400 with a message.

---

## Success Response

- Status: `200 OK`
- Body: updated `User` resource (same as `UserSerializer`)

Example:

```json
{
  "id": 16,
  "email": "user@example.com",
  "full_name": "Test User Updated",
  "contact": "9123456789",
  "role": "user",
  "has_address": true,
  "medixmall_mode": false,
  "email_verified": true,
  "profile_pic": null
}
```

---

## Error Responses (examples)

- Invalid contact format (400 Bad Request):

```json
{
  "contact": ["Contact number must be exactly 10 digits (no country code)."]
}
```

- Invalid starting digit (400 Bad Request):

```json
{
  "contact": ["Contact number must start with 6,7,8 or 9."]
}
```

- Duplicate contact (400 Bad Request):

```json
{
  "contact": ["This contact number is already in use."]
}
```

- Profile picture too large (400 Bad Request):

```json
{
  "profile_pic": ["Profile picture must be <= 200 KB"]
}
```

- Unauthorized (401):

```json
{ "detail": "Authentication credentials were not provided." }
```

---

## Examples

### PowerShell (JSON body — change contact)

```powershell
$token = "<access_token>"
$body = '{"contact":"9123456789"}'
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/accounts/me/" -Method PATCH -ContentType "application/json" -Headers @{Authorization = "Bearer $token"} -Body $body | ConvertTo-Json -Depth 5
```

### PowerShell (multipart/form-data — upload profile_pic)

```powershell
$token = "<access_token>"
$file = Get-Item "C:\path\to\avatar.jpg"
$form = @{
  full_name = 'New Name'
  profile_pic = $file
}
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/accounts/me/" -Method PATCH -Headers @{Authorization = "Bearer $token"} -Form $form
```

Note: PowerShell's `Invoke-RestMethod` will set the correct multipart headers automatically when `-Form` is used.

### Fetch (JSON)

```javascript
const token = localStorage.getItem('access_token');
await fetch('http://127.0.0.1:8000/api/accounts/me/', {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({ contact: '9123456789' })
});
```

### Fetch (multipart upload image)

```javascript
const token = localStorage.getItem('access_token');
const form = new FormData();
form.append('profile_pic', fileInput.files[0]);
form.append('full_name', 'Updated Name');

await fetch('http://127.0.0.1:8000/api/accounts/me/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: form
});
```

### Axios (JSON)

```javascript
import axios from 'axios';
const token = localStorage.getItem('access_token');
await axios.patch('http://127.0.0.1:8000/api/accounts/me/', { contact: '9123456789' }, {
  headers: { Authorization: `Bearer ${token}` }
});
```

### Axios (multipart upload)

```javascript
const form = new FormData();
form.append('profile_pic', fileInput.files[0]);
form.append('full_name', 'Updated Name');

await axios.patch('http://127.0.0.1:8000/api/accounts/me/', form, {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'multipart/form-data'
  }
});
```

---

## Frontend Recommendations

1. Validate contact on the client side before sending:
   - Ensure digits only, length 10, starts with 6/7/8/9.
   - Show immediate error messages for incorrect format.
2. Validate image size client-side before upload (<= 200KB) to avoid failed uploads.
3. Use `PATCH` for partial updates — do not include unchanged fields unless needed.
4. When updating contact, show a confirmation flow if the change affects login/OTP flows.

---

## Notes for Backend/Devops

- The server-side enforces all validation; keep docs and tests synchronized.
- Migrations: `accounts` now has `profile_pic` field; remember to run `makemigrations`/`migrate` in staging/production.

---


## Address response shape (important for frontend)

- Endpoint: `GET /api/accounts/address/` (authenticated)
- For frontend stability we return a single nested object named `address` instead of multiple top-level address fields that may be null. This avoids the client receiving top-level nulls which can be misinterpreted as intentionally empty fields.

Behavior:
- When the user has no saved address, the server returns `address: {}` (an empty object).
- When the user has an address, the server returns `address` populated with the usual keys (for example: `address_line_1`, `address_line_2`, `city`, `state`, `pincode`, `country`, `has_address: true`).

Example (no address):

```json
{
  "address": {}
}
```

Example (with address):

```json
{
  "address": {
    "address_line_1": "12 Baker Street",
    "address_line_2": "Near Central Park",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400001",
    "country": "India",
    "has_address": true
  }
}
```

This shape is backward-compatible for most clients (they can still read individual address fields inside `address`) and safer for form-driven frontends.

---

## PowerShell — full flow example (login -> patch profile -> get address)

This script demonstrates logging in with the test credentials, patching the profile (contact update), and then retrieving the address object. It uses the same server base URL used in earlier examples.

```powershell
```powershell
# login and get token
$loginBody = '{"email":"user@example.com","password":"User@123"}'
$loginRes = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/accounts/login/" -Method POST -ContentType "application/json" -Body $loginBody
$token = $loginRes.access
Write-Host "Access token acquired"

# PATCH the profile to update contact
$patchBody = '{"contact":"9123456789"}'
$patchRes = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/accounts/me/" -Method PATCH -ContentType "application/json" -Headers @{ Authorization = "Bearer $token" } -Body $patchBody
Write-Host "Profile updated: " ($patchRes | ConvertTo-Json -Depth 5)

# GET address
$getAddr = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/accounts/address/" -Method GET -Headers @{ Authorization = "Bearer $token" }
Write-Host "Address response: " ($getAddr | ConvertTo-Json -Depth 5)
```

Last updated: October 10, 2025

---

## Next.js / frontend image notes

If your frontend uses Next.js Image Optimization (`next/image`) you'll need to ensure the image source provided by the API is usable by Next.js.

1. The API now returns an absolute URL for `profile_pic` (for example: `http://127.0.0.1:8000/media/profile_pics/gk.jpg`) when a request is made with the HTTP request included in the serializer context. Use this URL directly as the `src` for an `<img>` or `next/image`.

2. For Next.js to optimize external images, add the API host to `next.config.js` `images.domains` or `images.remotePatterns`. Example (next.config.js):

```js
// next.config.js
module.exports = {
  images: {
    domains: ['127.0.0.1', 'localhost'],
    // or use remotePatterns for more control:
    // remotePatterns: [
    //   { protocol: 'http', hostname: '127.0.0.1' },
    // ],
  },
}
```

3. Alternatively, you can proxy media files through your Next.js server (or serve them from the same origin as the frontend) to avoid adding remote domains.

4. If you still see "The requested resource isn't a valid image" when Next.js requests the URL, check the following:
   - Visit the absolute URL in the browser to confirm it returns the image bytes (not HTML or an auth redirect).
   - Ensure Django's MEDIA_URL and MEDIA_ROOT are correctly served in development (e.g., via `django.views.static.serve` when DEBUG=True, or via your production static/media server).
   - Confirm there is no authentication gate (redirect to login) for media files; media files should be publicly accessible or proxied by the frontend.

Example usage in React/Next.js (functional component):

```jsx
import Image from 'next/image'

export default function Avatar({ user }) {
  // user.profile_pic should be an absolute URL or null
  if (!user?.profile_pic) return <div className="avatar-placeholder" />

  return (
    <Image
      src={user.profile_pic}
      alt={user.full_name || 'Profile picture'}
      width={150}
      height={150}
      // optional: unoptimized if you want to skip Next.js optimization
      // unoptimized
    />
  )
}
```
