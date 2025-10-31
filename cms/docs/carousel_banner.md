# CarouselBanner API — Documentation

This document describes the CarouselBanner model and all API endpoints implemented for it in the `cms` app.

Base API prefix used by the project: `/api/cms/`

## Summary

- Public (no auth):
  - GET /api/cms/carousel/ — list active carousel banners (public fetch for frontend)

- Admin (JWT authenticated, admin-only):
  - GET /api/cms/admin/carousels/ — list all carousel banners
  - POST /api/cms/admin/carousels/ — create a new carousel banner (multipart/form-data for image)
  - GET /api/cms/admin/carousels/{id}/ — retrieve a carousel banner detail
  - PATCH /api/cms/admin/carousels/{id}/ — partial update
  - PUT /api/cms/admin/carousels/{id}/ — full update
  - DELETE /api/cms/admin/carousels/{id}/ — delete

## Model / Serializer structure

CarouselBanner model fields (as exposed by the API):

- id: integer (read-only)
- title: string (required)
- image: file / URL (required for create via API; on response this is the absolute/media URL)
- link: string (URL, optional)
- caption: string (optional)
- order: integer (default: 0) — controls display order; lower values come first
- is_active: boolean (default: true) — whether this item should be shown publicly
- created_at: datetime (read-only)
- updated_at: datetime (read-only)

JSON schema (response) example

```json
{
  "id": 7,
  "title": "Summer Sale",
  "image": "https://example.com/media/carousel_banners/summer.jpg",
  "link": "https://example.com/sale",
  "caption": "Up to 50% off",
  "order": 0,
  "is_active": true,
  "created_at": "2025-11-01T10:00:00Z",
  "updated_at": "2025-11-01T10:00:00Z"
}
```

Notes:
- The `image` field on responses is a URL pointing to the media file (depends on your MEDIA_URL / storage setup).
- When creating/updating via API you must upload the file as `multipart/form-data` (see examples below).

## Public endpoint — Fetch active carousel banners

GET /api/cms/carousel/

- Description: Returns a list of active CarouselBanner objects ordered by `order`.
- Permission: AllowAny (public)
- Query parameters: none implemented (returns all items with `is_active=true` ordered by `order`).
- Response: 200 OK with JSON array of CarouselBanner objects.

Example response (200):

```json
[
  {
    "id": 3,
    "title": "T3",
    "image": "http://testserver/media/carousel_banners/dummy3.jpg",
    "link": "",
    "caption": "",
    "order": 0,
    "is_active": true,
    "created_at": "2025-11-01T01:36:39.182173+05:30",
    "updated_at": "2025-11-01T01:36:39.182173+05:30"
  }
]
```

## Admin endpoints — CRUD (admin-only)

All admin endpoints require authentication using the project's configured authentication method (JWT). The project uses `rest_framework_simplejwt` for JWT tokens. Include the token in the `Authorization` header:

Authorization: Bearer <access_token>

Permissions: `IsAdminUser` (DRF default) — only admin/superuser users can use these endpoints. Unauthenticated requests will return 401. Authenticated non-admin users will receive 403 (forbidden) where applicable.

### List (admin)

GET /api/cms/admin/carousels/

- Description: Returns a list of all CarouselBanner objects (admin view), ordered by `order`.
- Permission: Admin only (JWT required)
- Response: 200 OK with paginated list (project default pagination applies).

Example response (200):

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    { /* CarouselBanner object */ }
  ]
}
```

### Create (admin)

POST /api/cms/admin/carousels/

- Content-Type: multipart/form-data
- Body fields:
  - title: string (required)
  - image: file (required) — multipart file upload
  - link: string (optional)
  - caption: string (optional)
  - order: integer (optional)
  - is_active: boolean (optional)
- Permission: Admin only (JWT required)
- Responses:
  - 201 Created — returns created object
  - 400 Bad Request — validation errors (e.g., missing image)

Example cURL (file upload):

```bash
curl -X POST "https://example.com/api/cms/admin/carousels/" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F "title=Homepage Promo" \
  -F "image=@/path/to/banner.jpg" \
  -F "link=https://example.com/promo" \
  -F "caption=Big sale" \
  -F "order=1" \
  -F "is_active=true"
```

Successful response (201): returns the created object in the same format as the read schema.

Validation error example (400):

```json
{
  "image": ["No file was submitted."]
}
```

### Retrieve (admin)

GET /api/cms/admin/carousels/{id}/

- Permission: Admin only (JWT required)
- Success: 200 OK with the CarouselBanner object
- Not found: 404

### Update / Partial update (admin)

PUT /api/cms/admin/carousels/{id}/
PATCH /api/cms/admin/carousels/{id}/

- Content-Type: multipart/form-data for file updates, or application/json for non-file fields with PATCH/PUT if you do not update `image`.
- Fields: same as Create.
- Permission: Admin only
- Responses:
  - 200 OK — updated object
  - 400 Bad Request — validation errors
  - 401 / 403 — unauthorized/forbidden

Example PATCH (change title) using JSON body:

```http
PATCH /api/cms/admin/carousels/3/
Authorization: Bearer <ACCESS_TOKEN>
Content-Type: application/json

{"title": "Updated Title"}
```

### Delete (admin)

DELETE /api/cms/admin/carousels/{id}/

- Permission: Admin only
- Responses:
  - 204 No Content — deleted successfully
  - 404 Not Found — if id doesn't exist

## Errors and status codes

- 200 OK — successful GET/PUT/PATCH
- 201 Created — successful POST
- 204 No Content — successful DELETE
- 400 Bad Request — invalid payload or missing required fields
- 401 Unauthorized — missing/invalid authentication
- 403 Forbidden — authenticated but lacks admin privileges
- 404 Not Found — resource not found

## Testing notes (quick)

- The project uses JWT auth. To test admin endpoints:
  1. Create an admin user (superuser) using `createsuperuser` or via ORM.
  2. Obtain a JWT access token (login via `/api/token/` or generate token in shell using rest_framework_simplejwt RefreshToken.for_user).
  3. Include header `Authorization: Bearer <token>` in requests.

- Example using Django test client in a shell

```python
from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
User = get_user_model()
user = User.objects.create_superuser('admin@example.com', 'testpass')
refresh = RefreshToken.for_user(user)
access = str(refresh.access_token)
client = Client(HTTP_AUTHORIZATION=f'Bearer {access}')
client.get('/api/cms/admin/carousels/')
```

## Recommendations / Next steps

- Add swagger_auto_schema annotations for the newly-added views to include them in API docs (consistent with other CMS views).
- Add automated tests in `cms/tests.py` to:
  - Verify public GET returns only `is_active` items.
  - Verify admin CRUD operations (including a multipart file upload test using `django.core.files.uploadedfile.SimpleUploadedFile`).
- Optionally implement filtering (e.g., `is_active`, `order`, search by title) and pagination customizations for admin list view.

If you want, I can add the automated tests and Swagger annotations now.
