# Checkout Process API Documentation

This document outlines the complete checkout flow for the e-commerce platform, which involves three primary components:
1. Cart management
2. Payment processing (PAYMENT-FIRST APPROACH)
3. Order auto-creation (after successful payment)

All endpoints require authentication with a JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Permission Requirements
- **Allowed Roles**: `user`, `supplier`
- **Blocked Roles**: `admin` (Admins cannot have shopping carts or place orders)
- **Unauthenticated**: Blocked with 401 status

---

## Complete Checkout Flow

🔄 **NEW PAYMENT-FIRST WORKFLOW** (Recommended):

1. **Create/Manage Cart**: Add products to cart
2. **Create Payment from Cart**: Initialize payment directly from cart (NEW)
3. **Process Payment**: User completes payment (client-side)
4. **Verify Payment**: Confirm payment success 
5. **Auto-Create Order**: Order is automatically created from cart data (NEW)
6. **Order Status Update**: Order status reflects payment automatically

📝 **Legacy Order-First Workflow** (Still supported):

1. **Create/Manage Cart**: Add products to cart
2. **Checkout from Cart**: Convert cart to order with shipping/billing details
3. **Initialize Payment**: Create a payment record for the order
4. **Process Payment**: User completes payment (client-side)
5. **Verify Payment**: Confirm payment success 
6. **Order Status Update**: Order status changes to reflect payment

### 🎯 Key Benefits of Payment-First Approach:
- ✅ **Data Integrity**: Orders exist only after confirmed payment
- ✅ **No Orphaned Orders**: Prevents incomplete orders without payment
- ✅ **Financial Safety**: Payment processed before inventory allocation
- ✅ **Seamless Experience**: Automatic order creation after payment success

---

## 1. Cart Management Endpoints

### 1.1 GET /api/cart/
**Description**: Retrieve current user's cart with all items
**Permissions**: User, Supplier only
**Method**: GET

#### Response (200 OK):
```json
{
    "id": 1,
    "user": 2,
    "items": [
        {
            "id": 1,
            "product": {
                "id": 1,
                "name": "Sample Medicine",
                "price": "199.99",
                "image": "image_url"
            },
            "variant": {
                "id": 1,
                "size": "10mg",
                "additional_price": "50.00"
            },
            "quantity": 2,
            "total_price": 499.98
        }
    ],
    "total_items": 2,
    "total_price": 499.98,
    "created_at": "2025-08-23T10:30:00Z",
    "updated_at": "2025-08-23T10:35:00Z"
}
```

### 1.2 POST /api/cart/add/
**Description**: Add a product to cart
**Permissions**: User, Supplier only
**Method**: POST

#### Request Body:
```json
{
    "product_id": 1,
    "variant_id": 2,  // Optional
    "quantity": 3
}
```

#### Response (201 Created):
```json
{
    "message": "Item added to cart"
}
```

### 1.3 PUT /api/cart/items/<item_id>/update/
**Description**: Update quantity of a cart item
**Permissions**: User, Supplier only (own items only)
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

### 1.4 DELETE /api/cart/items/<item_id>/remove/
**Description**: Remove a specific item from cart
**Permissions**: User, Supplier only (own items only)
**Method**: DELETE

#### Response (204 No Content):
No response body

### 1.5 DELETE /api/cart/clear/
**Description**: Remove all items from cart
**Permissions**: User, Supplier only
**Method**: DELETE

#### Response (204 No Content):
No response body

---

## 2. Payment Endpoints (NEW PAYMENT-FIRST APPROACH)

### 2.1 POST /api/payments/create-from-cart/ 🆕
**Description**: Create payment directly from cart (RECOMMENDED - Payment-First Flow)
**Permissions**: User, Supplier only
**Method**: POST

#### Request Body:
```json
{
    "cart_id": 1,
    "shipping_address": {
        "full_name": "John Doe",
        "address_line_1": "123 Main St",
        "address_line_2": "Apt 4B",
        "city": "New Delhi",
        "state": "Delhi",
        "postal_code": "110001",
        "country": "India"
    },
    "billing_address": {
        "full_name": "John Doe",
        "address_line_1": "123 Main St",
        "address_line_2": "Apt 4B",
        "city": "New Delhi",
        "state": "Delhi",
        "postal_code": "110001",
        "country": "India"
    },
    "payment_method": "razorpay",
    "currency": "INR",
    "coupon_code": "DISCOUNT20"  // Optional
}
```

#### Response (200 OK):
```json
{
    "order_id": "order_R9VmHDWmrXWIza",
    "amount": 78379,  // Amount in paise (₹783.79)
    "currency": "INR",
    "key": "rzp_test_hZpYcGhumUM4Z2",
    "name": "Ecommerce",
    "description": "Payment for Cart 4",
    "prefill": {
        "name": "John Doe",
        "email": "user@example.com"
    },
    "notes": {
        "cart_id": 4,
        "payment_id": 13
    }
}
```

**Note**: 
- ❌ **No order is created yet** - only payment record with cart data
- ✅ Cart data is stored securely in payment record for later order creation
- ✅ Use this response to initialize Razorpay payment on frontend

### 2.2 POST /api/payments/verify/ (ENHANCED)
**Description**: Verify payment and auto-create order from cart data
**Permissions**: User, Supplier only (own payments)
**Method**: POST

#### Request Body:
```json
{
    "razorpay_order_id": "order_R9VmHDWmrXWIza",
    "razorpay_payment_id": "pay_N5tFKCFOHUHrS8",
    "razorpay_signature": "b779166df8c44354c3b58c5426a663439fae3f2098af28438db7b0590ee7f5e9"
}
```

#### Response (200 OK) - Payment-First Flow:
```json
{
    "status": "Payment successful",
    "message": "Payment verified and order created successfully",
    "order_created": true,
    "order": {
        "id": 9,
        "order_number": "ORD-2025-000009",
        "status": "pending",
        "total": "7259.95",
        "items_count": 2
    },
    "payment": {
        "id": 13,
        "status": "successful",
        "amount": "7837.94"
    }
}
```

#### Response (200 OK) - Legacy Flow:
```json
{
    "status": "Payment successful",
    "order_updated": true,
    "order_id": 1
}
```

### 2.3 POST /api/payments/create/ (LEGACY)
**Description**: Initialize payment for an existing order (Legacy Flow)
**Permissions**: User, Supplier only (own orders)
**Method**: POST

#### Request Body:
```json
{
    "order_id": 1,
    "amount": "549.98",
    "currency": "INR"
}
```

#### Response (200 OK):
```json
{
    "order_id": "order_N5tDEOBc5Uenrk",
    "amount": 54998,
    "currency": "INR",
    "key": "rzp_test_1234567890",
    "name": "Your E-commerce Store",
    "description": "Payment for Order #202508251001",
    "prefill": {
        "name": "John Doe",
        "email": "user@example.com"
    },
    "notes": {
        "order_id": 1
    }
}
```

---

## 3. Order Creation Endpoints (LEGACY SUPPORT)

### 3.1 POST /api/orders/checkout/ (LEGACY)
**Description**: Create a new order from cart contents (Legacy Order-First Flow)
**Permissions**: User, Supplier only
**Method**: POST

⚠️ **Note**: This endpoint creates an order immediately. For better data integrity, use the payment-first flow (`/api/payments/create-from-cart/`) instead.

#### Request Body:
```json
{
    "cart_id": 1,
    "shipping_address": {
        "name": "John Doe",
        "phone": "9876543210",
        "address_line1": "123 Main St",
        "address_line2": "Apt 4B",
        "city": "New Delhi",
        "state": "Delhi",
        "postal_code": "110001",
        "country": "India"
    },
    "billing_address": {
        "name": "John Doe",
        "phone": "9876543210",
        "address_line1": "123 Main St",
        "address_line2": "Apt 4B",
        "city": "New Delhi",
        "state": "Delhi",
        "postal_code": "110001",
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
    "id": 1,
    "order_number": "202508251001",
    "user": {
        "id": 2,
        "email": "user@example.com",
        "full_name": "John Doe"
    },
    "status": "pending",
    "current_status": {
        "status": "Pending",
        "timestamp": "2025-08-25T12:30:45Z",
        "changed_by": null
    },
    "payment_status": "pending",
    "payment_method": "credit_card",
    "subtotal": "499.98",
    "tax": "50.00",
    "shipping_charge": "0.00",
    "discount": "0.00",
    "coupon": null,
    "coupon_discount": "0.00",
    "total": "549.98",
    "created_at": "2025-08-25T12:30:45Z",
    "updated_at": "2025-08-25T12:30:45Z",
    "shipping_address": {
        "name": "John Doe",
        "phone": "9876543210",
        "address_line1": "123 Main St",
        "address_line2": "Apt 4B",
        "city": "New Delhi",
        "state": "Delhi",
        "postal_code": "110001",
        "country": "India"
    },
    "billing_address": {
        "name": "John Doe",
        "phone": "9876543210",
        "address_line1": "123 Main St",
        "address_line2": "Apt 4B",
        "city": "New Delhi",
        "state": "Delhi",
        "postal_code": "110001",
        "country": "India"
    },
    "notes": "Please deliver before 7 PM",
    "items": [
        {
            "id": 1,
            "product": {
                "id": 1,
                "name": "Sample Medicine",
                "price": "199.99",
                "image": "image_url"
            },
            "variant": {
                "id": 1,
                "size": "10mg",
                "additional_price": "50.00"
            },
            "quantity": 2,
            "price": "249.99",
            "total_price": "499.98",
            "created_at": "2025-08-25T12:30:45Z"
        }
    ],
    "status_changes": []
}
```

### 3.2 GET /api/orders/
**Description**: List all orders for the current user
**Permissions**: User, Supplier only (own orders), Admin (all orders)
**Method**: GET

#### Response (200 OK):
```json
[
    {
        "id": 1,
        "order_number": "202508251001",
        "status": "pending",
        "payment_status": "pending",
        "total": "549.98",
        "created_at": "2025-08-25T12:30:45Z"
        // (other fields omitted for brevity)
    },
    {
        "id": 2,
        "order_number": "202508251002",
        "status": "processing",
        "payment_status": "paid",
        "total": "799.50",
        "created_at": "2025-08-25T14:15:22Z"
        // (other fields omitted for brevity)
    }
]
```

### 3.3 GET /api/orders/{id}/
**Description**: Get details of a specific order
**Permissions**: User, Supplier only (own orders), Admin (all orders)
**Method**: GET

#### Response (200 OK):
```json
{
    "id": 1,
    "order_number": "202508251001",
    "user": {
        "id": 2,
        "email": "user@example.com",
        "full_name": "John Doe"
    },
    "status": "pending",
    "current_status": {
        "status": "Pending",
        "timestamp": "2025-08-25T12:30:45Z",
        "changed_by": null
    },
    "payment_status": "pending",
    "payment_method": "credit_card",
    "subtotal": "499.98",
    "tax": "50.00",
    "shipping_charge": "0.00",
    "discount": "0.00",
    "coupon": null,
    "coupon_discount": "0.00",
    "total": "549.98",
    "created_at": "2025-08-25T12:30:45Z",
    "updated_at": "2025-08-25T12:30:45Z",
    "shipping_address": {
        // Address details
    },
    "billing_address": {
        // Address details
    },
    "notes": "Please deliver before 7 PM",
    "items": [
        // Order items
    ],
    "status_changes": [
        // Status history
    ]
}
```

---

## 4. Additional Payment Endpoints

### 3.1 POST /api/payments/create/
**Description**: Initialize payment for an order
**Permissions**: User, Supplier only (own orders)
**Method**: POST

#### Request Body:
```json
{
    "order_id": 1,
    "amount": "549.98",
    "currency": "INR"
}
```

#### Response (200 OK):
```json
{
    "order_id": "order_N5tDEOBc5Uenrk",
    "amount": 54998,
    "currency": "INR",
    "key": "rzp_test_1234567890",
    "name": "Your E-commerce Store",
    "description": "Payment for Order #202508251001",
    "prefill": {
        "name": "John Doe",
        "email": "user@example.com"
    },
    "notes": {
        "order_id": 1
    }
}
```

**Note**: This response contains Razorpay payment gateway details that should be used in the frontend to initialize the payment form.

### 3.2 POST /api/payments/verify/
**Description**: Verify payment after completion
**Permissions**: User, Supplier only (own payments)
**Method**: POST

#### Request Body:
```json
{
    "razorpay_order_id": "order_N5tDEOBc5Uenrk",
    "razorpay_payment_id": "pay_N5tFKCFOHUHrS8",
    "razorpay_signature": "b779166df8c44354c3b58c5426a663439fae3f2098af28438db7b0590ee7f5e9"
}
```

#### Response (200 OK):
```json
{
    "status": "Payment successful"
}
```

### 4.1 GET /api/payments/
**Description**: List all payments for the current user
**Permissions**: User, Supplier only (own payments), Admin (all payments)
**Method**: GET

#### Response (200 OK):
```json
[
    {
        "id": 1,
        "order": {
            "id": 1,
            "order_number": "202508251001"
        },
        "razorpay_payment_id": "pay_N5tFKCFOHUHrS8",
        "razorpay_order_id": "order_N5tDEOBc5Uenrk",
        "amount": "549.98",
        "currency": "INR",
        "status": "successful",
        "created_at": "2025-08-25T12:35:22Z",
        "updated_at": "2025-08-25T12:36:10Z"
    }
]
```

### 4.2 GET /api/payments/{id}/
**Description**: Get details of a specific payment
**Permissions**: User, Supplier only (own payments), Admin (all payments)
**Method**: GET

#### Response (200 OK):
```json
{
    "id": 1,
    "order": {
        "id": 1,
        "order_number": "202508251001"
    },
    "razorpay_payment_id": "pay_N5tFKCFOHUHrS8",
    "razorpay_order_id": "order_N5tDEOBc5Uenrk",
    "razorpay_signature": "b779166df8c44354c3b58c5426a663439fae3f2098af28438db7b0590ee7f5e9",
    "amount": "549.98",
    "currency": "INR",
    "status": "successful",
    "created_at": "2025-08-25T12:35:22Z",
    "updated_at": "2025-08-25T12:36:10Z",
    "webhook_verified": false
}
```

---

## Error Handling

All endpoints follow a consistent error response format:

```json
{
    "error": "Error message description",
    "detail": "Additional error details"
}
```

Common error codes:
- **400**: Bad Request (invalid data, insufficient stock)
- **401**: Unauthorized (no token or invalid token)
- **403**: Forbidden (trying to access another user's resources)
- **404**: Not Found (resource doesn't exist)
- **500**: Server Error (unexpected issues)

---

## Important Notes

1. **Stock Validation**: All operations validate product/variant stock availability
2. **User Isolation**: Users can only access their own carts, orders, and payments
3. **Admin Restriction**: Admins cannot shop but can view all orders and payments
4. **Automatic Cart Creation**: Carts are created automatically when first accessed
5. **Payment Flow Options**: 
   - **🆕 RECOMMENDED - Payment-First**: Create payment from cart → User pays → Order auto-created
   - **Legacy - Order-First**: Create order → Initialize payment → User pays → Verify payment
6. **Order Status Lifecycle**:
   - pending → processing → shipped → delivered
   - (or can be cancelled/refunded)
7. **Payment Status Lifecycle**:
   - pending → paid → (optional: refunded)
8. **🔒 Data Integrity**: Payment-first approach ensures orders exist only after confirmed payment
9. **Auto Order Creation**: Orders are automatically created from cart data after successful payment verification

---

## Testing the Complete Flow

For developers and testers, we provide comprehensive testing scripts:

### 🆕 Payment-First Flow Testing (Recommended):
```bash
# Test payment creation from cart
python debug_payment_endpoint.py

# Test complete payment-first flow with manual order creation  
python test_payment_first_manual.py
```

### Legacy Order-First Flow Testing:
```bash
# Test legacy checkout flow
python checkout_flow_test.py
```

### What the Payment-First Test Does:
1. ✅ Logs in a user
2. ✅ Adds products to cart
3. ✅ Creates payment from cart (no order yet)
4. ✅ Simulates payment success
5. ✅ Auto-creates order from cart data
6. ✅ Verifies payment-order linkage

### What the Legacy Test Does:
1. Logs in a user
2. Adds products to cart
3. Creates an order from cart
4. Initializes payment for order
5. Simulates payment verification
6. Verifies order status updates

**Note**: Actual payment processing requires valid Razorpay credentials and is typically handled via frontend integration.

---

## 📊 API Endpoint Summary

| Endpoint | Method | Purpose | Creates Order? | Flow Type |
|----------|--------|---------|----------------|-----------|
| `/api/payments/create-from-cart/` | POST | Create payment from cart | ❌ No | 🆕 Payment-First |
| `/api/payments/verify/` | POST | Verify payment & auto-create order | ✅ Yes (if payment-first) | Both |
| `/api/orders/checkout/` | POST | Create order from cart | ✅ Yes | Legacy Order-First |
| `/api/payments/create/` | POST | Create payment for existing order | ❌ No | Legacy Order-First |

---

## 🔄 Migration Guide: Order-First → Payment-First

### For Frontend Developers:

**OLD Flow**:
```javascript
// 1. Create order first
const order = await createOrder(cartData);
// 2. Create payment for order  
const payment = await createPayment(order.id);
// 3. Process payment
const result = await processPayment(payment);
```

**NEW Flow** (Recommended):
```javascript
// 1. Create payment directly from cart
const payment = await createPaymentFromCart(cartData);
// 2. Process payment
const result = await processPayment(payment);
// 3. Order is auto-created during payment verification ✨
```

### Benefits:
- ✅ **Cleaner Flow**: One less API call
- ✅ **Data Integrity**: No orphaned orders
- ✅ **Error Handling**: Better payment failure handling
- ✅ **User Experience**: Faster checkout process