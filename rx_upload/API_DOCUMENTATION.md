# RX Upload API Documentation

Complete API documentation for the prescription upload and order flow system.

## Table of Contents
- [Authentication](#authentication)
- [Customer Prescription Flow](#customer-prescription-flow)
- [RX Verifier Endpoints](#rx-verifier-endpoints)
- [Error Handling](#error-handling)

---

## Base URL
```
Production: https://medixmall.com/api/rx-upload/
Development: http://localhost:8000/api/rx-upload/
```

---

## Authentication

All customer endpoints require user authentication with JWT token or session authentication.

### Headers Required
```http
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json (or multipart/form-data for file uploads)
```

---

## Customer Prescription Flow

The prescription order process follows these steps:
1. Upload Prescription File(s)
2. Add Patient Information
3. Select Delivery Address
4. Choose Delivery Option
5. Submit Order

### 1. Upload Prescription

**Endpoint:** `POST /api/rx-upload/customer/upload/`

**Authentication:** Required

**Content-Type:** `multipart/form-data`

**Request:**
```http
POST /api/rx-upload/customer/upload/
Content-Type: multipart/form-data

prescription_file: [FILE] (JPEG, PNG, PDF - Max 10MB)
```

**Success Response (201 Created):**
```json
{
  "success": true,
  "message": "Prescription uploaded successfully",
  "data": {
    "prescription_id": "550e8400-e29b-41d4-a716-446655440000",
    "prescription_number": "RX202501051430450ABCD1234",
    "prescription_image": "https://ik.imagekit.io/medixmall/prescriptions/prescription_550e8400_abc12345.jpg",
    "original_filename": "my_prescription.jpg",
    "file_size": 245678,
    "uploaded_at": "2025-01-05T14:30:45.123456Z"
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "message": "Please upload a prescription file",
  "errors": {
    "prescription_file": ["This field is required."]
  }
}
```

**Validation Rules:**
- File is required
- Max file size: 10MB
- Allowed formats: JPEG, JPG, PNG, GIF, WebP, PDF
- Valid file extension required

---

### 2. Add Patient Information

**Endpoint:** `POST /api/rx-upload/customer/{prescription_id}/patient-info/`

**Authentication:** Required

**Content-Type:** `application/json`

**Request:**
```http
POST /api/rx-upload/customer/550e8400-e29b-41d4-a716-446655440000/patient-info/
Content-Type: application/json

{
  "patient_name": "John Doe",
  "customer_phone": "9876543210",
  "patient_age": 30,
  "patient_gender": "male",
  "emergency_contact": "9123456789",
  "customer_notes": "Need medicine urgently"
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| patient_name | string | Yes | Full name of the patient |
| customer_phone | string | Yes | 10-digit mobile number |
| patient_age | integer | No | Age of patient |
| patient_gender | string | No | "male", "female", or "other" |
| emergency_contact | string | No | Alternative contact number |
| customer_notes | string | No | Additional notes |

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Patient information saved successfully",
  "data": {
    "prescription_id": "550e8400-e29b-41d4-a716-446655440000",
    "patient_name": "John Doe",
    "customer_phone": "9876543210",
    "patient_age": 30,
    "patient_gender": "male",
    "alternative_contact": "9123456789"
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "message": "Phone number is required",
  "errors": {
    "customer_phone": ["This field is required."]
  }
}
```

**Validation Rules:**
- `patient_name`: Required, non-empty string
- `customer_phone`: Required, exactly 10 digits
- `patient_gender`: Must be "male", "female", or "other"
- Prescription must belong to authenticated user

---

### 3. Get Delivery Addresses

**Endpoint:** `GET /api/rx-upload/customer/addresses/`

**Authentication:** Required

**Request:**
```http
GET /api/rx-upload/customer/addresses/
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "type": "home",
      "full_name": "Admin User",
      "phone": "1234567890",
      "address_line_1": "Rohini, Sector 5",
      "address_line_2": "",
      "city": "Purnia",
      "state": "Bihar",
      "postal_code": "854301",
      "country": "India",
      "is_default": true,
      "formatted_address": "Rohini, Sector 5, Purnia, Bihar - 854301"
    },
    {
      "id": 2,
      "type": "office",
      "full_name": "John Doe",
      "phone": "9876543210",
      "address_line_1": "Office Tower, Floor 5",
      "address_line_2": "Business District",
      "city": "Mumbai",
      "state": "Maharashtra",
      "postal_code": "400001",
      "country": "India",
      "is_default": false,
      "formatted_address": "Office Tower, Floor 5, Mumbai, Maharashtra - 400001"
    }
  ]
}
```

**Notes:**
- Returns all active addresses for the authenticated user
- Ordered by default address first, then by creation date
- Empty array returned if user has no addresses

---

### 4. Get Delivery Options

**Endpoint:** `GET /api/rx-upload/customer/delivery-options/`

**Authentication:** Required

**Request:**
```http
GET /api/rx-upload/customer/delivery-options/
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "options": [
      {
        "id": "express",
        "name": "Express Delivery",
        "description": "Get your medicines within 2-4 hours",
        "price": 99.00,
        "estimated_delivery": "2-4 hours",
        "icon": "flash"
      },
      {
        "id": "standard",
        "name": "Standard Delivery",
        "description": "Get your medicines within 24 hours",
        "price": 49.00,
        "estimated_delivery": "24 hours",
        "icon": "truck"
      },
      {
        "id": "free",
        "name": "Free Delivery",
        "description": "Get your medicines within 2-3 days",
        "price": 0.00,
        "estimated_delivery": "2-3 days",
        "icon": "gift"
      }
    ]
  }
}
```

**Delivery Options:**

| Option | Price | Delivery Time | Use Case |
|--------|-------|---------------|----------|
| express | ₹99 | 2-4 hours | Urgent medical needs |
| standard | ₹49 | 24 hours | Regular prescriptions |
| free | ₹0 | 2-3 days | Non-urgent orders |

---

### 5. Submit Prescription Order

**Endpoint:** `POST /api/rx-upload/customer/{prescription_id}/submit/`

**Authentication:** Required

**Content-Type:** `application/json`

**Request:**
```http
POST /api/rx-upload/customer/550e8400-e29b-41d4-a716-446655440000/submit/
Content-Type: application/json

{
  "delivery_address_id": 1,
  "delivery_option": "express",
  "payment_method": "cod",
  "customer_notes": "Please deliver before 6 PM"
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| delivery_address_id | integer | Yes | ID of selected delivery address |
| delivery_option | string | Yes | "express", "standard", or "free" |
| payment_method | string | No | "cod" or "online" (default: "cod") |
| customer_notes | string | No | Additional delivery instructions |

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Prescription order submitted successfully",
  "data": {
    "order_id": "RX202501051430450ABCD1234",
    "prescription_id": "550e8400-e29b-41d4-a716-446655440000",
    "delivery_charge": 99.00,
    "estimated_delivery": "2-4 hours",
    "status": "pending_verification",
    "message": "Your prescription is being verified by our pharmacist. You will be contacted once verification is complete.",
    "contact_info": {
      "phone": "9876543210",
      "email": "customer@example.com"
    }
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "message": "Please select a delivery address",
  "errors": {
    "delivery_address_id": ["This field is required."]
  }
}
```

**Validation Rules:**
- `delivery_address_id`: Must be valid address belonging to user
- `delivery_option`: Must be "express", "standard", or "free"
- Patient information must be completed before submission
- Prescription file must be uploaded

**Order Processing:**
1. Order marked as "pending_verification"
2. Prescription assigned priority based on delivery option
3. Express orders marked as urgent
4. Customer receives confirmation notification
5. RX verifier notified for verification

---

### 6. Get Order Summary

**Endpoint:** `GET /api/rx-upload/customer/{prescription_id}/summary/`

**Authentication:** Required

**Request:**
```http
GET /api/rx-upload/customer/550e8400-e29b-41d4-a716-446655440000/summary/
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "prescription_id": "550e8400-e29b-41d4-a716-446655440000",
    "prescription_number": "RX202501051430450ABCD1234",
    "prescription_files": 1,
    "prescription_image": "https://ik.imagekit.io/medixmall/prescriptions/prescription_550e8400_abc12345.jpg",
    "patient": "John Doe",
    "patient_phone": "9876543210",
    "delivery_address": "Rohini, Sector 5, Purnia, Bihar",
    "verification_status": "pending_verification",
    "can_submit": false,
    "missing_fields": [],
    "uploaded_at": "2025-01-05T14:30:45.123456Z"
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| prescription_files | integer | Number of uploaded files (0 or 1) |
| patient | string | Patient name or "Not specified" |
| delivery_address | string | Formatted address or "Not selected" |
| can_submit | boolean | Whether order can be submitted |
| missing_fields | array | List of incomplete fields |

**Missing Fields Values:**
- `prescription_file`: No file uploaded
- `patient_information`: Patient details incomplete
- `delivery_address`: Delivery address not selected

---

### 7. Get My Prescriptions

**Endpoint:** `GET /api/rx-upload/customer/my-prescriptions/`

**Authentication:** Required

**Request:**
```http
GET /api/rx-upload/customer/my-prescriptions/
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "prescription_id": "550e8400-e29b-41d4-a716-446655440000",
      "prescription_number": "RX202501051430450ABCD1234",
      "patient_name": "John Doe",
      "verification_status": "pending",
      "verification_status_display": "Pending Verification",
      "uploaded_at": "2025-01-05T14:30:45.123456Z",
      "prescription_image": "https://ik.imagekit.io/medixmall/prescriptions/prescription_550e8400_abc12345.jpg",
      "is_urgent": true
    }
  ],
  "count": 1
}
```

**Verification Status Values:**
- `pending`: Waiting for verification
- `in_review`: Being reviewed by pharmacist
- `approved`: Verified and approved
- `rejected`: Not approved
- `clarification_needed`: More information required

---

## RX Verifier Endpoints

### 1. Verifier Login

**Endpoint:** `POST /api/rx-upload/auth/login/`

**Authentication:** Not required

**Request:**
```json
{
  "email": "verifier@medixmall.com",
  "password": "SecurePassword123"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Welcome back, Dr. John Smith!",
  "data": {
    "user": {
      "id": 123,
      "email": "verifier@medixmall.com",
      "full_name": "Dr. John Smith",
      "role": "rx_verifier",
      "last_login": "2025-01-05T14:30:45.123456Z"
    },
    "workload": {
      "pending_count": 15,
      "in_review_count": 5,
      "total_verified": 250,
      "approval_rate": 0.95,
      "is_available": true,
      "can_accept_more": true
    }
  }
}
```

### 2. Get Prescriptions List

**Endpoint:** `GET /api/rx-upload/prescriptions/`

**Authentication:** Required (RX Verifier)

**Query Parameters:**
- `verification_status`: pending, in_review, approved, rejected
- `is_urgent`: true/false
- `search`: Search by patient name, prescription number
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

**Request:**
```http
GET /api/rx-upload/prescriptions/?verification_status=pending&is_urgent=true&page=1
```

**Success Response (200 OK):**
```json
{
  "count": 50,
  "next": "http://localhost:8000/api/rx-upload/prescriptions/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "prescription_number": "RX202501051430450ABCD1234",
      "customer_name": "Jane Doe",
      "customer_email": "jane@example.com",
      "patient_name": "John Doe",
      "patient_age": 30,
      "patient_gender": "male",
      "customer_phone": "9876543210",
      "prescription_image": "https://ik.imagekit.io/medixmall/prescriptions/...",
      "verification_status": "pending",
      "is_urgent": true,
      "priority_level": 3,
      "uploaded_at": "2025-01-05T14:30:45.123456Z",
      "can_be_verified": true
    }
  ]
}
```

### 3. Assign Prescription

**Endpoint:** `POST /api/rx-upload/prescriptions/{prescription_id}/assign/`

**Authentication:** Required (RX Verifier)

**Request:**
```http
POST /api/rx-upload/prescriptions/550e8400-e29b-41d4-a716-446655440000/assign/
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Prescription assigned successfully",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "verification_status": "in_review",
    "verified_by": 123,
    "verified_by_name": "Dr. John Smith"
  }
}
```

### 4. Approve Prescription

**Endpoint:** `POST /api/rx-upload/prescriptions/{prescription_id}/approve/`

**Authentication:** Required (RX Verifier)

**Request:**
```json
{
  "notes": "Prescription verified. All medications are appropriate."
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Prescription approved successfully",
  "data": {
    "verification_status": "approved",
    "verification_date": "2025-01-05T15:00:00.123456Z",
    "verification_notes": "Prescription verified. All medications are appropriate."
  }
}
```

### 5. Reject Prescription

**Endpoint:** `POST /api/rx-upload/prescriptions/{prescription_id}/reject/`

**Authentication:** Required (RX Verifier)

**Request:**
```json
{
  "notes": "Prescription is illegible. Please upload a clearer image."
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Prescription rejected",
  "data": {
    "verification_status": "rejected",
    "verification_date": "2025-01-05T15:00:00.123456Z",
    "verification_notes": "Prescription is illegible. Please upload a clearer image."
  }
}
```

### 6. Verification Dashboard

**Endpoint:** `GET /api/rx-upload/dashboard/`

**Authentication:** Required (RX Verifier/Admin)

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "counts": {
      "pending": 15,
      "in_review": 5,
      "approved": 200,
      "rejected": 10,
      "total": 230
    },
    "recent_activities": [],
    "performance": {
      "total_verified": 250,
      "approval_rate": 0.95,
      "average_processing_time": 15.5
    },
    "system_health": {
      "status": "healthy",
      "active_verifiers": 5
    }
  }
}
```

---

## Error Handling

### Standard Error Response Format

All endpoints return errors in consistent format:

```json
{
  "success": false,
  "message": "Human-readable error message",
  "errors": {
    "field_name": ["Specific error for this field"],
    "another_field": ["Another error message"]
  }
}
```

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET/PUT/PATCH request |
| 201 | Created | Successful POST creating new resource |
| 400 | Bad Request | Validation error or malformed request |
| 401 | Unauthorized | Authentication required or failed |
| 403 | Forbidden | User lacks permission for action |
| 404 | Not Found | Resource doesn't exist |
| 500 | Server Error | Internal server error |

### Common Error Scenarios

#### 1. Authentication Required (401)
```json
{
  "detail": "Authentication credentials were not provided."
}
```

#### 2. Permission Denied (403)
```json
{
  "success": false,
  "message": "You do not have permission to perform this action."
}
```

#### 3. Validation Error (400)
```json
{
  "success": false,
  "message": "Invalid input data",
  "errors": {
    "patient_name": ["This field is required."],
    "customer_phone": ["Enter a valid 10-digit mobile number."]
  }
}
```

#### 4. Resource Not Found (404)
```json
{
  "success": false,
  "message": "Prescription not found"
}
```

---

## Testing Checklist

### Customer Flow Tests
- [ ] Upload prescription with valid file
- [ ] Upload prescription with invalid file (too large, wrong format)
- [ ] Add patient information with all fields
- [ ] Add patient information with only required fields
- [ ] Validate phone number format
- [ ] Get delivery addresses
- [ ] Get delivery options
- [ ] Submit complete order
- [ ] Submit order with missing information
- [ ] Get order summary
- [ ] Get prescription history

### Verifier Flow Tests
- [ ] Login with valid credentials
- [ ] Login with invalid credentials
- [ ] List pending prescriptions
- [ ] Filter prescriptions by status
- [ ] Search prescriptions
- [ ] Assign prescription
- [ ] Approve prescription
- [ ] Reject prescription with notes
- [ ] Request clarification
- [ ] View dashboard statistics

### Edge Cases
- [ ] Upload multiple times to same prescription
- [ ] Submit order without uploading file
- [ ] Submit order without patient info
- [ ] Use invalid address ID
- [ ] Use invalid delivery option
- [ ] Access other user's prescription
- [ ] Assign already assigned prescription
- [ ] Approve already approved prescription

---

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **Authenticated Users:** 1000 requests per hour
- **Upload Endpoints:** 20 uploads per hour
- **Anonymous Users:** 100 requests per hour

Rate limit headers included in response:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1609459200
```

---

## Pagination

List endpoints support pagination:

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

**Response Format:**
```json
{
  "count": 100,
  "next": "http://api.example.com/resource/?page=2",
  "previous": null,
  "results": []
}
```

---

## Support

For API support or questions:
- Email: support@medixmall.com
- Phone: 1800-123-4567
- Documentation: https://medixmall.com/docs
