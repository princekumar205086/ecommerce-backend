#!/usr/bin/env python3
"""
Category POST test with ImageKit upload and generated markdown documentation.

- Authenticates as admin (admin@example.com / Admin@123)
- Creates a small PNG in-memory and uploads it to the category POST endpoint as `icon_file`
- Verifies response (201) and that `icon` field contains a URL (uploaded to ImageKit or returned)
- Deletes the created category to keep the test environment clean
- Saves a markdown document with endpoint, payload example and the actual response
"""
import io
import json
import sys
import os
from datetime import datetime

import requests
from PIL import Image

BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = "/api/accounts/login/"
CATEGORIES_ENDPOINT = "/api/products/categories/"

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "Admin@123"

DOC_FILENAME = f"category_post_imagekit_doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"


def make_png_bytes():
    """Create a simple 64x64 PNG image in-memory and return bytes."""
    img = Image.new('RGBA', (64, 64), (0, 150, 136, 255))
    bio = io.BytesIO()
    img.save(bio, format='PNG')
    bio.seek(0)
    return bio.read()


def login(email, password):
    url = f"{BASE_URL}{LOGIN_ENDPOINT}"
    payload = {'email': email, 'password': password}
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r
    except Exception as e:
        print(f"Login request failed: {e}")
        return None


def create_category(token, name, image_bytes, filename='category_icon.png'):
    url = f"{BASE_URL}{CATEGORIES_ENDPOINT}"
    headers = {'Authorization': f'Bearer {token}'}
    files = {
        'icon_file': (filename, image_bytes, 'image/png')
    }
    data = {
        'name': name
    }
    try:
        r = requests.post(url, headers=headers, files=files, data=data, timeout=30)
        return r
    except Exception as e:
        print(f"Category create request failed: {e}")
        return None


def delete_category(token, category_id):
    url = f"{BASE_URL}{CATEGORIES_ENDPOINT}{category_id}/"
    headers = {'Authorization': f'Bearer {token}'}
    try:
        r = requests.delete(url, headers=headers, timeout=10)
        return r
    except Exception as e:
        print(f"Category delete request failed: {e}")
        return None


def save_markdown(doc_path, endpoint, payload_desc, response_json, notes):
    md = []
    md.append(f"# Category POST (ImageKit) Test Report")
    md.append("")
    md.append(f"**Generated:** {datetime.now().isoformat()}")
    md.append("")
    md.append("## Endpoint")
    md.append("")
    md.append(f"POST {endpoint}")
    md.append("")
    md.append("## Authentication")
    md.append("")
    md.append("- JWT Bearer token via POST /api/accounts/login/ (email + password)")
    md.append("")
    md.append("## Payload (multipart/form-data)")
    md.append("")
    md.append(payload_desc)
    md.append("")
    md.append("## Sample cURL (replace <TOKEN>)")
    md.append("")
    md.append("curl -X POST '{base_url}{endpoint}' -H 'Authorization: Bearer <TOKEN>' -F 'name=My Category' -F 'icon_file=@category_icon.png'".replace('{base_url}', BASE_URL).replace('{endpoint}', endpoint))
    md.append("")
    md.append("## Actual Response (JSON)")
    md.append("")
    md.append('```json')
    md.append(json.dumps(response_json, indent=2))
    md.append('```')
    md.append("")
    md.append("## Notes / Observations")
    md.append("")
    md.append(notes)

    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))


def main():
    print("Starting Category POST (ImageKit) test...")

    # Create image bytes
    img_bytes = make_png_bytes()

    # Authenticate
    print("Logging in as admin...")
    login_resp = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    if not login_resp:
        print("Login failed: no response from server")
        return 1

    if login_resp.status_code != 200:
        print(f"Login failed: {login_resp.status_code} {login_resp.text}")
        return 1

    token = login_resp.json().get('access')
    if not token:
        print("Login succeeded but no access token returned")
        return 1

    print("Authenticated successfully. Creating category with icon upload...")
    name = f"ImageKit Test Category {datetime.now().strftime('%Y%m%d_%H%M%S')}"
    create_resp = create_category(token, name, img_bytes)

    if not create_resp:
        print("Category create failed: no response")
        return 1

    response_ok = (create_resp.status_code == 201)
    try:
        response_json = create_resp.json()
    except Exception:
        response_json = {'raw_text': create_resp.text}

    # Determine success notes
    notes = []
    if response_ok:
        notes.append("Category created successfully (HTTP 201)")
        icon_val = response_json.get('icon')
        if icon_val and isinstance(icon_val, str) and icon_val.startswith('http'):
            notes.append(f"Icon appears to be uploaded and returned as URL: {icon_val}")
        else:
            notes.append(f"Icon was not returned as an absolute URL. Returned value: {icon_val}")
    else:
        notes.append(f"Category creation failed with status {create_resp.status_code}")

    # Save markdown documentation
    payload_desc = (
        "Fields:\n"
        "- name (string, required)\n"
        "- icon_file (file, optional) - send image file in multipart/form-data under key 'icon_file'\n"
        "\nExample multipart fields:\n"
        "Content-Disposition: form-data; name=\"name\"\r\n\r\nMy Category\r\n"
        "--boundary\r\nContent-Disposition: form-data; name=\"icon_file\"; filename=\"category_icon.png\"\r\nContent-Type: image/png\r\n\r\n<binary image bytes>\r\n"
    )

    save_markdown(DOC_FILENAME, CATEGORIES_ENDPOINT, payload_desc, response_json, '\n'.join(notes))
    print(f"Documentation saved to {DOC_FILENAME}")

    # Cleanup: delete created category if created successfully
    if response_ok and response_json.get('id'):
        cat_id = response_json['id']
        print(f"Deleting created category {cat_id} to keep environment clean...")
        del_resp = delete_category(token, cat_id)
        if del_resp and del_resp.status_code in (204, 200):
            print(f"Deleted category {cat_id} (status: {del_resp.status_code})")
        else:
            print(f"Failed to delete category {cat_id}. Response: {del_resp.status_code if del_resp else 'No response'}")

    print('Done.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
