# Coupon Management System - API Documentation

## Overview

The Coupon Management System provides comprehensive coupon functionality with role-based access control, supporting both admin management and user consumption of coupons. The system is designed for enterprise-level e-commerce applications with features like bulk operations, analytics, and audit trails.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Authentication & Permissions](#authentication--permissions)
3. [Admin Endpoints](#admin-endpoints)
4. [User Endpoints](#user-endpoints)
5. [Application Endpoints](#application-endpoints)
6. [Public Endpoints](#public-endpoints)
7. [Data Models](#data-models)
8. [Response Formats](#response-formats)
9. [Error Handling](#error-handling)
10. [Testing Guide](#testing-guide)

## System Architecture

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Admin Views   │    │   User Views    │    │ Application     │
│                 │    │                 │    │ Views           │
│ - CRUD          │    │ - View Only     │    │ - Validation    │
│ - Analytics     │    │ - Assigned      │    │ - Application   │
│ - Bulk Ops      │    │ - Public        │    │ - Usage Tracking│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Core Models   │
                    │                 │
                    │ - Coupon        │
                    │ - CouponUsage   │
                    │ - User          │
                    └─────────────────┘
```

### Key Features

- **Role-Based Access Control**: Admin-only CRUD, User view/apply permissions
- **Flexible Discount Types**: Percentage and fixed amount discounts
- **User Assignment**: Public coupons or user-specific assignments
- **Usage Tracking**: Complete audit trail of coupon usage
- **Enterprise Features**: Bulk operations, analytics, reporting
- **Validation**: Comprehensive validation at model, serializer, and view levels

## Authentication & Permissions

### User Roles

| Role | Access Level | Permissions |
|------|--------------|-------------|
| `admin` | Full Access | Create, Read, Update, Delete all coupons; View all usage |
| `user` | Limited Access | View assigned/public coupons; Apply coupons; View own usage |
| `supplier` | No Access | Cannot access coupon system |
| `rx_verifier` | No Access | Cannot access coupon system |

### Authentication Methods

All endpoints require authentication except public promotional endpoints:

```http
Authorization: Bearer <jwt_token>
```

### Permission Classes Used

- `IsAdmin`: Admin-only access
- `IsAuthenticated`: Requires valid authentication
- `AllowAny`: Public access (promotional endpoints only)

## Admin Endpoints

### Base URL: `/api/coupons/admin/`

Admin endpoints provide complete coupon management capabilities with advanced features.

---

#### 1. List All Coupons

**GET** `/api/coupons/admin/`

List all coupons with filtering, searching, and pagination.

**Query Parameters:**
- `coupon_type`: Filter by type (`percentage`, `fixed_amount`)
- `is_active`: Filter by status (`true`, `false`)
- `applicable_to`: Filter by applicability (`all`, `pathology`, `doctor`, `medical`)
- `assigned_to_all`: Filter by assignment (`true`, `false`)
- `valid`: Filter by validity (`true`, `false`, `expired`, `future`)
- `usage_status`: Filter by usage (`unused`, `partially_used`, `fully_used`)
- `search`: Search in code and description
- `ordering`: Sort by fields (`-created_at`, `valid_to`, `used_count`, etc.)
- `created_from`: Filter by creation date (YYYY-MM-DD)
- `created_to`: Filter by creation date (YYYY-MM-DD)

**Response Example:**
```json
{
  "count": 25,
  "next": "http://api/coupons/admin/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "code": "WELCOME20",
      "description": "Welcome discount for new users",
      "coupon_type": "percentage",
      "discount_value": "20.00",
      "max_discount": "100.00",
      "min_order_amount": "200.00",
      "applicable_to": "all",
      "valid_from": "2024-01-01T00:00:00Z",
      "valid_to": "2024-12-31T23:59:59Z",
      "max_uses": 1000,
      "used_count": 245,
      "is_active": true,
      "assigned_to_all": true,
      "assigned_users": [],
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "created_by_info": {
        "id": 1,
        "email": "admin@medixmall.com",
        "full_name": "System Admin",
        "role": "admin"
      },
      "usage_stats": {
        "total_uses": 245,
        "max_uses": 1000,
        "usage_percentage": 24.5,
        "remaining_uses": 755
      },
      "remaining_uses": 755,
      "is_expired": false
    }
  ]
}
```

---

#### 2. Create New Coupon

**POST** `/api/coupons/admin/`

Create a new coupon with comprehensive validation.

**Request Body:**
```json
{
  "code": "NEWCOUPON20",
  "description": "New promotional coupon",
  "coupon_type": "percentage",
  "discount_value": "20.00",
  "max_discount": "150.00",
  "min_order_amount": "300.00",
  "applicable_to": "all",
  "valid_from": "2024-02-01T00:00:00Z",
  "valid_to": "2024-02-29T23:59:59Z",
  "max_uses": 500,
  "is_active": true,
  "assigned_to_all": false,
  "assigned_user_ids": [12, 34, 56]
}
```

**Response (201 Created):**
```json
{
  "id": 2,
  "code": "NEWCOUPON20",
  "description": "New promotional coupon",
  "coupon_type": "percentage",
  "discount_value": "20.00",
  "max_discount": "150.00",
  "min_order_amount": "300.00",
  "applicable_to": "all",
  "valid_from": "2024-02-01T00:00:00Z",
  "valid_to": "2024-02-29T23:59:59Z",
  "max_uses": 500,
  "used_count": 0,
  "is_active": true,
  "assigned_to_all": false,
  "assigned_users": [
    {
      "id": 12,
      "email": "user1@example.com",
      "full_name": "User One",
      "role": "user"
    }
  ],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "usage_stats": {
    "total_uses": 0,
    "max_uses": 500,
    "usage_percentage": 0,
    "remaining_uses": 500
  },
  "remaining_uses": 500,
  "is_expired": false
}
```

---

#### 3. Get Coupon Details

**GET** `/api/coupons/admin/{id}/`

Retrieve detailed information about a specific coupon.

**Response Example:**
```json
{
  "id": 1,
  "code": "DETAILED_VIEW",
  "description": "Detailed coupon information",
  "coupon_type": "fixed_amount",
  "discount_value": "50.00",
  "max_discount": null,
  "min_order_amount": "200.00",
  "applicable_to": "medical",
  "valid_from": "2024-01-01T00:00:00Z",
  "valid_to": "2024-06-30T23:59:59Z",
  "max_uses": 100,
  "used_count": 25,
  "is_active": true,
  "assigned_to_all": true,
  "assigned_users": [],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-10T15:45:00Z",
  "created_by_info": {
    "id": 1,
    "email": "admin@medixmall.com",
    "full_name": "System Admin",
    "role": "admin"
  },
  "usage_stats": {
    "total_uses": 25,
    "max_uses": 100,
    "usage_percentage": 25.0,
    "remaining_uses": 75
  },
  "remaining_uses": 75,
  "is_expired": false
}
```

---

#### 4. Update Coupon

**PUT/PATCH** `/api/coupons/admin/{id}/`

Update an existing coupon. Use PATCH for partial updates.

**Request Body (PATCH Example):**
```json
{
  "description": "Updated coupon description",
  "discount_value": "25.00",
  "is_active": false
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "code": "UPDATED_COUPON",
  "description": "Updated coupon description",
  "discount_value": "25.00",
  "is_active": false,
  // ... other fields
}
```

---

#### 5. Delete Coupon

**DELETE** `/api/coupons/admin/{id}/`

Delete a coupon. If the coupon has been used, it will be deactivated instead of deleted.

**Response:**
- **204 No Content**: Successfully deleted (unused coupon)
- **204 No Content**: Successfully deactivated (used coupon)

---

#### 6. Bulk Create Coupons

**POST** `/api/coupons/admin/bulk_create/`

Create multiple coupons with sequential codes.

**Request Body:**
```json
{
  "base_code": "BULK2024",
  "quantity": 10,
  "coupon_type": "percentage",
  "discount_value": "15.00",
  "max_discount": "100.00",
  "min_order_amount": "250.00",
  "applicable_to": "all",
  "valid_from": "2024-03-01T00:00:00Z",
  "valid_to": "2024-03-31T23:59:59Z",
  "max_uses": 1,
  "assigned_to_all": true
}
```

**Response (201 Created):**
```json
{
  "message": "Successfully created 10 coupons",
  "coupons": [
    {
      "id": 10,
      "code": "BULK2024001",
      "discount_value": "15.00",
      // ... other fields
    },
    {
      "id": 11,
      "code": "BULK2024002",
      "discount_value": "15.00",
      // ... other fields
    }
    // ... 8 more coupons
  ]
}
```

---

#### 7. Coupon Analytics

**GET** `/api/coupons/admin/analytics/`

Get comprehensive analytics and statistics about coupon performance.

**Response Example:**
```json
{
  "overview": {
    "total_coupons": 150,
    "active_coupons": 120,
    "expired_coupons": 25,
    "usage_rate": 45.2
  },
  "financial": {
    "total_discount_given": "12450.75",
    "average_discount_per_usage": "25.50"
  },
  "top_performers": [
    {
      "id": 1,
      "code": "BESTSELLER",
      "usage_count": 245,
      "total_discount": "4900.00"
    }
  ],
  "type_distribution": [
    {
      "coupon_type": "percentage",
      "count": 95
    },
    {
      "coupon_type": "fixed_amount",
      "count": 55
    }
  ]
}
```

---

#### 8. Coupon Usage History

**GET** `/api/coupons/admin/{id}/usage_history/`

Get detailed usage history for a specific coupon.

**Response Example:**
```json
{
  "coupon_code": "HISTORY_TEST",
  "total_usages": 15,
  "usages": [
    {
      "id": 1,
      "coupon": 1,
      "coupon_info": {
        "code": "HISTORY_TEST",
        "type": "Percentage",
        "discount_value": "20.00",
        "description": "Test coupon"
      },
      "user": 12,
      "user_info": {
        "id": 12,
        "email": "user@example.com",
        "full_name": "Test User",
        "role": "user"
      },
      "order_id": "ORDER123456",
      "discount_amount": "45.00",
      "applied_at": "2024-01-15T14:30:00Z"
    }
  ]
}
```

---

#### 9. Toggle Coupon Status

**POST** `/api/coupons/admin/{id}/toggle_status/`

Toggle the active/inactive status of a coupon.

**Response (200 OK):**
```json
{
  "message": "Coupon TESTCODE activated",
  "coupon": {
    "id": 1,
    "code": "TESTCODE",
    "is_active": true,
    // ... other fields
  }
}
```

---

#### 10. List All Coupon Usages

**GET** `/api/coupons/admin/usages/`

List all coupon usage records across the system.

**Query Parameters:**
- `coupon`: Filter by coupon ID
- `user`: Filter by user ID
- `coupon__coupon_type`: Filter by coupon type
- `date_from`: Filter by usage date (YYYY-MM-DD)
- `date_to`: Filter by usage date (YYYY-MM-DD)
- `search`: Search in coupon code, user email, or order ID
- `ordering`: Sort by fields (`-applied_at`, `discount_amount`)

**Response Example:**
```json
{
  "count": 500,
  "next": "http://api/coupons/admin/usages/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "coupon": 1,
      "coupon_info": {
        "code": "WELCOME20",
        "type": "Percentage",
        "discount_value": "20.00",
        "description": "Welcome discount"
      },
      "user": 15,
      "user_info": {
        "id": 15,
        "email": "customer@example.com",
        "full_name": "Customer Name",
        "role": "user"
      },
      "order_id": "ORD789012",
      "discount_amount": "40.00",
      "applied_at": "2024-01-15T16:45:00Z"
    }
  ]
}
```

## User Endpoints

### Base URL: `/api/coupons/`

User endpoints allow authenticated users to view and manage their available coupons.

---

#### 1. List User's Available Coupons

**GET** `/api/coupons/my-coupons/`

List coupons available to the authenticated user (both assigned and public).

**Query Parameters:**
- `coupon_type`: Filter by type (`percentage`, `fixed_amount`)
- `applicable_to`: Filter by applicability (`all`, `pathology`, `doctor`, `medical`)
- `available_only`: Show only usable coupons (`true`, `false`) - default: `true`
- `search`: Search in code and description
- `ordering`: Sort by fields (`valid_to`, `discount_value`)

**Response Example:**
```json
{
  "count": 8,
  "available_coupons": [
    {
      "id": 1,
      "code": "WELCOME10",
      "description": "Welcome discount for new users",
      "coupon_type": "percentage",
      "discount_value": "10.00",
      "max_discount": "50.00",
      "min_order_amount": "100.00",
      "applicable_to": "all",
      "valid_from": "2024-01-01T00:00:00Z",
      "valid_to": "2024-12-31T23:59:59Z",
      "discount_display": "10% off (max ₹50.00)",
      "validity_status": {
        "is_valid": true,
        "message": "Valid coupon",
        "is_active": true,
        "is_expired": false,
        "is_future": false,
        "days_until_expiry": 180
      },
      "can_use": true,
      "usage_info": {
        "remaining_uses": 755,
        "is_unlimited": false,
        "usage_percentage": 24.5
      }
    }
  ],
  "summary": {
    "total_available": 8,
    "expiring_soon": 2,
    "percentage_coupons": 5,
    "fixed_amount_coupons": 3
  }
}
```

---

#### 2. Get Coupon Details

**GET** `/api/coupons/my-coupons/{id}/`

Get detailed information about a specific coupon available to the user.

**Response Example:**
```json
{
  "id": 1,
  "code": "DETAILED_USER",
  "description": "User accessible coupon details",
  "coupon_type": "fixed_amount",
  "discount_value": "75.00",
  "max_discount": null,
  "min_order_amount": "300.00",
  "applicable_to": "medical",
  "valid_from": "2024-01-01T00:00:00Z",
  "valid_to": "2024-06-30T23:59:59Z",
  "discount_display": "₹75.00 off",
  "validity_status": {
    "is_valid": true,
    "message": "Valid coupon",
    "is_active": true,
    "is_expired": false,
    "is_future": false,
    "days_until_expiry": 95
  },
  "can_use": true,
  "usage_info": {
    "remaining_uses": 8,
    "is_unlimited": false,
    "usage_percentage": 20.0
  }
}
```

---

#### 3. User's Coupon Usage History

**GET** `/api/coupons/my-usage/`

List the authenticated user's coupon usage history.

**Query Parameters:**
- `coupon__coupon_type`: Filter by coupon type
- `ordering`: Sort by fields (`-applied_at`)

**Response Example:**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "coupon_code": "SAVE20",
      "coupon_description": "Save 20% on medical products",
      "order_id": "ORD456789",
      "discount_amount": "80.00",
      "applied_at": "2024-01-10T14:30:00Z"
    },
    {
      "id": 2,
      "coupon_code": "FIXED50",
      "coupon_description": "Fixed 50 rupees off",
      "order_id": "ORD123456",
      "discount_amount": "50.00",
      "applied_at": "2024-01-05T09:15:00Z"
    }
  ]
}
```

## Application Endpoints

### Base URL: `/api/coupons/`

Application endpoints handle coupon validation, application, and usage recording.

---

#### 1. Validate Coupon

**POST** `/api/coupons/validate/`

Validate a coupon without applying it. Useful for showing discount preview.

**Request Body:**
```json
{
  "code": "VALIDATE_ME",
  "cart_total": "500.00"
}
```

**Response (200 OK):**
```json
{
  "coupon_code": "VALIDATE_ME",
  "is_valid": true,
  "message": "Valid coupon",
  "coupon_details": {
    "description": "Validation test coupon",
    "coupon_type": "Percentage",
    "discount_value": "15.00",
    "min_order_amount": "200.00",
    "applicable_to": "All Products",
    "valid_until": "2024-06-30T23:59:59Z",
    "max_discount": "100.00"
  },
  "preview": {
    "cart_total": "500.00",
    "discount_amount": "75.00",
    "final_total": "425.00",
    "savings_percentage": 15.0
  }
}
```

**Error Response (200 OK - Invalid Coupon):**
```json
{
  "coupon_code": "INVALID_CODE",
  "is_valid": false,
  "message": "Coupon has expired",
  "coupon_details": {
    "description": "Expired coupon",
    "coupon_type": "Percentage",
    "discount_value": "20.00",
    "min_order_amount": "100.00",
    "applicable_to": "All Products",
    "valid_until": "2023-12-31T23:59:59Z",
    "max_discount": null
  }
}
```

---

#### 2. Apply Coupon

**POST** `/api/coupons/apply/`

Apply a coupon to calculate final discount amount. This does not record usage.

**Request Body:**
```json
{
  "code": "APPLY_NOW",
  "cart_total": "750.00",
  "applicable_products": ["medicine", "pathology"]
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Coupon applied successfully",
  "coupon_code": "APPLY_NOW",
  "coupon_description": "Special discount for medical products",
  "discount_amount": "112.50",
  "discount_type": "Percentage",
  "original_total": "750.00",
  "new_total": "637.50",
  "savings_percentage": 15.0,
  "applicable_to": "All Products",
  "coupon_details": {
    "id": 5,
    "min_order_amount": "300.00",
    "max_discount": "150.00",
    "valid_until": "2024-08-31T23:59:59Z",
    "remaining_uses": 45
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "message": "Minimum order amount not met (₹300.00 required)",
  "error": null
}
```

---

#### 3. Record Coupon Usage

**POST** `/api/coupons/record-usage/`

Record actual coupon usage after successful order completion. This is typically called by the order processing system.

**Request Body:**
```json
{
  "coupon_code": "USED_COUPON",
  "order_id": "ORD987654",
  "discount_amount": "85.00"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Coupon usage recorded successfully",
  "coupon_code": "USED_COUPON",
  "remaining_uses": 24
}
```

**Error Response (400 Bad Request - Usage Limit Reached):**
```json
{
  "error": "Coupon usage limit reached"
}
```

**Error Response (400 Bad Request - Duplicate Order):**
```json
{
  "error": "This coupon has already been used for this order"
}
```

## Public Endpoints

### Base URL: `/api/coupons/public/`

Public endpoints provide promotional coupon information without requiring authentication.

---

#### 1. List Public Promotional Coupons

**GET** `/api/coupons/public/`

List currently valid public coupons for promotional purposes.

**Query Parameters:**
- `coupon_type`: Filter by type (`percentage`, `fixed_amount`)
- `applicable_to`: Filter by applicability (`all`, `pathology`, `doctor`, `medical`)
- `ordering`: Sort by fields (`valid_to`, `discount_value`)

**Response Example:**
```json
{
  "count": 3,
  "promotional_coupons": [
    {
      "code": "PUBLIC20",
      "description": "Public discount for all users",
      "discount_display": "20% off (max ₹200.00)",
      "min_order_amount": "500.00",
      "applicable_to": "All Products",
      "valid_until": "2024-03-31T23:59:59Z",
      "days_remaining": 45
    },
    {
      "code": "FIXED100",
      "description": "Fixed discount for medical products",
      "discount_display": "₹100.00 off",
      "min_order_amount": "800.00",
      "applicable_to": "Medical Products Only",
      "valid_until": "2024-02-29T23:59:59Z",
      "days_remaining": 15
    }
  ]
}
```

## Data Models

### Coupon Model

```python
class Coupon(models.Model):
    # Core Fields
    code = CharField(max_length=50, unique=True)
    description = TextField(blank=True)
    
    # Discount Configuration
    coupon_type = CharField(choices=[('percentage', 'Percentage'), ('fixed_amount', 'Fixed Amount')])
    discount_value = DecimalField(max_digits=10, decimal_places=2)
    max_discount = DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_order_amount = DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Applicability
    applicable_to = CharField(choices=[('all', 'All Products'), ('pathology', 'Pathology Products Only'), ('doctor', 'Doctor Products Only'), ('medical', 'Medical Products Only')])
    
    # Validity Period
    valid_from = DateTimeField(default=timezone.now)
    valid_to = DateTimeField()
    
    # Usage Tracking
    max_uses = PositiveIntegerField(default=1)
    used_count = PositiveIntegerField(default=0, editable=False)
    is_active = BooleanField(default=True)
    
    # User Assignment
    assigned_to_all = BooleanField(default=True)
    assigned_users = ManyToManyField(User, blank=True, related_name='assigned_coupons')
    
    # Metadata
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    created_by = ForeignKey(User, on_delete=PROTECT, related_name='created_coupons')
```

### CouponUsage Model

```python
class CouponUsage(models.Model):
    coupon = ForeignKey(Coupon, on_delete=CASCADE, related_name='usages')
    user = ForeignKey(User, on_delete=CASCADE, related_name='coupon_usages')
    order_id = CharField(max_length=100, blank=True, null=True, db_index=True)
    discount_amount = DecimalField(max_digits=10, decimal_places=2)
    applied_at = DateTimeField(auto_now_add=True)
```

## Response Formats

### Success Response Structure

```json
{
  "success": true,
  "data": {
    // Response data
  },
  "message": "Operation completed successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Response Structure

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field_name": ["Error message for this field"]
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Pagination Format

```json
{
  "count": 150,
  "next": "http://api/endpoint/?page=3",
  "previous": "http://api/endpoint/?page=1",
  "results": [
    // Paginated results
  ]
}
```

## Error Handling

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource |
| 500 | Internal Server Error | Server error |

### Common Error Scenarios

#### 1. Validation Errors (400)

```json
{
  "field_name": ["Error message"],
  "non_field_errors": ["General validation error"]
}
```

#### 2. Authentication Errors (401)

```json
{
  "detail": "Authentication credentials were not provided."
}
```

#### 3. Permission Errors (403)

```json
{
  "detail": "You do not have permission to perform this action."
}
```

#### 4. Not Found Errors (404)

```json
{
  "detail": "Not found."
}
```

#### 5. Coupon-Specific Errors

```json
{
  "error": "Coupon has expired",
  "code": "COUPON_EXPIRED"
}
```

```json
{
  "error": "Minimum order amount not met (₹500.00 required)",
  "code": "INSUFFICIENT_CART_AMOUNT"
}
```

```json
{
  "error": "Coupon usage limit reached",
  "code": "USAGE_LIMIT_EXCEEDED"
}
```

## Testing Guide

### Running Tests

```bash
# Run all coupon tests
python manage.py test coupon

# Run specific test modules
python manage.py test coupon.tests.test_models
python manage.py test coupon.tests.test_admin_views
python manage.py test coupon.tests.test_user_views
python manage.py test coupon.tests.test_application_views
python manage.py test coupon.tests.test_serializers

# Run with coverage
coverage run --source='coupon' manage.py test coupon
coverage report
coverage html
```

### Test Categories

1. **Model Tests** (`test_models.py`)
   - Coupon creation and validation
   - Discount calculation
   - Usage recording
   - Business logic validation

2. **Admin View Tests** (`test_admin_views.py`)
   - CRUD operations
   - Permission enforcement
   - Bulk operations
   - Analytics endpoints

3. **User View Tests** (`test_user_views.py`)
   - Coupon listing for users
   - Assignment validation
   - Usage history

4. **Application Tests** (`test_application_views.py`)
   - Coupon validation
   - Application logic
   - Usage recording

5. **Serializer Tests** (`test_serializers.py`)
   - Data validation
   - Serialization/deserialization
   - Business rule enforcement

### Sample Test Commands

```bash
# Test admin coupon creation
curl -X POST http://localhost:8000/api/coupons/admin/ \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "TEST20",
    "coupon_type": "percentage",
    "discount_value": "20.00",
    "valid_from": "2024-01-01T00:00:00Z",
    "valid_to": "2024-12-31T23:59:59Z"
  }'

# Test user coupon listing
curl -X GET http://localhost:8000/api/coupons/my-coupons/ \
  -H "Authorization: Bearer <user_token>"

# Test coupon validation
curl -X POST http://localhost:8000/api/coupons/validate/ \
  -H "Authorization: Bearer <user_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "TEST20",
    "cart_total": "500.00"
  }'
```

## Performance Considerations

1. **Database Optimization**
   - Proper indexing on frequently queried fields
   - Query optimization using select_related and prefetch_related
   - Pagination for large datasets

2. **Caching Strategy**
   - Cache frequently accessed coupons
   - Redis for session-based coupon applications
   - Cache invalidation on coupon updates

3. **Security Measures**
   - Rate limiting on coupon validation endpoints
   - Input sanitization and validation
   - Audit logging for admin operations

4. **Scalability**
   - Asynchronous processing for bulk operations
   - Database connection pooling
   - Load balancing for high traffic

## Integration Examples

### Frontend Integration

```javascript
// Validate coupon before checkout
const validateCoupon = async (code, cartTotal) => {
  const response = await fetch('/api/coupons/validate/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      code: code,
      cart_total: cartTotal
    })
  });
  
  return response.json();
};

// Apply coupon during checkout
const applyCoupon = async (code, cartTotal) => {
  const response = await fetch('/api/coupons/apply/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      code: code,
      cart_total: cartTotal
    })
  });
  
  return response.json();
};
```

### Order Processing Integration

```python
# Record coupon usage after successful order
def process_order_with_coupon(order_data, coupon_code):
    # Process order
    order = create_order(order_data)
    
    if order.is_successful and coupon_code:
        # Record coupon usage
        record_usage_response = requests.post(
            f'{API_BASE}/coupons/record-usage/',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'coupon_code': coupon_code,
                'order_id': order.id,
                'discount_amount': str(order.discount_amount)
            }
        )
        
        if not record_usage_response.ok:
            logger.error(f"Failed to record coupon usage: {record_usage_response.text}")
    
    return order
```

---

This documentation provides a comprehensive guide for implementing and using the Coupon Management System. For additional support or clarification, please refer to the test files or contact the development team.