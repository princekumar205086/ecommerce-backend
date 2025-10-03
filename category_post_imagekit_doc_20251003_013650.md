# Category POST (ImageKit) Test Report

**Generated:** 2025-10-03T01:36:59.920631

## Endpoint

POST /api/products/categories/

## Authentication

- JWT Bearer token via POST /api/accounts/login/ (email + password)

## Payload (multipart/form-data)

Fields:
- name (string, required)
- icon_file (file, optional) - send image file in multipart/form-data under key 'icon_file'

Example multipart fields:
Content-Disposition: form-data; name="name"

My Category
--boundary
Content-Disposition: form-data; name="icon_file"; filename="category_icon.png"
Content-Type: image/png

<binary image bytes>


## Sample cURL (replace <TOKEN>)

curl -X POST 'http://localhost:8000/api/products/categories/' -H 'Authorization: Bearer <TOKEN>' -F 'name=My Category' -F 'icon_file=@category_icon.png'

## Actual Response (JSON)

```json
{
  "id": 132,
  "name": "ImageKit Test Category 20251003_013654",
  "parent": null,
  "created_at": "2025-10-03T01:36:59.909976+05:30",
  "status": "published",
  "is_publish": true,
  "icon": "https://ik.imagekit.io/medixmall/products_categories_category_01dcd7b7-c51c-4459-8686-6d47b206acfa_Jeom4voaB.png"
}
```

## Notes / Observations

Category created successfully (HTTP 201)
Icon appears to be uploaded and returned as URL: https://ik.imagekit.io/medixmall/products_categories_category_01dcd7b7-c51c-4459-8686-6d47b206acfa_Jeom4voaB.png