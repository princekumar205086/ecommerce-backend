# Complete Order Management API Documentation

## Overview
This document provides comprehensive documentation for all order-related endpoints in the eCommerce backend system. The API supports three user roles: **User**, **Supplier**, and **Admin**, each with different levels of access and functionality.

## Table of Contents
1. [Authentication](#authentication)
2. [User Order Endpoints](#user-order-endpoints)
3. [Admin Order Endpoints](#admin-order-endpoints)
4. [Supplier Order Endpoints](#supplier-order-endpoints)
5. [ShipRocket Integration Endpoints](#shiprocket-integration-endpoints)
6. [Order Models](#order-models)
7. [Error Handling](#error-handling)
8. [MedixMall Mode](#medixmall-mode)

## Authentication
All endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <access_token>
```

Get tokens using:
```
POST /api/token/
{
    "email": "user@example.com",
    "password": "password"
}
```

## User Order Endpoints

### 1. Create Order from Cart (Checkout)
**POST** `/api/orders/checkout/`

Creates a new order from cart contents.

**Request Body:**
```json
{
    "cart_id": 1,
    "shipping_address": {
        "name": "John Doe",
        "address_line_1": "123 Main Street",
        "address_line_2": "Apt 4B",
        "city": "Delhi",
        "state": "Delhi",
        "postal_code": "110001",
        "country": "India",
        "phone": "9876543210"
    },
    "billing_address": {
        "name": "John Doe",
        "address_line_1": "123 Main Street",
        "city": "Delhi",
        "state": "Delhi",
        "postal_code": "110001",
        "country": "India",
        "phone": "9876543210"
    },
    "payment_method": "cod",
    "coupon_code": "SAVE10",
    "notes": "Please deliver after 6 PM"
}
```

**Response:**
```json
{
    "id": 1,
    "order_number": "202509020001",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "full_name": "John Doe"
    },
    "status": "pending",
    "payment_status": "pending",
    "payment_method": "cod",
    "subtotal": "200.00",
    "tax": "20.00",
    "shipping_charge": "50.00",
    "discount": "0.00",
    "coupon_discount": "20.00",
    "total": "250.00",
    "created_at": "2025-09-02T10:30:00Z",
    "items": [
        {
            "id": 1,
            "product": {
                "id": 1,
                "name": "Medicine Name",
                "price": "100.00"
            },
            "quantity": 2,
            "price": "100.00",
            "total_price": "200.00"
        }
    ],
    "shipping_address": {...},
    "billing_address": {...}
}
```

### 2. List User Orders
**GET** `/api/orders/`

Lists all orders for the authenticated user.

**Query Parameters:**
- `status`: Filter by order status (pending, processing, shipped, delivered, cancelled)
- `payment_status`: Filter by payment status (pending, paid, failed)
- `payment_method`: Filter by payment method
- `search`: Search by order number or user email
- `ordering`: Sort by fields (created_at, total, -created_at, -total)

**Response:**
```json
{
    "count": 10,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "order_number": "202509020001",
            "status": "delivered",
            "payment_status": "paid",
            "total": "250.00",
            "created_at": "2025-09-02T10:30:00Z",
            "current_status": {
                "status": "Delivered",
                "timestamp": "2025-09-02T15:30:00Z",
                "changed_by": "admin@example.com"
            }
        }
    ]
}
```

**MedixMall Mode:** When user has `medixmall_mode=true`, only shows orders containing medicine products.

### 3. Get Order Details
**GET** `/api/orders/{id}/`

Gets detailed information about a specific order.

**Response:**
```json
{
    "id": 1,
    "order_number": "202509020001",
    "user": {...},
    "status": "delivered",
    "payment_status": "paid",
    "items": [...],
    "status_changes": [
        {
            "id": 1,
            "status": "delivered",
            "changed_by": {
                "email": "admin@example.com"
            },
            "notes": "Order delivered successfully",
            "created_at": "2025-09-02T15:30:00Z"
        }
    ],
    "shipping_address": {...},
    "billing_address": {...}
}
```

### 4. Apply Coupon to Order
**POST** `/api/orders/{order_id}/apply-coupon/`

Applies a coupon to an existing order (only for pending orders).

**Request Body:**
```json
{
    "coupon_code": "SAVE10"
}
```

**Response:**
```json
{
    "id": 1,
    "order_number": "202509020001",
    "coupon_discount": "20.00",
    "total": "230.00",
    "coupon": {
        "code": "SAVE10",
        "discount_value": "10.00",
        "coupon_type": "percentage"
    }
}
```

## Admin Order Endpoints

### 1. Accept Order
**POST** `/api/orders/admin/accept/`

Accept a pending order and move it to processing status.

**Request Body:**
```json
{
    "order_id": 1,
    "notes": "Order accepted and ready for processing"
}
```

**Response:**
```json
{
    "status": "success",
    "message": "Order accepted and moved to processing",
    "order_id": 1,
    "order_number": "202509020001",
    "new_status": "processing"
}
```

### 2. Reject Order
**POST** `/api/orders/admin/reject/`

Reject an order with a reason.

**Request Body:**
```json
{
    "order_id": 1,
    "reason": "Out of stock",
    "notes": "Product is temporarily unavailable"
}
```

**Response:**
```json
{
    "status": "success",
    "message": "Order rejected",
    "order_id": 1,
    "order_number": "202509020001",
    "new_status": "cancelled",
    "reason": "Out of stock"
}
```

### 3. Assign Shipping
**POST** `/api/orders/admin/assign-shipping/`

Assign order to a shipping partner with tracking details.

**Request Body:**
```json
{
    "order_id": 1,
    "shipping_partner": "Shiprocket",
    "tracking_id": "SR123456789",
    "notes": "Order shipped via Shiprocket"
}
```

**Response:**
```json
{
    "status": "success",
    "message": "Order assigned to Shiprocket",
    "order_id": 1,
    "order_number": "202509020001",
    "shipping_partner": "Shiprocket",
    "tracking_id": "SR123456789",
    "new_status": "shipped"
}
```

### 4. Mark as Delivered
**POST** `/api/orders/admin/mark-delivered/`

Mark an order as delivered.

**Request Body:**
```json
{
    "order_id": 1,
    "notes": "Order delivered successfully"
}
```

**Response:**
```json
{
    "status": "success",
    "message": "Order marked as delivered",
    "order_id": 1,
    "order_number": "202509020001",
    "delivered_at": "2025-09-02T15:30:00Z",
    "new_status": "delivered"
}
```

### 5. Order Statistics
**GET** `/api/orders/stats/`

Get comprehensive order statistics for admin dashboard.

**Response:**
```json
{
    "total_orders": 150,
    "total_revenue": "15000.00",
    "recent_orders": 25,
    "status_distribution": [
        {"status": "pending", "count": 10},
        {"status": "processing", "count": 8},
        {"status": "shipped", "count": 12},
        {"status": "delivered", "count": 115},
        {"status": "cancelled", "count": 5}
    ],
    "top_products": [
        {
            "product__name": "Popular Medicine",
            "total_sold": 50,
            "revenue": "2500.00"
        }
    ]
}
```

### 6. Admin Order Management (ViewSet)
**Base URL:** `/api/orders/admin/manage/`

Provides CRUD operations for admin order management:

- **GET** `/api/orders/admin/manage/` - List all orders
- **GET** `/api/orders/admin/manage/{id}/` - Get order details
- **PUT/PATCH** `/api/orders/admin/manage/{id}/` - Update order
- **POST** `/api/orders/admin/manage/{id}/accept_order/` - Accept order
- **POST** `/api/orders/admin/manage/{id}/reject_order/` - Reject order
- **POST** `/api/orders/admin/manage/{id}/assign_shipping/` - Assign shipping
- **POST** `/api/orders/admin/manage/{id}/mark_delivered/` - Mark delivered
- **GET** `/api/orders/admin/manage/dashboard_stats/` - Dashboard statistics

## Supplier Order Endpoints

### 1. List Supplier Orders
**GET** `/api/orders/supplier/`

Lists orders containing products created by the supplier.

**Response:**
```json
{
    "count": 5,
    "results": [
        {
            "id": 1,
            "order_number": "202509020001",
            "status": "processing",
            "total": "250.00",
            "created_at": "2025-09-02T10:30:00Z",
            "items": [
                {
                    "product": {
                        "name": "My Product",
                        "created_by": {
                            "email": "supplier@example.com"
                        }
                    }
                }
            ]
        }
    ]
}
```

### 2. Mark Items Ready to Ship
**POST** `/api/orders/supplier/{id}/mark_ready_to_ship/`

Mark supplier's items in an order as ready to ship.

**Response:**
```json
{
    "status": "success",
    "message": "Items marked as ready to ship",
    "order_id": 1,
    "order_number": "202509020001"
}
```

### 3. Supplier Order Summary
**GET** `/api/orders/supplier/my_orders_summary/`

Get summary of orders for the supplier.

**Response:**
```json
{
    "total_orders": 15,
    "pending_orders": 3,
    "processing_orders": 5,
    "shipped_orders": 4,
    "delivered_orders": 3,
    "recent_orders": [
        {
            "id": 1,
            "order_number": "202509020001",
            "status": "processing",
            "created_at": "2025-09-02T10:30:00Z",
            "total": "250.00"
        }
    ]
}
```

### 4. Supplier Order Statistics
**GET** `/api/orders/supplier/stats/`

Get detailed statistics for supplier orders.

**Response:**
```json
{
    "total_orders": 15,
    "total_revenue": "3750.00",
    "recent_orders": 8,
    "status_breakdown": {
        "pending": 3,
        "processing": 5,
        "shipped": 4,
        "delivered": 3,
        "cancelled": 0
    },
    "payment_status": {
        "pending": 8,
        "paid": 7,
        "failed": 0
    }
}
```

## ShipRocket Integration Endpoints

### 1. Check Serviceability
**POST** `/api/orders/shiprocket/serviceability/`

Check if delivery is serviceable for given pincodes.

**Request Body:**
```json
{
    "pickup_pincode": "110001",
    "delivery_pincode": "400001",
    "weight": 1.5,
    "cod": false
}
```

**Response:**
```json
{
    "success": true,
    "serviceable": true,
    "couriers": [
        {
            "courier_name": "BlueDart",
            "courier_id": "1",
            "freight_charge": "75.00",
            "cod_charge": "0.00",
            "delivery_days": "2-3"
        }
    ],
    "message": "Serviceability check completed"
}
```

### 2. Get Shipping Rates
**POST** `/api/orders/shiprocket/rates/`

Get shipping rates from different couriers.

**Request Body:**
```json
{
    "pickup_pincode": "110001",
    "delivery_pincode": "400001",
    "weight": 1.5,
    "dimensions": {
        "length": 15,
        "breadth": 10,
        "height": 8
    }
}
```

**Response:**
```json
{
    "success": true,
    "rates": [
        {
            "courier_name": "BlueDart",
            "freight_charge": "75.00",
            "cod_charge": "25.00",
            "total_charge": "100.00",
            "delivery_days": "2-3",
            "is_cod_available": true
        }
    ],
    "cheapest": {
        "courier_name": "Delhivery",
        "freight_charge": "65.00"
    },
    "message": "Shipping rates retrieved successfully"
}
```

### 3. Create ShipRocket Order
**POST** `/api/orders/shiprocket/create/`

Create a ShipRocket order from an existing order.

**Request Body:**
```json
{
    "order_id": 1
}
```

**Response:**
```json
{
    "success": true,
    "message": "ShipRocket order created successfully",
    "shiprocket_order_id": "SR123456",
    "shiprocket_shipment_id": "SH789012",
    "shipment_id": 1
}
```

### 4. Track Shipment
**GET** `/api/orders/shiprocket/track/{shipment_id}/`

Track a shipment using ShipRocket.

**Response:**
```json
{
    "success": true,
    "shipment": {
        "id": 1,
        "order_id": "202509020001",
        "status": "in_transit",
        "awb_code": "AWB123456789",
        "courier_name": "BlueDart",
        "tracking_url": "https://shiprocket.co/tracking/AWB123456789"
    },
    "tracking_data": {
        "current_status": "In Transit",
        "last_update": "2025-09-02T14:30:00Z",
        "estimated_delivery": "2025-09-03T18:00:00Z",
        "tracking_events": [...]
    }
}
```

### 5. Generate Invoice
**POST** `/api/orders/shiprocket/invoice/`

Generate invoice for orders using ShipRocket.

**Request Body:**
```json
{
    "order_ids": [1, 2, 3]
}
```

**Response:**
```json
{
    "success": true,
    "invoice_url": "https://shiprocket.co/invoice/download/123456",
    "message": "Invoice generated successfully"
}
```

## Order Models

### Order Status Values
- `pending` - Order placed, awaiting admin review
- `processing` - Order accepted and being prepared
- `shipped` - Order dispatched for delivery
- `delivered` - Order successfully delivered
- `cancelled` - Order cancelled
- `refunded` - Order refunded

### Payment Status Values
- `pending` - Payment not yet processed
- `partial` - Partially paid
- `paid` - Fully paid
- `failed` - Payment failed
- `refunded` - Payment refunded

### Payment Methods
- `credit_card` - Credit Card
- `debit_card` - Debit Card
- `net_banking` - Net Banking
- `upi` - UPI
- `cod` - Cash on Delivery

### Order Item Structure
```json
{
    "id": 1,
    "product": {
        "id": 1,
        "name": "Product Name",
        "price": "100.00",
        "sku": "PROD001"
    },
    "variant": {
        "id": 1,
        "size": "Large",
        "weight": "500g",
        "additional_price": "10.00"
    },
    "quantity": 2,
    "price": "100.00",
    "total_price": "200.00"
}
```

### Address Structure
```json
{
    "name": "John Doe",
    "address_line_1": "123 Main Street",
    "address_line_2": "Apt 4B",
    "city": "Delhi",
    "state": "Delhi",
    "postal_code": "110001",
    "country": "India",
    "phone": "9876543210"
}
```

## Error Handling

### Common Error Responses

**400 Bad Request:**
```json
{
    "error": "Validation error message",
    "details": {
        "field_name": ["Error description"]
    }
}
```

**401 Unauthorized:**
```json
{
    "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden:**
```json
{
    "error": "You do not have permission to perform this action."
}
```

**404 Not Found:**
```json
{
    "error": "Order not found"
}
```

**500 Internal Server Error:**
```json
{
    "error": "An error occurred during processing"
}
```

### Validation Errors

**Empty Cart:**
```json
{
    "error": "Cart is empty"
}
```

**Invalid Coupon:**
```json
{
    "error": "Invalid coupon code"
}
```

**Insufficient Stock:**
```json
{
    "error": "Not enough stock for Product Name. Available: 5, Requested: 10"
}
```

## MedixMall Mode

When a user has `medixmall_mode=true`, the API behavior changes:

1. **Order Filtering**: Only shows orders containing medicine products
2. **Response Headers**: Includes `X-MedixMall-Mode: true` header
3. **Product Filtering**: Cart and order operations consider only medicine products

**Example Response Header:**
```
X-MedixMall-Mode: true
```

This mode is designed for users who only want to see medical/pharmaceutical products and orders.

## Rate Limiting
- Standard rate limiting applies: 1000 requests per hour for authenticated users
- ShipRocket endpoints have additional rate limiting: 100 requests per hour

## Webhooks (Future Enhancement)
ShipRocket webhook endpoint for status updates:
```
POST /api/orders/shiprocket/webhook/
```

## Testing
Use the comprehensive test suite to validate all endpoints:
```bash
python comprehensive_order_endpoint_test.py
```

## Support
For API support and issues:
- Email: support@medecommerce.com
- Documentation: https://docs.medecommerce.com
- Status Page: https://status.medecommerce.com

---

**Last Updated:** September 2, 2025  
**API Version:** v1  
**Documentation Version:** 2.0