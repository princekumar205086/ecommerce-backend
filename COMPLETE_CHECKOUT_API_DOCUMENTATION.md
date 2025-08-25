# Complete Checkout Flow API Documentation

This document provides comprehensive documentation for the complete e-commerce checkout flow, covering Cart, Order, and Payment APIs working together.

## Authentication Required
All endpoints require JWT authentication:
```
Authorization: Bearer <your_jwt_token>
```

## Permission Requirements
- **Allowed Roles**: `user`, `supplier`
- **Blocked Roles**: `admin` (Admins cannot have shopping carts or place orders)
- **Unauthenticated**: Blocked with 401 status

---

## Complete Checkout Flow Overview

The checkout process follows this sequence:
1. **Cart Management**: Add/modify products in cart
2. **Address Collection**: Gather shipping and billing addresses
3. **Order Creation**: Convert cart to order with addresses
4. **Payment Initialization**: Create payment record via Razorpay
5. **Payment Processing**: User completes payment (frontend)
6. **Payment Verification**: Verify payment success
7. **Order Fulfillment**: Auto-update order status and inventory

**Flow Pattern**: `cart(cart_id, address) → payment (if success) → order auto creation & status update`

---

## 🛒 Cart Management APIs

### 1. GET /api/cart/
**Description**: Retrieve current user's cart with all items
**Method**: GET

#### Response (200 OK):
```json
{
    "id": 3,
    "user": 2,
    "items": [
        {
            "id": 15,
            "product": {
                "id": 46,
                "name": "Fixed Image Test Pathology",
                "price": "299.99",
                "image": "/media/product_images/test_image.jpg"
            },
            "variant": null,
            "quantity": 2,
            "total_price": 599.98
        }
    ],
    "total_items": 6,
    "total_price": 2899.94,
    "created_at": "2025-08-25T10:30:00Z",
    "updated_at": "2025-08-25T10:35:00Z"
}
```

### 2. POST /api/cart/add/
**Description**: Add a product to cart
**Method**: POST

#### Request Body:
```json
{
    "product_id": 46,
    "quantity": 2,
    "variant_id": null  // Optional
}
```

#### Response (201 Created):
```json
{
    "message": "Item added to cart"
}
```

### 3. PUT /api/cart/items/{item_id}/update/
**Description**: Update quantity of a cart item
**Method**: PUT

#### Request Body:
```json
{
    "quantity": 5
}
```

#### Response (200 OK):
```json
{
    "quantity": 5
}
```

### 4. DELETE /api/cart/items/{item_id}/remove/
**Description**: Remove a specific item from cart
**Method**: DELETE

#### Response (204 No Content):
No response body

### 5. DELETE /api/cart/clear/
**Description**: Remove all items from cart
**Method**: DELETE

#### Response (204 No Content):
No response body

---

## 📦 Order Management APIs

### 1. POST /api/orders/checkout/
**Description**: Create order from cart with shipping/billing addresses
**Method**: POST

#### Request Body:
```json
{
    "cart_id": 3,
    "shipping_address": {
        "name": "John Doe",
        "phone": "9876543210",
        "address_line1": "123 Main Street",
        "address_line2": "Apartment 4B",
        "city": "New Delhi",
        "state": "Delhi",
        "postal_code": "110001",
        "country": "India"
    },
    "billing_address": {
        "name": "John Doe",
        "phone": "9876543210",
        "address_line1": "456 Business Avenue",
        "address_line2": "Suite 200",
        "city": "Mumbai",
        "state": "Maharashtra",
        "postal_code": "400001",
        "country": "India"
    },
    "payment_method": "credit_card",
    "coupon_code": "DISCOUNT20",  // Optional
    "notes": "Please deliver before 7 PM"  // Optional
}
```

#### Response (201 Created):
```json
{
    "id": 7,
    "order_number": "202508250002",
    "user": {
        "id": 2,
        "email": "testuser@example.com",
        "full_name": "Test User"
    },
    "status": "pending",
    "current_status": {
        "status": "Pending",
        "timestamp": "2025-08-25T12:30:45Z",
        "changed_by": null
    },
    "payment_status": "pending",
    "payment_method": "credit_card",
    "subtotal": "2899.94",
    "tax": "289.99",
    "shipping_charge": "0.00",
    "discount": "0.00",
    "coupon": null,
    "coupon_discount": "0.00",
    "total": "3189.93",
    "created_at": "2025-08-25T12:30:45Z",
    "updated_at": "2025-08-25T12:30:45Z",
    "shipping_address": {
        "name": "John Doe",
        "phone": "9876543210",
        "address_line1": "123 Main Street",
        "address_line2": "Apartment 4B",
        "city": "New Delhi",
        "state": "Delhi",
        "postal_code": "110001",
        "country": "India"
    },
    "billing_address": {
        "name": "John Doe",
        "phone": "9876543210",
        "address_line1": "456 Business Avenue",
        "address_line2": "Suite 200",
        "city": "Mumbai",
        "state": "Maharashtra",
        "postal_code": "400001",
        "country": "India"
    },
    "notes": "Please deliver before 7 PM",
    "items": [
        {
            "id": 1,
            "product": {
                "id": 46,
                "name": "Fixed Image Test Pathology",
                "price": "299.99"
            },
            "variant": null,
            "quantity": 2,
            "price": "299.99",
            "total_price": "599.98",
            "created_at": "2025-08-25T12:30:45Z"
        }
    ],
    "status_changes": []
}
```

### 2. GET /api/orders/
**Description**: List all orders for the current user
**Method**: GET

#### Query Parameters:
- `status`: Filter by order status (pending, processing, shipped, delivered, cancelled)
- `payment_status`: Filter by payment status (pending, paid, failed, refunded)
- `ordering`: Sort by fields like `-created_at`, `total`

#### Response (200 OK):
```json
[
    {
        "id": 7,
        "order_number": "202508250002",
        "status": "pending",
        "payment_status": "pending",
        "total": "3189.93",
        "created_at": "2025-08-25T12:30:45Z"
        // ... other fields
    }
]
```

### 3. GET /api/orders/{id}/
**Description**: Get details of a specific order
**Method**: GET

#### Response (200 OK):
Returns the same detailed order object as the checkout response.

---

## 💳 Payment APIs

### 1. POST /api/payments/create/
**Description**: Initialize payment for an order
**Method**: POST

#### Request Body:
```json
{
    "order_id": 7,
    "amount": "3189.93",
    "currency": "INR"
}
```

#### Response (200 OK):
```json
{
    "order_id": "order_R9UiRUcWy8W0TG",
    "amount": 318993,  // Amount in paise (for Razorpay)
    "currency": "INR",
    "key": "rzp_test_hZpYcGhumUM4Z2",
    "name": "Your E-commerce Store",
    "description": "Payment for Order #202508250002",
    "prefill": {
        "name": "Test User",
        "email": "testuser@example.com"
    },
    "notes": {
        "order_id": 7
    }
}
```

**Usage**: This response should be used to initialize the Razorpay payment widget on the frontend.

### 2. POST /api/payments/verify/
**Description**: Verify payment after completion
**Method**: POST

#### Request Body:
```json
{
    "razorpay_order_id": "order_R9UiRUcWy8W0TG",
    "razorpay_payment_id": "pay_R9UjF4KcE8FG2s",
    "razorpay_signature": "b779166df8c44354c3b58c5426a663439fae3f2098af28438db7b0590ee7f5e9"
}
```

#### Response (200 OK):
```json
{
    "status": "Payment successful"
}
```

**Post-verification Effects**:
- Payment status updated to "successful"
- Order payment_status updated to "paid"
- Order status may change to "processing"
- Stock automatically deducted from inventory

### 3. GET /api/payments/
**Description**: List all payments for the current user
**Method**: GET

#### Response (200 OK):
```json
[
    {
        "id": 4,
        "order": {
            "id": 7,
            "order_number": "202508250002"
        },
        "razorpay_payment_id": "pay_R9UjF4KcE8FG2s",
        "razorpay_order_id": "order_R9UiRUcWy8W0TG",
        "amount": "3189.93",
        "currency": "INR",
        "status": "successful",
        "created_at": "2025-08-25T12:35:22Z",
        "updated_at": "2025-08-25T12:36:10Z",
        "webhook_verified": true
    }
]
```

### 4. GET /api/payments/{id}/
**Description**: Get details of a specific payment
**Method**: GET

Returns detailed payment information including order details and transaction status.

---

## 🔄 Complete Flow Example

Here's a step-by-step example of the complete checkout flow:

### Step 1: Add Products to Cart
```bash
POST /api/cart/add/
{
    "product_id": 46,
    "quantity": 2
}
```

### Step 2: Verify Cart Contents
```bash
GET /api/cart/
# Returns cart with items and total
```

### Step 3: Create Order with Addresses
```bash
POST /api/orders/checkout/
{
    "cart_id": 3,
    "shipping_address": { ... },
    "billing_address": { ... },
    "payment_method": "credit_card"
}
# Returns order object with ID 7
```

### Step 4: Initialize Payment
```bash
POST /api/payments/create/
{
    "order_id": 7,
    "amount": "3189.93",
    "currency": "INR"
}
# Returns Razorpay configuration for frontend
```

### Step 5: Frontend Payment Processing
```javascript
// Frontend code using Razorpay
const options = {
    key: response.key,
    amount: response.amount,
    currency: response.currency,
    order_id: response.order_id,
    handler: function(response) {
        // Step 6: Verify payment
        verifyPayment(response);
    }
};
const rzp = new Razorpay(options);
rzp.open();
```

### Step 6: Verify Payment
```bash
POST /api/payments/verify/
{
    "razorpay_order_id": "order_R9UiRUcWy8W0TG",
    "razorpay_payment_id": "pay_R9UjF4KcE8FG2s", 
    "razorpay_signature": "b779166df..."
}
# Payment verified, order status updated
```

### Step 7: Check Final Order Status
```bash
GET /api/orders/7/
# Returns order with payment_status: "paid", status: "processing"
```

---

## 🚨 Error Handling

### Common Error Responses:

#### 400 Bad Request:
```json
{
    "error": "Insufficient stock for Fixed Image Test Pathology. Available: 98, Requested: 100"
}
```

#### 401 Unauthorized:
```json
{
    "detail": "Given token not valid for any token type",
    "code": "token_not_valid"
}
```

#### 403 Forbidden:
```json
{
    "error": "Admins cannot access cart functionality"
}
```

#### 404 Not Found:
```json
{
    "error": "Cart item not found"
}
```

#### 500 Server Error:
```json
{
    "error": "An error occurred during checkout"
}
```

---

## 🔒 Security Features

1. **JWT Authentication**: All endpoints require valid JWT tokens
2. **User Isolation**: Users can only access their own carts, orders, and payments
3. **Role-based Access**: Admins cannot place orders (business logic)
4. **Payment Security**: Razorpay signature verification prevents payment tampering
5. **Stock Validation**: Prevents overselling through atomic transactions
6. **Address Validation**: Ensures required address fields are provided

---

## 📊 Business Logic

### Automatic Processes:
1. **Cart Clearance**: Cart is automatically cleared after successful order creation
2. **Stock Deduction**: Product stock is deducted when order is created
3. **Tax Calculation**: 10% tax automatically applied to subtotal
4. **Order Numbering**: Sequential order numbers generated (YYYYMMDDNNNN format)
5. **Status Tracking**: Order status changes are logged with timestamps

### Inventory Management:
- Stock validation occurs during cart operations
- Stock is reserved when order is created
- Stock is deducted atomically to prevent race conditions
- Variants have separate stock tracking from base products

### Payment Integration:
- Supports multiple payment methods (credit card, debit card, UPI, etc.)
- Webhooks handle asynchronous payment notifications
- Payment verification uses Razorpay's signature verification
- Failed payments don't affect order status

---

## 🧪 Testing

Use the provided test script to validate the entire flow:

```bash
python comprehensive_checkout_test.py
```

This script tests:
- ✅ User authentication
- ✅ Cart management (add, update, remove, clear)
- ✅ Order creation with addresses
- ✅ Payment initialization
- ✅ Cart clearance after order creation
- ✅ Order status verification
- ✅ Individual endpoint functionality

---

## 📝 Integration Notes

### Frontend Integration:
1. Use JWT tokens for all API calls
2. Implement Razorpay widget for payment processing
3. Handle payment callbacks and verification
4. Provide real-time order status updates
5. Implement proper error handling and user feedback

### Production Considerations:
1. Set up Razorpay webhook endpoints
2. Configure proper Razorpay keys (live vs test)
3. Implement rate limiting for payment endpoints
4. Set up monitoring for failed payments
5. Configure email notifications for order status changes

The checkout flow is fully functional and production-ready! 🚀