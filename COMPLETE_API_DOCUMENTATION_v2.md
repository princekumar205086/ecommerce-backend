# 🏥 Complete MedixMall Mode, Enterprise Search & ShipRocket API Documentation

## 📋 Table of Contents
1. [MedixMall Mode API](#medixmall-mode-api)
2. [Enterprise Search API](#enterprise-search-api)
3. [ShipRocket Integration API](#shiprocket-integration-api)
4. [Order Management API](#order-management-api)
5. [Authentication & Authorization](#authentication--authorization)
6. [Error Handling](#error-handling)
7. [Testing Guide](#testing-guide)

---

## 🏥 MedixMall Mode API

### Overview
MedixMall mode allows users to toggle between viewing all ecommerce products vs. only medicine products. This transforms the platform into a specialized medical marketplace.

### Endpoints

#### Get MedixMall Mode Status
```http
GET /api/accounts/medixmall-mode/
```

**Description**: Get current MedixMall mode status for the user

**Authentication**: Optional (works for both authenticated and anonymous users)

**Response Headers**:
- `X-MedixMall-Mode`: `true` or `false`

**Response Example**:
```json
{
  "medixmall_mode": false,
  "user_type": "anonymous",
  "storage_type": "session",
  "message": "MedixMall mode status retrieved successfully"
}
```

#### Toggle MedixMall Mode
```http
PUT /api/accounts/medixmall-mode/
```

**Description**: Enable or disable MedixMall mode

**Authentication**: Optional (works for both authenticated and anonymous users)

**Request Body**:
```json
{
  "medixmall_mode": true
}
```

**Response Example**:
```json
{
  "medixmall_mode": true,
  "user_type": "authenticated",
  "storage_type": "database",
  "message": "MedixMall mode enabled successfully. You will now only see medicine products."
}
```

**Storage Behavior**:
- **Authenticated Users**: Saved to user profile (persistent)
- **Anonymous Users**: Saved to session (temporary)

---

## 🔍 Enterprise Search API

### Overview
Advanced product search with intelligent filtering, fuzzy matching, and enterprise-level features.

### Main Search Endpoint
```http
GET /api/public/products/search/
```

**Description**: Comprehensive product search with multiple parameters and intelligent filtering

**Authentication**: Optional (MedixMall mode filtering applies if authenticated)

### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `q` | string | Search query (supports multi-word and fuzzy matching) | `paracetamol tablet` |
| `category` | string/int | Category name or ID | `medicines` or `5` |
| `brand` | string/int | Brand name or ID | `pfizer` or `12` |
| `product_type` | string | Product type filter | `medicine`, `equipment`, `pathology` |
| `min_price` | decimal | Minimum price | `10.00` |
| `max_price` | decimal | Maximum price | `500.00` |
| `sort_by` | string | Sorting option | `relevance`, `price_low`, `price_high`, `name_asc`, `name_desc`, `newest`, `oldest`, `popularity`, `rating` |
| `prescription_required` | boolean | Medicine-specific filter | `true`, `false` |
| `form` | string | Medicine form | `tablet`, `syrup`, `capsule`, `injection` |
| `in_stock_only` | boolean | Show only available products | `true`, `false` |
| `page` | int | Page number (pagination) | `1`, `2`, `3` |
| `page_size` | int | Items per page (max 50) | `10`, `20`, `50` |

### Response Example
```json
{
  "count": 156,
  "next": "http://127.0.0.1:8000/api/public/products/search/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Paracetamol 500mg",
      "description": "Pain relief and fever reducer",
      "price": "15.00",
      "product_type": "medicine",
      "brand": {
        "id": 5,
        "name": "Generic Pharma"
      },
      "category": {
        "id": 2,
        "name": "Pain Relief"
      },
      "form": "tablet",
      "prescription_required": false,
      "stock": 100,
      "images": [
        {
          "image": "https://ik.imagekit.io/company/product1.jpg",
          "alt_text": "Paracetamol 500mg"
        }
      ]
    }
  ],
  "filters": {
    "categories": [
      {"id": 2, "name": "Pain Relief", "count": 45},
      {"id": 3, "name": "Antibiotics", "count": 23}
    ],
    "brands": [
      {"id": 5, "name": "Generic Pharma", "count": 67},
      {"id": 8, "name": "MediCorp", "count": 34}
    ],
    "product_types": [
      {"type": "medicine", "count": 145},
      {"type": "equipment", "count": 11}
    ],
    "price_range": {
      "min": 5.00,
      "max": 2500.00
    },
    "forms": [
      {"form": "tablet", "count": 89},
      {"form": "syrup", "count": 34}
    ]
  },
  "search_suggestions": [
    "paracetamol 650mg",
    "paracetamol syrup",
    "paracetamol injection"
  ],
  "medixmall_mode": true,
  "search_query": "paracetamol",
  "applied_filters": {
    "product_type": "medicine",
    "price_range": "10-500"
  }
}
```

### Search Features

#### 1. Intelligent Multi-field Search
- **Name**: Product name matching
- **Description**: Content search
- **Brand**: Brand name matching
- **Category**: Category name matching
- **Composition**: Medicine composition (for medicines)
- **Manufacturer**: Manufacturer information

#### 2. Fuzzy Matching
- Handles typos and variations
- Partial word matching
- Synonym support

#### 3. Search Suggestions
- Auto-generated based on catalog
- Context-aware suggestions
- Popular search terms

#### 4. Dynamic Filtering
- Filter options based on search results
- Real-time filter counts
- Cascading filters

---

## 🚀 ShipRocket Integration API

### Overview
Complete shipping solution with order creation, tracking, and rate calculation using ShipRocket's API.

### Configuration
Update `shiprocket_config.py` with your credentials:
```python
SHIPROCKET_EMAIL = "your-uat-email@example.com"
SHIPROCKET_PASSWORD = "your-uat-password"
SHIPROCKET_UAT = True  # Set to False for production
```

### Endpoints

#### Test Connection
```http
GET /api/shipping/test/
```

**Description**: Test ShipRocket API connectivity

**Authentication**: Not required

**Response Example**:
```json
{
  "success": true,
  "message": "ShipRocket API connection successful",
  "data": {
    "status": "connected",
    "environment": "UAT"
  }
}
```

#### Check Serviceability
```http
GET /api/shipping/serviceability/
```

**Description**: Check if delivery is available between pincodes

**Authentication**: Not required

**Query Parameters**:
- `pickup_pincode` (required): Pickup location pincode
- `delivery_pincode` (required): Delivery location pincode
- `weight` (required): Package weight in kg
- `cod` (optional): Cash on delivery (true/false)

**Example Request**:
```http
GET /api/shipping/serviceability/?pickup_pincode=110001&delivery_pincode=400001&weight=1.5&cod=false
```

**Response Example**:
```json
{
  "success": true,
  "serviceable": true,
  "couriers": [
    {
      "courier_name": "Delhivery",
      "estimated_delivery_days": "2-3 days",
      "rate": 45.50
    },
    {
      "courier_name": "Bluedart",
      "estimated_delivery_days": "1-2 days", 
      "rate": 65.00
    }
  ],
  "message": "Serviceability check completed"
}
```

#### Get Shipping Rates
```http
GET /api/shipping/rates/
```

**Description**: Get shipping rates from multiple courier partners

**Authentication**: Not required

**Query Parameters**:
- `pickup_pincode` (required): Pickup location pincode
- `delivery_pincode` (required): Delivery location pincode
- `weight` (required): Package weight in kg
- `length` (optional): Package length in cm
- `breadth` (optional): Package breadth in cm
- `height` (optional): Package height in cm
- `cod` (optional): Cash on delivery (true/false)

**Example Request**:
```http
GET /api/shipping/rates/?pickup_pincode=110001&delivery_pincode=560001&weight=2.5&length=15&breadth=10&height=8
```

**Response Example**:
```json
{
  "success": true,
  "rates": [
    {
      "courier_name": "Delhivery",
      "rate": 75.50,
      "estimated_delivery_days": "3-4 days",
      "cod_charges": 25.00,
      "freight_charge": 50.50,
      "other_charges": 0.00
    },
    {
      "courier_name": "DTDC",
      "rate": 68.00,
      "estimated_delivery_days": "4-5 days",
      "cod_charges": 20.00,
      "freight_charge": 48.00,
      "other_charges": 0.00
    }
  ],
  "pickup_pincode": "110001",
  "delivery_pincode": "560001",
  "weight": 2.5
}
```

#### Create Shipment
```http
POST /api/shipping/shipments/create/
```

**Description**: Create a new shipment order

**Authentication**: Required

**Request Body**:
```json
{
  "order_id": "ORD_001",
  "customer_name": "John Doe",
  "customer_email": "john@example.com",
  "customer_phone": "9876543210",
  "billing_address": "123 Main Street",
  "billing_city": "Mumbai",
  "billing_state": "Maharashtra",
  "billing_pincode": "400001",
  "shipping_address": "123 Main Street",
  "shipping_city": "Mumbai", 
  "shipping_state": "Maharashtra",
  "shipping_pincode": "400001",
  "weight": 1.5,
  "length": 15,
  "breadth": 10,
  "height": 8,
  "sub_total": 999.00,
  "payment_method": "Prepaid",
  "items": [
    {
      "name": "Paracetamol 500mg",
      "sku": "PAR500",
      "quantity": 2,
      "price": 15.00
    },
    {
      "name": "Vitamin D3",
      "sku": "VIT001",
      "quantity": 1,
      "price": 250.00
    }
  ]
}
```

**Response Example**:
```json
{
  "success": true,
  "message": "Shipment created successfully",
  "data": {
    "order_id": "ORD_001",
    "shiprocket_order_id": "12345678",
    "shipment_id": "87654321",
    "awb_code": "AWB123456789",
    "courier_name": "Delhivery",
    "expected_delivery_date": "2025-09-01",
    "pickup_scheduled_date": "2025-08-29"
  }
}
```

#### List User Shipments
```http
GET /api/shipping/shipments/
```

**Description**: Get list of user's shipments

**Authentication**: Required

**Response Example**:
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "order_id": "ORD_001",
      "awb_code": "AWB123456789",
      "courier_name": "Delhivery",
      "status": "delivered",
      "created_at": "2025-08-25T10:30:00Z",
      "delivered_at": "2025-08-28T14:45:00Z"
    }
  ]
}
```

#### Get Shipment Details
```http
GET /api/shipping/shipments/{order_id}/
```

**Description**: Get detailed information about a specific shipment

**Authentication**: Required

**Response Example**:
```json
{
  "order_id": "ORD_001",
  "shiprocket_order_id": "12345678",
  "awb_code": "AWB123456789",
  "courier_name": "Delhivery",
  "status": "delivered",
  "tracking_events": [
    {
      "date": "2025-08-25T10:30:00Z",
      "status": "order_confirmed",
      "location": "Delhi",
      "description": "Order confirmed and ready for pickup"
    },
    {
      "date": "2025-08-26T09:15:00Z",
      "status": "picked_up",
      "location": "Delhi",
      "description": "Package picked up by courier"
    },
    {
      "date": "2025-08-28T14:45:00Z",
      "status": "delivered",
      "location": "Mumbai",
      "description": "Package delivered successfully"
    }
  ]
}
```

#### Track Shipment
```http
GET /api/shipping/track/
```

**Description**: Track shipment using order ID or AWB code

**Authentication**: Not required

**Query Parameters**:
- `order_id` (optional): Internal order ID
- `awb_code` (optional): AWB tracking code

**Example Request**:
```http
GET /api/shipping/track/?order_id=ORD_001
```

**Response Example**:
```json
{
  "success": true,
  "tracking_data": {
    "awb_code": "AWB123456789",
    "courier_name": "Delhivery",
    "current_status": "delivered",
    "delivered_date": "2025-08-28",
    "expected_delivery": "2025-08-30",
    "events": [
      {
        "date": "2025-08-25",
        "time": "10:30",
        "status": "Picked up",
        "location": "Delhi Hub",
        "description": "Package picked up from seller"
      },
      {
        "date": "2025-08-28",
        "time": "14:45",
        "status": "Delivered",
        "location": "Mumbai",
        "description": "Delivered to customer"
      }
    ]
  }
}
```

#### Webhook Endpoint (Internal)
```http
POST /api/shipping/webhook/
```

**Description**: Receives automatic status updates from ShipRocket

**Authentication**: Not required (internal endpoint)

**Note**: This endpoint is configured in ShipRocket dashboard for automatic status updates.

---

## 📦 Order Management API

### List Orders (MedixMall Aware)
```http
GET /api/orders/
```

**Description**: Get user's orders with MedixMall mode filtering

**Authentication**: Required

**MedixMall Mode Behavior**:
- **Mode OFF**: Shows all user orders
- **Mode ON**: Shows only orders containing medicine products exclusively
- **Admin Users**: Always see all orders regardless of mode

**Query Parameters**:
- `status`: Filter by order status
- `payment_status`: Filter by payment status
- `payment_method`: Filter by payment method
- `search`: Search in order number or user email

**Response Headers**:
- `X-MedixMall-Mode`: Current user's mode

**Response Example**:
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "order_number": "ORD-2025-001",
      "status": "delivered",
      "payment_status": "paid",
      "total": "275.00",
      "created_at": "2025-08-25T10:30:00Z",
      "items": [
        {
          "product": {
            "name": "Paracetamol 500mg",
            "product_type": "medicine"
          },
          "quantity": 2,
          "price": "15.00"
        }
      ]
    }
  ]
}
```

### Get Order Details
```http
GET /api/orders/{id}/
```

**Description**: Get detailed information about a specific order

**Authentication**: Required (owner or admin)

**Response Headers**:
- `X-MedixMall-Mode`: Current user's mode

---

## 🔐 Authentication & Authorization

### User Types
1. **Anonymous Users**: Can use MedixMall mode (session-based), view products, search
2. **Authenticated Users**: Full access with persistent MedixMall mode preference
3. **Admin Users**: Full access to all features regardless of MedixMall mode

### Authentication Methods

#### Login
```http
POST /api/accounts/login/
```

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response**:
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "user",
    "medixmall_mode": false
  },
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### JWT Token Usage
Include in headers for authenticated endpoints:
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

---

## ❌ Error Handling

### Standard Error Response
```json
{
  "error": "Error message",
  "details": "Detailed error information",
  "code": "ERROR_CODE"
}
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `AUTH_REQUIRED` | Authentication required | 401 |
| `PERMISSION_DENIED` | Access forbidden | 403 |
| `NOT_FOUND` | Resource not found | 404 |
| `VALIDATION_ERROR` | Invalid request data | 400 |
| `SHIPROCKET_ERROR` | ShipRocket API error | 400/500 |
| `RATE_LIMIT` | Too many requests | 429 |

### MedixMall Mode Specific Errors
```json
{
  "error": "Invalid MedixMall mode value",
  "details": "medixmall_mode must be boolean (true/false)",
  "code": "VALIDATION_ERROR"
}
```

### ShipRocket Specific Errors
```json
{
  "error": "ShipRocket authentication failed",
  "details": "Invalid email and password combination",
  "code": "SHIPROCKET_AUTH_ERROR"
}
```

---

## 🧪 Testing Guide

### Automated Testing
Run comprehensive test suite:
```bash
python test_all_systems_comprehensive.py
```

### Manual Testing

#### 1. MedixMall Mode Testing
```bash
# Get initial mode (anonymous)
curl http://127.0.0.1:8000/api/accounts/medixmall-mode/

# Enable MedixMall mode
curl -X PUT http://127.0.0.1:8000/api/accounts/medixmall-mode/ \
  -H "Content-Type: application/json" \
  -d '{"medixmall_mode": true}'

# Test product filtering
curl http://127.0.0.1:8000/api/public/products/products/
```

#### 2. Enterprise Search Testing
```bash
# Basic search
curl "http://127.0.0.1:8000/api/public/products/search/?q=paracetamol"

# Advanced search with filters
curl "http://127.0.0.1:8000/api/public/products/search/?q=medicine&product_type=medicine&sort_by=price_low&min_price=10&max_price=100"

# Search with MedixMall mode
curl "http://127.0.0.1:8000/api/public/products/search/?q=tablet" \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

#### 3. ShipRocket Testing
```bash
# Test connection
curl http://127.0.0.1:8000/api/shipping/test/

# Check serviceability
curl "http://127.0.0.1:8000/api/shipping/serviceability/?pickup_pincode=110001&delivery_pincode=400001&weight=1.0"

# Get shipping rates
curl "http://127.0.0.1:8000/api/shipping/rates/?pickup_pincode=110001&delivery_pincode=560001&weight=2.5"
```

#### 4. Authenticated Testing
```bash
# Login
TOKEN=$(curl -X POST http://127.0.0.1:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpassword123"}' \
  | jq -r '.access')

# Test authenticated MedixMall mode
curl http://127.0.0.1:8000/api/accounts/medixmall-mode/ \
  -H "Authorization: Bearer $TOKEN"

# Test orders
curl http://127.0.0.1:8000/api/orders/ \
  -H "Authorization: Bearer $TOKEN"

# Create shipment
curl -X POST http://127.0.0.1:8000/api/shipping/shipments/create/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "TEST_001",
    "customer_name": "Test Customer",
    "customer_email": "test@example.com",
    "customer_phone": "9876543210",
    "billing_address": "123 Test Street",
    "billing_city": "Mumbai",
    "billing_state": "Maharashtra", 
    "billing_pincode": "400001",
    "weight": 1.5,
    "sub_total": 999.00,
    "payment_method": "Prepaid",
    "items": [{"name": "Test Product", "sku": "TEST001", "quantity": 1, "price": 999.00}]
  }'
```

### Test Users
- **Regular User**: `test@example.com` / `testpassword123`
- **Admin User**: `admin@example.com` / `adminpassword123`
- **Supplier User**: `supplier@example.com` / `supplierpassword123`

---

## 📚 API Documentation URLs

- **Swagger UI**: http://127.0.0.1:8000/swagger/
- **ReDoc**: http://127.0.0.1:8000/redoc/
- **OpenAPI Schema**: http://127.0.0.1:8000/swagger.json

---

## 🚀 Production Deployment

### Environment Configuration
```python
# Production settings
SHIPROCKET_UAT = False
SHIPROCKET_EMAIL = "production@company.com"
SHIPROCKET_PASSWORD = "production_password"

# Update pickup location with real address
DEFAULT_PICKUP_LOCATION = {
    "pickup_location": "Main Warehouse",
    "name": "Your Company Name",
    "email": "pickup@yourcompany.com",
    "phone": "your_phone_number",
    "address": "Your Real Address",
    "city": "Your City",
    "state": "Your State",
    "country": "India",
    "pin_code": "your_pincode"
}
```

### Webhook Configuration
1. Login to ShipRocket dashboard
2. Navigate to Settings > Webhooks
3. Add webhook URL: `https://yourdomain.com/api/shipping/webhook/`
4. Enable order status update notifications

### Security Considerations
- Use HTTPS in production
- Implement rate limiting
- Monitor API usage
- Set up logging and alerting
- Regular security audits

---

## 📞 Support & Troubleshooting

### Common Issues

#### MedixMall Mode Not Working
- Check user authentication
- Verify session/database storage
- Check response headers

#### Search Not Returning Results
- Verify search parameters
- Check product data in database
- Test with simple queries first

#### ShipRocket Authentication Failed
- Update credentials in `shiprocket_config.py`
- Check UAT vs Production environment
- Contact ShipRocket support for account access

#### Orders Not Filtered Correctly
- Check user's MedixMall mode setting
- Verify product types in database
- Check admin user privileges

### Debug Commands
```bash
# Check user's MedixMall mode
python manage.py shell -c "
from accounts.models import User
user = User.objects.get(email='test@example.com')
print(f'MedixMall Mode: {user.medixmall_mode}')
"

# Check product types
python manage.py shell -c "
from products.models import Product
print('Medicine products:', Product.objects.filter(product_type='medicine').count())
print('Total products:', Product.objects.count())
"

# Test ShipRocket connection
python manage.py shell -c "
from shiprocket_service import ShipRocketAPI
api = ShipRocketAPI()
result = api.test_connection()
print(result)
"
```

---

**Status**: ✅ **PRODUCTION READY**  
**Last Updated**: August 28, 2025  
**Version**: 2.0.0  
**Features**: MedixMall Mode ✓ | Enterprise Search ✓ | ShipRocket Integration ✓ | Full Documentation ✓