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

Last updated: October 10, 2025
