# Address API - Quick Reference Card

## 🔐 Authentication

**Login:** `POST /api/accounts/login/`
```json
{"email": "user@example.com", "password": "User@123"}
```
**Response:** Store `access` token for Authorization header

---

## 📍 Endpoints

### 1. Get Address
```
GET /api/accounts/address/
Headers: Authorization: Bearer <token>
```

### 2. Create Address
```
POST /api/accounts/address/
Headers: Authorization: Bearer <token>
Body: {
  "address_line_1": "123 Street",
  "address_line_2": "Apt 4B",
  "city": "Mumbai",
  "state": "Maharashtra",
  "postal_code": "400001",
  "country": "India"
}
```

### 3. Update Address
```
PUT /api/accounts/address/
Headers: Authorization: Bearer <token>
Body: {same as POST}
```

### 4. Delete Address
```
DELETE /api/accounts/address/
Headers: Authorization: Bearer <token>
```

### 5. Save from Checkout
```
POST /api/accounts/address/save-from-checkout/
Headers: Authorization: Bearer <token>
Body: {
  "shipping_address": {
    "full_name": "John Doe",
    "address_line_1": "...",
    "city": "...",
    "state": "...",
    "postal_code": "...",
    "country": "India"
  }
}
```

---

## ✅ Required Fields

- `address_line_1` ✅
- `city` ✅
- `state` ✅
- `postal_code` ✅
- `country` ✅
- `address_line_2` ❌ (optional)

---

## 📦 Response Structure

```json
{
  "message": "Address created/updated successfully",
  "address": {
    "id": 16,
    "email": "user@example.com",
    "full_name": "Test User",
    "contact": "9876543210",
    "address_line_1": "123 Street",
    "address_line_2": "Apt 4B",
    "city": "Mumbai",
    "state": "Maharashtra",
    "postal_code": "400001",
    "country": "India",
    "has_address": true
  }
}
```

---

## 🔢 Status Codes

- `200 OK` - GET, PUT, DELETE success
- `201 Created` - POST success
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Missing/invalid token

---

## ⚡ Quick JavaScript

```javascript
// Login
const login = async () => {
  const res = await fetch('http://127.0.0.1:8000/api/accounts/login/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({email: 'user@example.com', password: 'User@123'})
  });
  const data = await res.json();
  localStorage.setItem('token', data.access);
};

// Get Address
const getAddress = async () => {
  const token = localStorage.getItem('token');
  const res = await fetch('http://127.0.0.1:8000/api/accounts/address/', {
    headers: {'Authorization': `Bearer ${token}`}
  });
  return await res.json();
};

// Create/Update Address
const saveAddress = async (addressData) => {
  const token = localStorage.getItem('token');
  const res = await fetch('http://127.0.0.1:8000/api/accounts/address/', {
    method: 'POST', // or 'PUT' for update
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(addressData)
  });
  return await res.json();
};
```

---

## 📝 Notes

- Always include Authorization header
- Validate required fields before submit
- Check `has_address` to determine if address exists
- Handle 401 errors (token expired)
- Country defaults to "India"

---

**Full Documentation:** See `ADDRESS_API_GUIDE.md`  
**Test Results:** See `ADDRESS_API_TEST_RESULTS.md`
