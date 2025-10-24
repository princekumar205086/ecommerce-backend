# Admin User Management API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Endpoints](#endpoints)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Pagination](#pagination)

---

## Overview

The Admin User Management API provides comprehensive endpoints for managing users in the MedixMall e-commerce platform. This API is designed for enterprise-level user management with features including:

- **User CRUD Operations**: Create, Read, Update, Delete users
- **Role Management**: Change user roles (user, supplier, admin, rx_verifier)
- **Status Management**: Activate/Deactivate user accounts
- **Bulk Operations**: Perform actions on multiple users simultaneously
- **Advanced Filtering**: Filter users by role, status, email verification, date ranges
- **Search**: Search users by email, name, or contact
- **Analytics**: View user statistics and growth metrics
- **Audit Logging**: Track all admin actions for compliance
- **Data Export**: Export user data to CSV

---

## Authentication

All admin endpoints require JWT authentication with admin role.

### Getting an Access Token

**Endpoint:** `POST /api/accounts/login/`

**Request:**
```json
{
  "email": "admin@medixmall.com",
  "password": "your_password"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "admin@medixmall.com",
    "full_name": "Admin User",
    "role": "admin"
  },
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Using the Token

Include the access token in the `Authorization` header for all API requests:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

## Endpoints

### 1. List All Users

Get a paginated list of all users with filtering and search.

**Endpoint:** `GET /api/accounts/admin/users/`

**Authentication:** Required (Admin)

**Query Parameters:**
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `role` | string | Filter by role | `?role=supplier` |
| `is_active` | boolean | Filter by active status | `?is_active=true` |
| `email_verified` | boolean | Filter by email verification | `?email_verified=false` |
| `search` | string | Search by email, name, or contact | `?search=john` |
| `date_joined_from` | date | Filter from date (YYYY-MM-DD) | `?date_joined_from=2024-01-01` |
| `date_joined_to` | date | Filter to date (YYYY-MM-DD) | `?date_joined_to=2024-12-31` |
| `ordering` | string | Order by field | `?ordering=-date_joined` |
| `page` | integer | Page number | `?page=1` |
| `page_size` | integer | Items per page (max 100) | `?page_size=20` |

**Response:**
```json
{
  "count": 150,
  "next": "http://api.medixmall.com/api/accounts/admin/users/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "email": "user@example.com",
      "full_name": "John Doe",
      "contact": "9876543210",
      "role": "user",
      "is_active": true,
      "is_staff": false,
      "is_superuser": false,
      "email_verified": true,
      "date_joined": "2024-01-15T10:30:00Z",
      "last_login_display": "2 days ago",
      "has_address": true,
      "medixmall_mode": false,
      "is_on_duty": true,
      "total_orders": 5,
      "account_age_days": 120
    }
  ]
}
```

**Examples:**

```bash
# Get all active suppliers
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.medixmall.com/api/accounts/admin/users/?role=supplier&is_active=true"

# Search for users by email
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.medixmall.com/api/accounts/admin/users/?search=john@example.com"

# Get users registered in January 2024
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.medixmall.com/api/accounts/admin/users/?date_joined_from=2024-01-01&date_joined_to=2024-01-31"
```

---

### 2. Get User Details

Get detailed information about a specific user.

**Endpoint:** `GET /api/accounts/admin/users/{id}/`

**Authentication:** Required (Admin)

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "contact": "9876543210",
  "role": "user",
  "is_active": true,
  "is_staff": false,
  "is_superuser": false,
  "email_verified": true,
  "date_joined": "2024-01-15T10:30:00Z",
  "last_login": "2024-10-23T14:20:00Z",
  "has_address": true,
  "full_address": "123 Main St, Mumbai, Maharashtra 400001, India",
  "address_line_1": "123 Main St",
  "address_line_2": "Apt 4B",
  "city": "Mumbai",
  "state": "Maharashtra",
  "postal_code": "400001",
  "country": "India",
  "medixmall_mode": false,
  "is_on_duty": true,
  "profile_pic": "https://imagekit.io/profile_pics/user_123.jpg",
  "total_orders": 5,
  "total_spent": 15000.50,
  "recent_orders": [
    {
      "id": 101,
      "order_number": "ORD-2024-101",
      "status": "delivered",
      "total_amount": 3500.00,
      "created_at": "2024-10-20T10:00:00Z"
    }
  ],
  "account_stats": {
    "account_age_days": 120,
    "email_verified": true,
    "total_orders": 5,
    "pending_orders": 1,
    "completed_orders": 4,
    "cancelled_orders": 0,
    "cart_items": 3,
    "wishlist_items": 10
  }
}
```

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.medixmall.com/api/accounts/admin/users/1/"
```

---

### 3. Create User

Create a new user account from admin panel.

**Endpoint:** `POST /api/accounts/admin/users/create/`

**Authentication:** Required (Admin)

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "full_name": "New User",
  "contact": "9876543210",
  "role": "user",
  "password": "securePassword123",
  "password2": "securePassword123",
  "is_active": true,
  "is_staff": false,
  "email_verified": true,
  "send_credentials_email": true
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | User email (unique) |
| `full_name` | string | Yes | Full name |
| `contact` | string | Yes | Contact number |
| `role` | string | Yes | Role: user, supplier, admin, rx_verifier |
| `password` | string | Yes | Password (min 8 chars) |
| `password2` | string | Yes | Password confirmation |
| `is_active` | boolean | No | Active status (default: true) |
| `is_staff` | boolean | No | Staff status (default: false) |
| `email_verified` | boolean | No | Email verified (default: false) |
| `send_credentials_email` | boolean | No | Send credentials email (default: true) |

**Response:**
```json
{
  "message": "User created successfully",
  "user": {
    "id": 151,
    "email": "newuser@example.com",
    "full_name": "New User",
    "contact": "9876543210",
    "role": "user",
    "is_active": true,
    "email_verified": true
  }
}
```

**Example:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "full_name": "New User",
    "contact": "9876543210",
    "role": "user",
    "password": "securePassword123",
    "password2": "securePassword123",
    "email_verified": true,
    "send_credentials_email": false
  }' \
  "https://api.medixmall.com/api/accounts/admin/users/create/"
```

---

### 4. Update User

Update user information.

**Endpoint:** `PATCH /api/accounts/admin/users/{id}/update/`

**Authentication:** Required (Admin)

**Request Body:** (all fields optional for PATCH)
```json
{
  "full_name": "Updated Name",
  "contact": "9876543211",
  "is_active": true,
  "email_verified": true,
  "city": "Mumbai",
  "state": "Maharashtra"
}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "Updated Name",
  "contact": "9876543211",
  "is_active": true,
  "email_verified": true
}
```

**Example:**
```bash
curl -X PATCH \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Updated Name",
    "is_active": true
  }' \
  "https://api.medixmall.com/api/accounts/admin/users/1/update/"
```

---

### 5. Change User Role

Change a user's role.

**Endpoint:** `POST /api/accounts/admin/users/{user_id}/change-role/`

**Authentication:** Required (Admin)

**Request Body:**
```json
{
  "role": "supplier",
  "reason": "User requested to become a supplier"
}
```

**Allowed Roles:**
- `user` - Regular customer
- `supplier` - Product supplier
- `admin` - Administrator
- `rx_verifier` - Prescription verifier

**Response:**
```json
{
  "message": "User role changed to supplier successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "supplier"
  }
}
```

**Example:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "supplier",
    "reason": "Approved supplier application"
  }' \
  "https://api.medixmall.com/api/accounts/admin/users/1/change-role/"
```

---

### 6. Change User Status

Activate or deactivate a user account.

**Endpoint:** `POST /api/accounts/admin/users/{user_id}/change-status/`

**Authentication:** Required (Admin)

**Request Body:**
```json
{
  "is_active": false,
  "reason": "Suspicious activity detected"
}
```

**Response:**
```json
{
  "message": "User account deactivated successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "is_active": false
  }
}
```

**Example:**
```bash
# Deactivate user
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false,
    "reason": "Account suspended for review"
  }' \
  "https://api.medixmall.com/api/accounts/admin/users/1/change-status/"

# Reactivate user
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": true,
    "reason": "Review completed, reinstating account"
  }' \
  "https://api.medixmall.com/api/accounts/admin/users/1/change-status/"
```

---

### 7. Delete User (Soft Delete)

Deactivate a user account (soft delete).

**Endpoint:** `DELETE /api/accounts/admin/users/{id}/delete/`

**Authentication:** Required (Admin)

**Response:**
```json
{
  "message": "User user@example.com has been deactivated"
}
```

**Note:** This is a soft delete - the user is deactivated but not removed from the database.

**Example:**
```bash
curl -X DELETE \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.medixmall.com/api/accounts/admin/users/1/delete/"
```

---

### 8. Bulk User Actions

Perform actions on multiple users simultaneously.

**Endpoint:** `POST /api/accounts/admin/users/bulk-action/`

**Authentication:** Required (Admin)

**Request Body:**
```json
{
  "user_ids": [1, 2, 3, 4, 5],
  "action": "activate",
  "reason": "Mass activation after verification"
}
```

**Supported Actions:**
- `activate` - Activate user accounts
- `deactivate` - Deactivate user accounts
- `verify_email` - Mark emails as verified
- `delete` - Soft delete users

**Response:**
```json
{
  "message": "Bulk action completed. 5 out of 5 users affected.",
  "affected_count": 5,
  "total_count": 5,
  "errors": []
}
```

**Example:**
```bash
# Bulk activate users
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": [1, 2, 3, 4, 5],
    "action": "activate",
    "reason": "Approved after verification"
  }' \
  "https://api.medixmall.com/api/accounts/admin/users/bulk-action/"

# Bulk verify emails
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": [10, 11, 12],
    "action": "verify_email"
  }' \
  "https://api.medixmall.com/api/accounts/admin/users/bulk-action/"
```

---

### 9. User Statistics

Get comprehensive user statistics and analytics.

**Endpoint:** `GET /api/accounts/admin/statistics/`

**Authentication:** Required (Admin)

**Response:**
```json
{
  "total_users": 1500,
  "active_users": 1420,
  "inactive_users": 80,
  "verified_users": 1380,
  "unverified_users": 120,
  "users_by_role": {
    "user": 1200,
    "supplier": 250,
    "admin": 5,
    "rx_verifier": 45
  },
  "new_users_today": 12,
  "new_users_this_week": 85,
  "new_users_this_month": 340,
  "growth_rate": {
    "current_month": 340,
    "previous_month": 280,
    "percentage": 21.43
  }
}
```

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.medixmall.com/api/accounts/admin/statistics/"
```

---

### 10. Audit Logs

View audit logs of all admin actions.

**Endpoint:** `GET /api/accounts/admin/audit-logs/`

**Authentication:** Required (Admin)

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | integer | Filter by user ID |
| `action` | string | Filter by action type |
| `date_from` | date | Filter from date |
| `date_to` | date | Filter to date |
| `success` | boolean | Filter by success status |

**Response:**
```json
{
  "count": 500,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": 1,
      "user_email": "admin@medixmall.com",
      "user_name": "Admin User",
      "action": "role_change",
      "action_display": "Role Changed",
      "resource": "User:5",
      "details": {
        "target_user": "user@example.com",
        "old_role": "user",
        "new_role": "supplier",
        "reason": "Approved supplier application",
        "admin": "admin@medixmall.com"
      },
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "timestamp": "2024-10-25T10:30:00Z",
      "success": true,
      "error_message": null,
      "time_ago": "2 hours ago"
    }
  ]
}
```

**Example:**
```bash
# Get all audit logs
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.medixmall.com/api/accounts/admin/audit-logs/"

# Get role changes
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.medixmall.com/api/accounts/admin/audit-logs/?action=role_change"

# Get today's actions
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.medixmall.com/api/accounts/admin/audit-logs/?date_from=2024-10-25"
```

---

### 11. Export Users to CSV

Export user data to CSV file.

**Endpoint:** `GET /api/accounts/admin/users/export/`

**Authentication:** Required (Admin)

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `role` | string | Filter by role |
| `is_active` | boolean | Filter by active status |

**Response:** CSV file download

**Example:**
```bash
# Export all users
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.medixmall.com/api/accounts/admin/users/export/" \
  -o users_export.csv

# Export only suppliers
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.medixmall.com/api/accounts/admin/users/export/?role=supplier" \
  -o suppliers_export.csv
```

---

### 12. Create RX Verifier

Create a new RX Verifier account with automatic credential email.

**Endpoint:** `POST /api/accounts/admin/rx-verifiers/create/`

**Authentication:** Required (Admin)

**Request Body:**
```json
{
  "email": "rxverifier@medixmall.com",
  "full_name": "Dr. John Smith",
  "contact": "9876543210",
  "password": "securePassword123",
  "password2": "securePassword123",
  "send_credentials_email": true
}
```

**Response:**
```json
{
  "message": "RX Verifier account created successfully. Credentials have been sent via email.",
  "user": {
    "id": 152,
    "email": "rxverifier@medixmall.com",
    "full_name": "Dr. John Smith",
    "role": "rx_verifier",
    "email_verified": true
  }
}
```

**Example:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "rxverifier@medixmall.com",
    "full_name": "Dr. John Smith",
    "contact": "9876543210",
    "password": "securePassword123",
    "password2": "securePassword123",
    "send_credentials_email": true
  }' \
  "https://api.medixmall.com/api/accounts/admin/rx-verifiers/create/"
```

---

### 13. Search Users

Advanced search for users.

**Endpoint:** `GET /api/accounts/admin/users/search/`

**Authentication:** Required (Admin)

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Search query |

**Response:**
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "email": "john@example.com",
      "full_name": "John Doe",
      "role": "user"
    }
  ]
}
```

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.medixmall.com/api/accounts/admin/users/search/?q=john"
```

---

## Error Handling

All endpoints return consistent error responses:

### Error Response Format

```json
{
  "error": "Error message describing what went wrong",
  "details": {
    "field_name": ["Specific error for this field"]
  }
}
```

### HTTP Status Codes

| Status Code | Meaning |
|-------------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing or invalid token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error |

### Common Error Examples

**401 Unauthorized:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden:**
```json
{
  "detail": "Admin access required."
}
```

**400 Bad Request:**
```json
{
  "email": ["This field is required."],
  "password": ["Passwords don't match."]
}
```

---

## Rate Limiting

To prevent abuse, the API implements rate limiting:

- **Rate Limit:** 1000 requests per hour per user
- **Headers:** Rate limit info is included in response headers:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Time when limit resets (Unix timestamp)

**Example Response Headers:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1698249600
```

---

## Pagination

List endpoints return paginated results:

### Default Pagination
- **Default Page Size:** 20 items
- **Maximum Page Size:** 100 items

### Pagination Parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `page` | Page number | `?page=2` |
| `page_size` | Items per page | `?page_size=50` |

### Pagination Response
```json
{
  "count": 150,
  "next": "https://api.medixmall.com/api/accounts/admin/users/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## Complete API Endpoint Summary

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/accounts/admin/users/` | List all users | Admin |
| GET | `/api/accounts/admin/users/{id}/` | Get user details | Admin |
| POST | `/api/accounts/admin/users/create/` | Create user | Admin |
| PATCH | `/api/accounts/admin/users/{id}/update/` | Update user | Admin |
| DELETE | `/api/accounts/admin/users/{id}/delete/` | Delete user | Admin |
| POST | `/api/accounts/admin/users/{user_id}/change-role/` | Change user role | Admin |
| POST | `/api/accounts/admin/users/{user_id}/change-status/` | Change user status | Admin |
| POST | `/api/accounts/admin/users/bulk-action/` | Bulk user actions | Admin |
| GET | `/api/accounts/admin/users/search/` | Search users | Admin |
| GET | `/api/accounts/admin/users/export/` | Export users CSV | Admin |
| POST | `/api/accounts/admin/rx-verifiers/create/` | Create RX verifier | Admin |
| GET | `/api/accounts/admin/statistics/` | User statistics | Admin |
| GET | `/api/accounts/admin/audit-logs/` | Audit logs | Admin |

---

## Best Practices

1. **Always use HTTPS** in production
2. **Store tokens securely** (never in localStorage, use httpOnly cookies or secure storage)
3. **Implement proper error handling** in your frontend
4. **Use pagination** for large datasets
5. **Log all admin actions** for audit trail
6. **Validate input** on both frontend and backend
7. **Handle rate limiting** gracefully
8. **Refresh tokens** before expiration

---

## Need Help?

For support or questions:
- **Email:** support@medixmall.com
- **Documentation:** https://docs.medixmall.com
- **API Status:** https://status.medixmall.com
