# 📚 Comprehensive Payment API Documentation

## 🎯 Overview

Complete documentation for all payment methods in the e-commerce backend:
- **Razorpay** - Online payment gateway
- **COD (Cash on Delivery)** - Pay on delivery
- **Pathlog Wallet** - Custom wallet with mobile/OTP verification

---
## 🔐 Authentication

All endpoints require JWT authentication unless specified otherwise.

### Headers Required:
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### Get JWT Token:
```bash
POST /api/accounts/login/
{
  "email": "user@example.com",
  "password": "password"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

---

## 🛒 Cart Management (Prerequisites)

Before making any payment, you need items in your cart.

### Add Item to Cart:
```bash
POST /api/cart/add/
{
  "product_id": 1,
  "variant_id": 2,
  "quantity": 2
}
```

### View Cart:
```bash
GET /api/cart/
```

**Response:**
```json
{
  "id": 1,
  "user": 1,
  "items": [
    {
      "id": 1,
      "product": {
        "id": 1,
        "name": "Pathology Collection Kit"
      },
      "variant": {
        "id": 2,
        "name": "Family Pack",
        "price": "235.00"
      },
      "quantity": 2,
      "subtotal": "470.00"
    }
  ],
  "total": "470.00"
}
```

---

## 💳 1. RAZORPAY PAYMENT FLOW

### Step 1: Create Razorpay Payment

**Endpoint:** `POST /api/payments/create-from-cart/`

**Payload:**
```json
{
  "payment_method": "razorpay",
  "shipping_address": {
    "full_name": "John Doe",
    "address_line_1": "123 Main Street",
    "address_line_2": "Apt 4B",
    "city": "Mumbai",
    "state": "Maharashtra",
    "postal_code": "400001",
    "country": "India"
  }
}
```

**Response:**
```json
{
  "payment_method": "razorpay",
  "payment_id": 1,
  "amount": 604.6,
  "currency": "INR",
  "razorpay_order_id": "order_MKlqKDZvp8cqAm",
  "razorpay_key": "rzp_test_xxxxxxxx",
  "message": "Razorpay order created successfully",
  "order_summary": {
    "subtotal": 470.0,
    "tax": 84.6,
    "shipping": 50.0,
    "discount": 0.0,
    "total": 604.6
  }
}
```

### Step 2: Frontend Razorpay Integration

Use the response data to integrate with Razorpay checkout:

```javascript
const options = {
  key: response.razorpay_key,
  amount: response.amount * 100, // Amount in paise
  currency: response.currency,
  order_id: response.razorpay_order_id,
  name: "Your Store Name",
  description: "Order Payment",
  handler: function(response) {
    // Success callback
    confirmRazorpayPayment(response);
  },
  prefill: {
    name: "John Doe",
    email: "john@example.com",
    contact: "9999999999"
  }
};

const rzp = new Razorpay(options);
rzp.open();
```

### Step 3: Confirm Razorpay Payment

**Endpoint:** `POST /api/payments/confirm-razorpay/`

**Payload:**
```json
{
  "payment_id": 1,
  "razorpay_order_id": "order_MKlqKDZvp8cqAm",
  "razorpay_payment_id": "pay_MKlqKDZvp8cqAm",
  "razorpay_signature": "signature_hash_here"
}
```

**Success Response:**
```json
{
  "status": "Payment successful",
  "order_created": true,
  "order_id": 1,
  "order_number": "202508250001",
  "message": "Payment successful. Order created: #202508250001"
}
```

**Error Response:**
```json
{
  "error": "Payment verification failed"
}
```

---

## 🚚 2. COD (CASH ON DELIVERY) FLOW

### Step 1: Create COD Payment

**Endpoint:** `POST /api/payments/create-from-cart/`

**Payload:**
```json
{
  "payment_method": "cod",
  "shipping_address": {
    "full_name": "Jane Smith",
    "address_line_1": "456 Oak Avenue",
    "address_line_2": "Floor 2",
    "city": "Delhi",
    "state": "Delhi",
    "postal_code": "110001",
    "country": "India"
  }
}
```

**Response:**
```json
{
  "payment_method": "cod",
  "payment_id": 2,
  "amount": 604.6,
  "currency": "INR",
  "message": "COD order created. Please confirm to proceed.",
  "next_step": "/api/payments/confirm-cod/",
  "order_summary": {
    "subtotal": 470.0,
    "tax": 84.6,
    "shipping": 50.0,
    "discount": 0.0,
    "total": 604.6
  }
}
```

### Step 2: Confirm COD Payment

**Endpoint:** `POST /api/payments/confirm-cod/`

**Payload:**
```json
{
  "payment_id": 2
}
```

**Success Response:**
```json
{
  "status": "COD confirmed",
  "message": "COD order created: #202508250002",
  "order_created": true,
  "order": {
    "id": 2,
    "order_number": "202508250002",
    "status": "pending",
    "payment_status": "pending",
    "total": "517.00",
    "items_count": 1
  },
  "payment": {
    "id": 2,
    "status": "cod_confirmed",
    "amount": "604.60",
    "method": "cod"
  }
}
```

**Error Response:**
```json
{
  "error": "Payment not found"
}
```

---

## 📱 3. PATHLOG WALLET FLOW

### Step 1: Create Pathlog Wallet Payment

**Endpoint:** `POST /api/payments/create-from-cart/`

**Payload:**
```json
{
  "payment_method": "pathlog_wallet",
  "shipping_address": {
    "full_name": "Amit Kumar",
    "address_line_1": "789 Tech Park",
    "address_line_2": "Building A",
    "city": "Bangalore",
    "state": "Karnataka",
    "postal_code": "560001",
    "country": "India"
  }
}
```

**Response:**
```json
{
  "payment_method": "pathlog_wallet",
  "payment_id": 3,
  "amount": 604.6,
  "currency": "INR",
  "message": "Pathlog Wallet payment created. Please verify your wallet to proceed.",
  "next_step": "/api/payments/pathlog-wallet/verify/",
  "verification_required": true,
  "order_summary": {
    "subtotal": 470.0,
    "tax": 84.6,
    "shipping": 50.0,
    "discount": 0.0,
    "total": 604.6
  }
}
```

### Step 2: Verify Mobile Number

**Endpoint:** `POST /api/payments/pathlog-wallet/verify/`

**Payload:**
```json
{
  "payment_id": 3,
  "mobile_number": "8677939971"
}
```

**Success Response:**
```json
{
  "status": "OTP Sent",
  "message": "OTP sent to +91 8677939971",
  "mobile_number": "8677939971",
  "demo_otp": "123456"
}
```

**Error Response:**
```json
{
  "error": "Payment not found"
}
```

### Step 3: Verify OTP and Check Balance

**Endpoint:** `POST /api/payments/pathlog-wallet/otp/`

**Payload:**
```json
{
  "payment_id": 3,
  "otp": "123456"
}
```

**Success Response:**
```json
{
  "status": "Wallet Verified Successfully",
  "account_details": {
    "name": "Pathlog User",
    "phone": "+91 8677939971",
    "pathlog_id": "PL939971"
  },
  "available_balance": 1302.0,
  "payment_amount": 604.6,
  "remaining_balance": 697.4,
  "can_proceed": true
}
```

**Insufficient Balance Response:**
```json
{
  "status": "Wallet Verified Successfully",
  "account_details": {
    "name": "Pathlog User",
    "phone": "+91 8677939971",
    "pathlog_id": "PL939971"
  },
  "available_balance": 100.0,
  "payment_amount": 604.6,
  "remaining_balance": -504.6,
  "can_proceed": false,
  "error": "Insufficient wallet balance"
}
```

**Invalid OTP Response:**
```json
{
  "error": "Invalid OTP"
}
```

### Step 4: Process Pathlog Wallet Payment

**Endpoint:** `POST /api/payments/pathlog-wallet/pay/`

**Payload:**
```json
{
  "payment_id": 3
}
```

**Success Response:**
```json
{
  "status": "Payment Successful",
  "message": "Payment successful. Order created: #202508250003",
  "transaction_id": "TXNABC123DEF456",
  "order_created": true,
  "order": {
    "id": 3,
    "order_number": "202508250003",
    "status": "pending",
    "payment_status": "paid",
    "total": "517.00",
    "items_count": 1
  },
  "payment": {
    "id": 3,
    "status": "successful",
    "amount": "604.60",
    "method": "pathlog_wallet",
    "transaction_id": "TXNABC123DEF456"
  }
}
```

**Error Responses:**
```json
// Wallet not verified
{
  "error": "Wallet not verified"
}

// Insufficient balance
{
  "error": "Insufficient wallet balance"
}

// Payment not found
{
  "error": "Payment not found"
}
```

---

## 🔄 Complete Flow Examples

### Razorpay Flow:
```
1. POST /api/payments/create-from-cart/ (payment_method: "razorpay")
2. Frontend Razorpay integration
3. POST /api/payments/confirm-razorpay/ (with razorpay response)
4. Order automatically created ✅
```

### COD Flow:
```
1. POST /api/payments/create-from-cart/ (payment_method: "cod")
2. POST /api/payments/confirm-cod/ (payment_id)
3. Order automatically created ✅
```

### Pathlog Wallet Flow:
```
1. POST /api/payments/create-from-cart/ (payment_method: "pathlog_wallet")
2. POST /api/payments/pathlog-wallet/verify/ (mobile_number)
3. POST /api/payments/pathlog-wallet/otp/ (otp)
4. POST /api/payments/pathlog-wallet/pay/ (payment_id)
5. Order automatically created ✅
```

---

## 📊 Payment Calculation

All payments include these calculations:

```json
{
  "subtotal": 470.0,      // Sum of all cart items
  "tax": 84.6,            // 18% GST on subtotal
  "shipping": 50.0,       // Fixed shipping charge
  "discount": 0.0,        // Applied coupons/discounts
  "total": 604.6          // subtotal + tax + shipping - discount
}
```

---

## 🏠 Address Management

### Address Fields:
- `full_name` (required)
- `address_line_1` (required)
- `address_line_2` (optional)
- `city` (required)
- `state` (required)
- `postal_code` (required)
- `country` (required)

### Address Persistence:
- Address is automatically saved to user profile during payment creation
- Billing address = Shipping address (unified approach)
- Address is reused for future orders

---

## 📦 Order Auto-Creation

### Order Generation:
- Orders are automatically created after successful payment
- Order number format: `YYYYMMDDXXXX` (e.g., 202508250001)
- Cart items are cleared after order creation
- User address is saved to profile

### Order Status Mapping:
| Payment Method | Order Status | Payment Status |
|---------------|--------------|----------------|
| Razorpay | pending | paid |
| COD | pending | pending |
| Pathlog Wallet | pending | paid |

---

## 🛡️ Security Features

### Authentication:
- JWT token required for all endpoints
- User-specific payment access
- Payment isolation per user

### Pathlog Wallet Security:
- Mobile number validation
- OTP verification (demo: 123456)
- Balance verification before payment
- Transaction ID generation
- Wallet balance management

### Razorpay Security:
- Signature verification
- Order validation
- Payment verification

---

## ⚠️ Error Handling

### Common HTTP Status Codes:
- `200` - Success
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid/missing token)
- `404` - Not Found (payment/order not found)
- `500` - Internal Server Error

### Common Error Formats:
```json
// Validation Error
{
  "field_name": ["This field is required."]
}

// Authentication Error
{
  "detail": "Authentication credentials were not provided."
}

// Custom Error
{
  "error": "Insufficient wallet balance"
}
```

---

## 🧪 Testing with cURL

### 1. Test COD Flow:

```bash
# Step 1: Create COD Payment
curl -X POST http://localhost:8000/api/payments/create-from-cart/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_method": "cod",
    "shipping_address": {
      "full_name": "Test User",
      "address_line_1": "123 Test Street",
      "city": "Test City",
      "state": "Test State",
      "postal_code": "123456",
      "country": "India"
    }
  }'

# Step 2: Confirm COD
curl -X POST http://localhost:8000/api/payments/confirm-cod/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_id": 1
  }'
```

### 2. Test Pathlog Wallet Flow:

```bash
# Step 1: Create Pathlog Wallet Payment
curl -X POST http://localhost:8000/api/payments/create-from-cart/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_method": "pathlog_wallet",
    "shipping_address": {
      "full_name": "Wallet User",
      "address_line_1": "456 Wallet Street",
      "city": "Wallet City",
      "state": "Wallet State",
      "postal_code": "654321",
      "country": "India"
    }
  }'

# Step 2: Verify Mobile
curl -X POST http://localhost:8000/api/payments/pathlog-wallet/verify/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_id": 1,
    "mobile_number": "8677939971"
  }'

# Step 3: Verify OTP
curl -X POST http://localhost:8000/api/payments/pathlog-wallet/otp/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_id": 1,
    "otp": "123456"
  }'

# Step 4: Process Payment
curl -X POST http://localhost:8000/api/payments/pathlog-wallet/pay/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_id": 1
  }'
```

---

## 🚀 Environment Setup

### Required Environment Variables:
```bash
# Razorpay
RAZORPAY_API_KEY=rzp_test_xxxxxxxx
RAZORPAY_API_SECRET=xxxxxxxx

# Django
SECRET_KEY=your_secret_key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

### URLs Configuration:
```python
# ecommerce/urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/cart/', include('cart.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/orders/', include('orders.urls')),
]
```

---

## 📋 Quick Reference

### All Payment Endpoints:
```
POST /api/payments/create-from-cart/           # Universal payment creation
POST /api/payments/confirm-razorpay/           # Confirm Razorpay payment
POST /api/payments/confirm-cod/                # Confirm COD payment
POST /api/payments/pathlog-wallet/verify/      # Verify mobile number
POST /api/payments/pathlog-wallet/otp/         # Verify OTP
POST /api/payments/pathlog-wallet/pay/         # Process wallet payment
```

### Payment Methods:
- `"razorpay"` - Online payment
- `"cod"` - Cash on delivery
- `"pathlog_wallet"` - Wallet payment

### Demo Credentials:
- **Pathlog Wallet OTP:** `123456`
- **Demo Balance:** `₹1302.00`

---

## 🔮 Future Enhancements

### Planned Features:
- Real Pathlog API integration
- Multiple payment methods per order
- Partial payments
- Payment retry mechanism
- Refund processing
- Webhook integration
- Transaction history

---

**Last Updated:** August 25, 2025  
**Version:** 1.0  
**Status:** Production Ready ✅