# CarouselBanner API — Complete Documentation

**Last Updated:** November 1, 2025  
**Version:** 1.0 with ImageKit Integration  
**Status:** ✅ Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Reference](#quick-reference)
3. [Model & Fields](#model--fields)
4. [Public API](#public-api)
5. [Admin API](#admin-api)
6. [Image Upload & ImageKit](#image-upload--imagekit)
7. [Error Handling](#error-handling)
8. [Testing Examples](#testing-examples)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The **CarouselBanner API** enables creation and management of carousel/slider banners for e-commerce platforms.

### Key Features

✅ **Public Endpoint** — Fetch active banners without authentication  
✅ **Admin CRUD Operations** — Create, read, update, delete with JWT authentication  
✅ **ImageKit CDN Storage** — All images hosted on ImageKit, not stored locally  
✅ **2 MB File Limit** — Enforced at application level  
✅ **Comprehensive Validation** — File type, size, and integrity checks  
✅ **Flexible Ordering** — Control banner display order  
✅ **Activation Toggle** — Show/hide banners without deletion  

### Base URL

```
/api/cms/
```

---

## Quick Reference

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `carousel/` | GET | Public | List active banners |
| `admin/carousels/` | GET | Admin | List all banners (paginated) |
| `admin/carousels/` | POST | Admin | Create banner |
| `admin/carousels/{id}/` | GET | Admin | Get banner detail |
| `admin/carousels/{id}/` | PATCH | Admin | Partial update |
| `admin/carousels/{id}/` | PUT | Admin | Full update |
| `admin/carousels/{id}/` | DELETE | Admin | Delete banner |

---

## Model & Fields

### CarouselBanner Fields

| Field | Type | Required | Max Length | Default | Notes |
|-------|------|----------|-----------|---------|-------|
| `id` | integer | ✗ | — | auto | Read-only, auto-generated |
| `title` | string | ✓ | 200 | — | Display name |
| `image` | string (URL) | ✓ | 500 | — | ImageKit URL (read-only in response) |
| `image_file` | file | (write-only) | — | — | Multipart upload field (POST/PATCH only) |
| `link` | URL | ✗ | 500 | "" | Clickable destination |
| `caption` | string | ✗ | 255 | "" | Overlay text |
| `order` | integer | ✗ | — | 0 | Sort order (lower = first) |
| `is_active` | boolean | ✗ | — | true | Public visibility |
| `created_at` | datetime | ✗ | — | auto | Read-only, creation timestamp |
| `updated_at` | datetime | ✗ | — | auto | Read-only, update timestamp |

### Example JSON Response

```json
{
  "id": 5,
  "title": "Summer Sale 2025",
  "image": "https://ik.imagekit.io/your-endpoint/carousel_banners/carousel_a1b2c3d4.jpg",
  "link": "https://example.com/summer-sale",
  "caption": "Up to 50% off selected items",
  "order": 0,
  "is_active": true,
  "created_at": "2025-11-01T10:30:45.123456Z",
  "updated_at": "2025-11-01T14:22:10.654321Z"
}
```

---

## Public API

### GET `/api/cms/carousel/`

Retrieve all active carousel banners (public, no authentication required).

**Response:** 200 OK with array of banners, ordered by `order` field.

```bash
curl "https://api.example.com/api/cms/carousel/"
```

**Response (200):**

```json
[
  {
    "id": 1,
    "title": "Featured Banner",
    "image": "https://ik.imagekit.io/.../carousel_001.jpg",
    "link": "https://example.com/featured",
    "caption": "New Collection",
    "order": 0,
    "is_active": true,
    "created_at": "2025-11-01T08:00:00Z",
    "updated_at": "2025-11-01T08:00:00Z"
  },
  {
    "id": 2,
    "title": "Promo Banner",
    "image": "https://ik.imagekit.io/.../carousel_002.jpg",
    "link": "https://example.com/promo",
    "caption": "Limited Time Offer",
    "order": 1,
    "is_active": true,
    "created_at": "2025-11-01T09:15:00Z",
    "updated_at": "2025-11-01T09:15:00Z"
  }
]
```

---

## Admin API

All admin endpoints require **JWT authentication** and **admin permissions**.

### Authentication

#### Obtaining JWT Token

```bash
curl -X POST "https://api.example.com/api/token/" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "password"}'
```

**Response:**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Using Token in Requests

Include in Authorization header:

```
Authorization: Bearer <access_token>
```

---

### GET `/api/cms/admin/carousels/`

List all carousel banners with pagination.

**Permission:** Admin only  
**Response:** 200 OK with paginated results

```bash
curl "https://api.example.com/api/cms/admin/carousels/" \
  -H "Authorization: Bearer <access_token>"
```

**Response (200):**

```json
{
  "count": 10,
  "next": "https://api.example.com/api/cms/admin/carousels/?page=2",
  "previous": null,
  "results": [
    { /* CarouselBanner object */ }
  ]
}
```

---

### POST `/api/cms/admin/carousels/`

Create a new carousel banner.

**Permission:** Admin only  
**Content-Type:** `multipart/form-data`  
**Response:** 201 Created

#### Request Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `title` | string | ✓ | Banner name (max 200 chars) |
| `image_file` | file | ✓ | Image upload (2 MB max, JPG/PNG/GIF/WEBP) |
| `link` | URL | ✗ | Destination link |
| `caption` | string | ✗ | Overlay text |
| `order` | integer | ✗ | Sort order |
| `is_active` | boolean | ✗ | Public visibility |

#### Example

```bash
curl -X POST "https://api.example.com/api/cms/admin/carousels/" \
  -H "Authorization: Bearer <access_token>" \
  -F "title=New Summer Banner" \
  -F "image_file=@banner.jpg" \
  -F "caption=Check our summer collection" \
  -F "link=https://example.com/summer" \
  -F "order=1" \
  -F "is_active=true"
```

**Success Response (201):**

```json
{
  "id": 15,
  "title": "New Summer Banner",
  "image": "https://ik.imagekit.io/your-endpoint/carousel_banners/carousel_xyz.jpg",
  "link": "https://example.com/summer",
  "caption": "Check our summer collection",
  "order": 1,
  "is_active": true,
  "created_at": "2025-11-01T15:45:30Z",
  "updated_at": "2025-11-01T15:45:30Z"
}
```

#### Error Responses

**Missing image (400):**
```json
{"image": ["Image is required."]}
```

**Image too large (400):**
```json
{"image_file": ["Image file too large. Maximum size allowed is 2 MB."]}
```

**Invalid format (400):**
```json
{"image_file": ["Unsupported image format. Allowed types: JPG, PNG, GIF, WEBP."]}
```

**Invalid JWT (401):**
```json
{"detail": "Authentication credentials were not provided."}
```

**Not admin (403):**
```json
{"detail": "Permission denied."}
```

---

### GET `/api/cms/admin/carousels/{id}/`

Retrieve a specific carousel banner.

**Permission:** Admin only  
**Response:** 200 OK or 404 Not Found

```bash
curl "https://api.example.com/api/cms/admin/carousels/15/" \
  -H "Authorization: Bearer <access_token>"
```

---

### PATCH `/api/cms/admin/carousels/{id}/`

Partially update a carousel banner (only provided fields).

**Permission:** Admin only  
**Content-Type:** `multipart/form-data` (if uploading image) or `application/json`

#### Example (Update title only)

```bash
curl -X PATCH "https://api.example.com/api/cms/admin/carousels/15/" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Summer Banner", "is_active": false}'
```

**Response (200):**
```json
{ /* Updated CarouselBanner object */ }
```

#### Example (Update image)

```bash
curl -X PATCH "https://api.example.com/api/cms/admin/carousels/15/" \
  -H "Authorization: Bearer <access_token>" \
  -F "image_file=@new_banner.jpg" \
  -F "title=Updated with New Image"
```

---

### PUT `/api/cms/admin/carousels/{id}/`

Fully replace a carousel banner (all fields required).

**Permission:** Admin only  
**Response:** 200 OK

Use PUT when you want to replace the entire object. PATCH is recommended for partial updates.

---

### DELETE `/api/cms/admin/carousels/{id}/`

Delete a carousel banner permanently.

**Permission:** Admin only  
**Response:** 204 No Content (empty body)

```bash
curl -X DELETE "https://api.example.com/api/cms/admin/carousels/15/" \
  -H "Authorization: Bearer <access_token>"
```

**Success:** HTTP 204 (no response body)

**Error (404):**
```json
{"detail": "Not found."}
```

---

## Image Upload & ImageKit

### Storage Details

- **Backend:** ImageKit CDN (not local storage)
- **Upload Folder:** `carousel_banners/`
- **URL Format:** Full ImageKit HTTPS CDN URLs  
- **File Naming:** Auto-generated UUID-based names (e.g., `carousel_a1b2c3d4.jpg`)

### Size & Format Limits

| Requirement | Value |
|------------|-------|
| **Max Size** | 2 MB (enforced at app level) |
| **Allowed Formats** | JPG, JPEG, PNG, GIF, WEBP |
| **Minimum Size** | 1 byte (recommended ≥ 100 KB for quality) |

### Handling 413 Request Entity Too Large

If your reverse proxy blocks uploads:

**nginx fix:**

```nginx
server {
    listen 80;
    server_name example.com;
    
    # Allow 10 MB at proxy (Django enforces 2 MB internally)
    client_max_body_size 10M;
    
    location / {
        proxy_pass http://django-backend;
    }
}
```

Reload nginx:
```bash
sudo systemctl reload nginx
```

**Apache fix:**

```apache
<Directory /var/www/app>
    LimitRequestBody 10485760  # 10 MB in bytes
</Directory>
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | GET/PATCH/PUT successful |
| 201 | Created | POST successful |
| 204 | No Content | DELETE successful |
| 400 | Bad Request | Invalid data, file too large |
| 401 | Unauthorized | Missing/invalid JWT |
| 403 | Forbidden | User not admin |
| 404 | Not Found | Resource doesn't exist |
| 413 | Request Too Large | Proxy rejected (fix nginx config) |

### Common Error Messages

| Error | Cause | Fix |
|-------|-------|-----|
| "Image is required" | No image_file provided on create | Upload an image |
| "Image file too large" | File > 2 MB | Compress image or use smaller file |
| "Unsupported image format" | Wrong file type | Use JPG, PNG, GIF, or WEBP |
| "Invalid image file" | Corrupted or invalid image | Re-save or re-upload the image |
| "Image upload to ImageKit failed" | ImageKit API error | Check IMAGEKIT credentials in .env |
| "Authentication credentials not provided" | Missing JWT token | Include Authorization header |
| "Permission denied" | User not admin | Use superuser account |

---

## Testing Examples

### 1. Create Superuser

```bash
python manage.py createsuperuser
# Follow prompts to create admin account
```

### 2. Get Access Token

```bash
curl -X POST "http://localhost:8000/api/token/" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}'
```

Save the `access` token value.

### 3. Create Carousel

```bash
TOKEN="eyJ0eXAiOiJKV1Q..."

curl -X POST "http://localhost:8000/api/cms/admin/carousels/" \
  -H "Authorization: Bearer $TOKEN" \
  -F "title=Test Banner" \
  -F "image_file=@test.jpg" \
  -F "is_active=true"
```

### 4. List Carousels

```bash
curl "http://localhost:8000/api/cms/admin/carousels/" \
  -H "Authorization: Bearer $TOKEN"
```

### 5. Test Public Endpoint

```bash
curl "http://localhost:8000/api/cms/carousel/"
# Should return only is_active=true items
```

### Python/Django Shell Test

```python
from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()
admin_user = User.objects.create_superuser('test@example.com', 'password')
token = str(RefreshToken.for_user(admin_user).access_token)

client = Client(HTTP_AUTHORIZATION=f'Bearer {token}')
response = client.get('/api/cms/admin/carousels/')
print(response.status_code)  # Should be 200
print(response.json())
```

---

## Troubleshooting

### "Image file too large. Maximum size allowed is 2 MB."

**Cause:** File exceeds 2 MB limit  
**Solution:** 
- Check file size: `ls -lh filename.jpg`
- Compress image using online tools or ImageMagick:
  ```bash
  convert input.jpg -quality 85 output.jpg
  ```

### "Unsupported image format"

**Cause:** File type not in [JPG, PNG, GIF, WEBP]  
**Solution:**
- Convert file: `convert input.bmp output.jpg`
- Or use online converters

### "413 Request Entity Too Large"

**Cause:** Reverse proxy (nginx/Apache) rejects before Django  
**Solution:** Update proxy config (see "Handling 413" section above)

### "Image upload to ImageKit failed"

**Cause:** ImageKit credentials missing or invalid  
**Solution:**
- Check `.env` file has:
  ```
  IMAGEKIT_PRIVATE_KEY=...
  IMAGEKIT_PUBLIC_KEY=...
  IMAGEKIT_URL_ENDPOINT=...
  ```
- Test ImageKit credentials separately

### "401 Unauthorized"

**Cause:** Missing or invalid JWT  
**Solution:**
- Get new token from `/api/token/`
- Include full header: `Authorization: Bearer <token>`

### "403 Forbidden"

**Cause:** User is authenticated but not admin  
**Solution:**
- Create superuser: `python manage.py createsuperuser`
- Or set `is_staff=true` on user in admin panel

---

## Frontend Integration Example

### JavaScript/Fetch

```javascript
// Get active carousels (public)
fetch('/api/cms/carousel/')
  .then(r => r.json())
  .then(data => {
    console.log('Active carousels:', data);
    // Render carousels on page
  });
```

### File Upload with Validation

```html
<input type="file" id="bannerImage" accept="image/*" />
<div id="error" style="color: red;"></div>

<script>
document.getElementById('bannerImage').addEventListener('change', e => {
  const file = e.target.files[0];
  const maxSize = 2 * 1024 * 1024; // 2 MB
  const allowed = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
  
  if (!file) return;
  if (!allowed.includes(file.type)) {
    document.getElementById('error').textContent = 
      '❌ Invalid type. Use: JPG, PNG, GIF, WEBP';
    e.target.value = '';
    return;
  }
  if (file.size > maxSize) {
    document.getElementById('error').textContent = 
      `❌ File too large (${(file.size/1024/1024).toFixed(2)} MB). Max: 2 MB`;
    e.target.value = '';
    return;
  }
  document.getElementById('error').textContent = '✅ File valid';
});
</script>
```

---

## API Documentation

**Swagger UI:** `/swagger/`  
**ReDoc:** `/redoc/`  
**OpenAPI JSON:** `/swagger.json`

---

## Environment Configuration

### Required `.env` Variables

```bash
# ImageKit credentials (for image uploads)
IMAGEKIT_PRIVATE_KEY=your_private_key
IMAGEKIT_PUBLIC_KEY=your_public_key
IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/your-endpoint
```

### Django Settings

```python
# In ecommerce/settings.py
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
```

---

## Future Enhancements

- [ ] Add Swagger `@swagger_auto_schema` decorators
- [ ] Add advanced search/filtering (title search, date range)
- [ ] Add start/end activation dates (like Banner model)
- [ ] Add view analytics (track carousel impressions)
- [ ] Add admin dashboard with drag-drop reordering
- [ ] Add carousel placement targeting (homepage, category pages)
- [ ] Add A/B testing support

---

**Support:** For issues or questions, refer to troubleshooting section or contact admin team.
