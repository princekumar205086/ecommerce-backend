# User Address Management API - Frontend Integration Guide

## 📋 Overview

This guide provides comprehensive documentation for the User Address Management system in the eCommerce backend. It covers all endpoints, authentication requirements, request/response structures, and example implementations.

---

## 🔐 Authentication

All address endpoints require JWT authentication. Include the access token in the Authorization header.

### Login to Get Access Token

**Endpoint:** `POST /api/accounts/login/`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "User@123"
}
```

**Response:**
```json
{
  "user": {
    "id": 16,
    "email": "user@example.com",
    "full_name": "Test User",
    "contact": "9876543210",
    "role": "user",
    "has_address": false,
    "medixmall_mode": false,
    "email_verified": true
  },
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Store the `access` token** for use in subsequent requests.

---

## 📍 Address Endpoints

### Base URL
```
http://127.0.0.1:8000/api/accounts/
```

---

## 1️⃣ GET User Address

Retrieve the current user's saved address.

### Endpoint
```
GET /api/accounts/address/
```

### Headers
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Request
No request body required.

### Response (200 OK)
```json
{
  "id": 16,
  "email": "user@example.com",
  "full_name": "Test User",
  "contact": "9876543210",
  "address_line_1": "123 MG Road",
  "address_line_2": "Apartment 4B",
  "city": "Mumbai",
  "state": "Maharashtra",
  "postal_code": "400001",
  "country": "India",
  "has_address": true
}
```

### Response (No Address Saved)
```json
{
  "id": 16,
  "email": "user@example.com",
  "full_name": "Test User",
  "contact": "9876543210",
  "address_line_1": null,
  "address_line_2": null,
  "city": null,
  "state": null,
  "postal_code": null,
  "country": "India",
  "has_address": false
}
```

### Example JavaScript/Fetch
```javascript
const getAddress = async () => {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://127.0.0.1:8000/api/accounts/address/', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  const data = await response.json();
  console.log(data);
  return data;
};
```

### Example Axios
```javascript
import axios from 'axios';

const getAddress = async () => {
  const token = localStorage.getItem('access_token');
  
  const response = await axios.get('http://127.0.0.1:8000/api/accounts/address/', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return response.data;
};
```

---

## 2️⃣ POST Create Address

Create/save a new address for the user.

### Endpoint
```
POST /api/accounts/address/
```

### Headers
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Request Body (Required Fields)
```json
{
  "address_line_1": "123 MG Road",
  "address_line_2": "Apartment 4B",
  "city": "Mumbai",
  "state": "Maharashtra",
  "postal_code": "400001",
  "country": "India"
}
```

### Field Validations
| Field | Type | Required | Max Length | Description |
|-------|------|----------|------------|-------------|
| `address_line_1` | string | ✅ Yes | 255 | Primary address line |
| `address_line_2` | string | ❌ No | 255 | Secondary address (apartment, suite, etc.) |
| `city` | string | ✅ Yes | 100 | City name |
| `state` | string | ✅ Yes | 100 | State/Province name |
| `postal_code` | string | ✅ Yes | 20 | ZIP/Postal code |
| `country` | string | ✅ Yes | 100 | Country name (default: "India") |

### Response (201 Created)
```json
{
  "message": "Address created successfully",
  "address": {
    "id": 16,
    "email": "user@example.com",
    "full_name": "Test User",
    "contact": "9876543210",
    "address_line_1": "123 MG Road",
    "address_line_2": "Apartment 4B",
    "city": "Mumbai",
    "state": "Maharashtra",
    "postal_code": "400001",
    "country": "India",
    "has_address": true
  }
}
```

### Error Response (400 Bad Request)
```json
{
  "required_fields": "Missing required fields: address_line_1, city, state, postal_code, country"
}
```

### Example JavaScript/Fetch
```javascript
const createAddress = async (addressData) => {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://127.0.0.1:8000/api/accounts/address/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(addressData)
  });
  
  const data = await response.json();
  return data;
};

// Usage
const newAddress = {
  address_line_1: "123 MG Road",
  address_line_2: "Apartment 4B",
  city: "Mumbai",
  state: "Maharashtra",
  postal_code: "400001",
  country: "India"
};

createAddress(newAddress);
```

### Example React Component
```jsx
import React, { useState } from 'react';
import axios from 'axios';

const AddressForm = () => {
  const [formData, setFormData] = useState({
    address_line_1: '',
    address_line_2: '',
    city: '',
    state: '',
    postal_code: '',
    country: 'India'
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('access_token');
    
    try {
      const response = await axios.post(
        'http://127.0.0.1:8000/api/accounts/address/',
        formData,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      console.log('Address created:', response.data);
      alert('Address saved successfully!');
    } catch (error) {
      console.error('Error:', error.response.data);
      alert('Failed to save address');
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        name="address_line_1"
        value={formData.address_line_1}
        onChange={handleChange}
        placeholder="Address Line 1"
        required
      />
      <input
        name="address_line_2"
        value={formData.address_line_2}
        onChange={handleChange}
        placeholder="Address Line 2 (Optional)"
      />
      <input
        name="city"
        value={formData.city}
        onChange={handleChange}
        placeholder="City"
        required
      />
      <input
        name="state"
        value={formData.state}
        onChange={handleChange}
        placeholder="State"
        required
      />
      <input
        name="postal_code"
        value={formData.postal_code}
        onChange={handleChange}
        placeholder="Postal Code"
        required
      />
      <input
        name="country"
        value={formData.country}
        onChange={handleChange}
        placeholder="Country"
        required
      />
      <button type="submit">Save Address</button>
    </form>
  );
};

export default AddressForm;
```

---

## 3️⃣ PUT Update Address

Update existing user address.

### Endpoint
```
PUT /api/accounts/address/
```

### Headers
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Request Body
```json
{
  "address_line_1": "456 Linking Road",
  "address_line_2": "Suite 10",
  "city": "Mumbai",
  "state": "Maharashtra",
  "postal_code": "400050",
  "country": "India"
}
```

### Response (200 OK)
```json
{
  "message": "Address updated successfully",
  "address": {
    "id": 16,
    "email": "user@example.com",
    "full_name": "Test User",
    "contact": "9876543210",
    "address_line_1": "456 Linking Road",
    "address_line_2": "Suite 10",
    "city": "Mumbai",
    "state": "Maharashtra",
    "postal_code": "400050",
    "country": "India",
    "has_address": true
  }
}
```

### Example JavaScript/Fetch
```javascript
const updateAddress = async (addressData) => {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://127.0.0.1:8000/api/accounts/address/', {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(addressData)
  });
  
  const data = await response.json();
  return data;
};
```

---

## 4️⃣ DELETE Address

Delete the user's saved address (resets to null/empty).

### Endpoint
```
DELETE /api/accounts/address/
```

### Headers
```
Authorization: Bearer <access_token>
```

### Request
No request body required.

### Response (200 OK)
```json
{
  "message": "Address deleted successfully"
}
```

### Example JavaScript/Fetch
```javascript
const deleteAddress = async () => {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://127.0.0.1:8000/api/accounts/address/', {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  console.log(data.message); // "Address deleted successfully"
  return data;
};
```

---

## 5️⃣ Save Address from Checkout

Save address during checkout flow (includes full_name update).

### Endpoint
```
POST /api/accounts/address/save-from-checkout/
```

### Headers
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Request Body
```json
{
  "shipping_address": {
    "full_name": "Test User Updated",
    "address_line_1": "789 Park Street",
    "address_line_2": "Floor 3",
    "city": "Kolkata",
    "state": "West Bengal",
    "postal_code": "700016",
    "country": "India"
  }
}
```

### Response (200 OK)
```json
{
  "message": "Address saved successfully for future use",
  "address": {
    "address_line_1": "789 Park Street",
    "address_line_2": "Floor 3",
    "city": "Kolkata",
    "state": "West Bengal",
    "postal_code": "700016",
    "country": "India",
    "has_address": true
  }
}
```

### Example JavaScript/Fetch
```javascript
const saveAddressFromCheckout = async (shippingAddress) => {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://127.0.0.1:8000/api/accounts/address/save-from-checkout/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ shipping_address: shippingAddress })
  });
  
  const data = await response.json();
  return data;
};

// Usage
const shippingInfo = {
  full_name: "John Doe",
  address_line_1: "789 Park Street",
  address_line_2: "Floor 3",
  city: "Kolkata",
  state: "West Bengal",
  postal_code: "700016",
  country: "India"
};

saveAddressFromCheckout(shippingInfo);
```

---

## 🔄 Complete Flow Example

### Full Address Management Workflow

```javascript
// 1. Login and get token
const login = async (email, password) => {
  const response = await fetch('http://127.0.0.1:8000/api/accounts/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  const data = await response.json();
  localStorage.setItem('access_token', data.access);
  localStorage.setItem('refresh_token', data.refresh);
  return data;
};

// 2. Check if user has address
const checkAddress = async () => {
  const token = localStorage.getItem('access_token');
  const response = await fetch('http://127.0.0.1:8000/api/accounts/address/', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  const data = await response.json();
  return data.has_address;
};

// 3. Create or update address based on existence
const saveAddress = async (addressData) => {
  const token = localStorage.getItem('access_token');
  const hasAddress = await checkAddress();
  
  const method = hasAddress ? 'PUT' : 'POST';
  
  const response = await fetch('http://127.0.0.1:8000/api/accounts/address/', {
    method: method,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(addressData)
  });
  
  return await response.json();
};

// 4. Usage
(async () => {
  // Login
  await login('user@example.com', 'User@123');
  
  // Check if address exists
  const hasAddress = await checkAddress();
  console.log('User has address:', hasAddress);
  
  // Save address
  const addressData = {
    address_line_1: "123 Main St",
    address_line_2: "Apt 4B",
    city: "Mumbai",
    state: "Maharashtra",
    postal_code: "400001",
    country: "India"
  };
  
  const result = await saveAddress(addressData);
  console.log('Address saved:', result);
})();
```

---

## 🛡️ Error Handling

### Common Error Responses

#### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```
**Solution:** Ensure the Authorization header includes a valid Bearer token.

#### 400 Bad Request - Missing Fields
```json
{
  "required_fields": "Missing required fields: city, state, postal_code"
}
```
**Solution:** Provide all required fields in the request body.

#### 400 Bad Request - Validation Error
```json
{
  "address_line_1": ["This field is required."],
  "postal_code": ["This field is required."]
}
```
**Solution:** Check the specific field errors and correct the input.

### Example Error Handling in React
```jsx
const handleAddressSave = async (addressData) => {
  const token = localStorage.getItem('access_token');
  
  try {
    const response = await axios.post(
      'http://127.0.0.1:8000/api/accounts/address/',
      addressData,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    
    alert('Address saved successfully!');
    return response.data;
    
  } catch (error) {
    if (error.response) {
      // Server responded with error
      if (error.response.status === 401) {
        alert('Session expired. Please login again.');
        // Redirect to login
      } else if (error.response.status === 400) {
        const errors = error.response.data;
        console.error('Validation errors:', errors);
        alert('Please check all required fields.');
      }
    } else {
      // Network error
      alert('Network error. Please try again.');
    }
  }
};
```

---

## 📊 Data Model Structure

### User Model (Address Fields)

```typescript
interface UserAddress {
  id: number;
  email: string;
  full_name: string;
  contact: string;
  address_line_1: string | null;
  address_line_2: string | null;
  city: string | null;
  state: string | null;
  postal_code: string | null;
  country: string;
  has_address: boolean;
}
```

### Address Request Payload

```typescript
interface AddressPayload {
  address_line_1: string;
  address_line_2?: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
}
```

### Checkout Address Payload

```typescript
interface CheckoutAddressPayload {
  shipping_address: {
    full_name: string;
    address_line_1: string;
    address_line_2?: string;
    city: string;
    state: string;
    postal_code: string;
    country: string;
  };
}
```

---

## 🧪 Testing with PowerShell

### Test Credentials
```
Email: user@example.com
Password: User@123
```

### Get Token
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/accounts/login/" -Method POST -ContentType "application/json" -Body '{"email": "user@example.com", "password": "User@123"}' | ConvertTo-Json
```

### GET Address
```powershell
$token = "YOUR_ACCESS_TOKEN_HERE"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/accounts/address/" -Method GET -Headers @{Authorization = "Bearer $token"} | ConvertTo-Json
```

### POST Address
```powershell
$token = "YOUR_ACCESS_TOKEN_HERE"
$body = '{"address_line_1": "123 MG Road", "address_line_2": "Apt 4B", "city": "Mumbai", "state": "Maharashtra", "postal_code": "400001", "country": "India"}'
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/accounts/address/" -Method POST -ContentType "application/json" -Headers @{Authorization = "Bearer $token"} -Body $body | ConvertTo-Json
```

---

## 📝 Quick Reference

### Endpoint Summary

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| GET | `/api/accounts/address/` | Get user address | ✅ |
| POST | `/api/accounts/address/` | Create new address | ✅ |
| PUT | `/api/accounts/address/` | Update existing address | ✅ |
| DELETE | `/api/accounts/address/` | Delete address | ✅ |
| POST | `/api/accounts/address/save-from-checkout/` | Save address from checkout | ✅ |

### Required Headers

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Status Codes

- `200 OK` - Successful GET, PUT, DELETE, or checkout save
- `201 Created` - Successful POST (address created)
- `400 Bad Request` - Validation error or missing fields
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Insufficient permissions

---

## 🚀 Integration Checklist

- [ ] Store access token securely after login
- [ ] Include Authorization header in all requests
- [ ] Handle token expiration and refresh
- [ ] Validate form inputs before submission
- [ ] Handle error responses appropriately
- [ ] Show loading states during API calls
- [ ] Display success/error messages to users
- [ ] Pre-fill form with existing address data
- [ ] Implement proper state management
- [ ] Test all CRUD operations

---

## 🔗 Related Endpoints

### Authentication
- `POST /api/accounts/login/` - Login to get tokens
- `POST /api/accounts/token/refresh/` - Refresh access token
- `POST /api/accounts/logout/` - Logout user

### User Profile
- `GET /api/accounts/me/` - Get user profile
- `PUT /api/accounts/me/` - Update user profile

---

## 📞 Support

For any issues or questions:
- Check Swagger docs: `http://127.0.0.1:8000/swagger/`
- Review API documentation: `http://127.0.0.1:8000/redoc/`
- Contact backend team

---

**Last Updated:** October 10, 2025  
**API Version:** v1  
**Backend Framework:** Django Rest Framework  
**Authentication:** JWT (JSON Web Tokens)
