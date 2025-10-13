# Pathlog Wallet Frontend Integration Guide

## Overview
This guide provides comprehensive documentation for integrating Pathlog Wallet payment method into your frontend application. The Pathlog Wallet system supports cart-first payment flow with order creation after successful payment.

## Table of Contents
- [Authentication](#authentication)
- [Cart Management](#cart-management)
- [Payment Flow](#payment-flow)
- [Pathlog Wallet Specific Endpoints](#pathlog-wallet-specific-endpoints)
- [Error Handling](#error-handling)
- [Testing](#testing)
- [Production Considerations](#production-considerations)

## Authentication

### JWT Token
All API requests require JWT authentication.

**Endpoint:** `POST /api/token/`

**Request:**
```json
{
    "email": "user@example.com",
    "password": "password123"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Headers for all subsequent requests:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json
```

## Cart Management

### Get Cart
**Endpoint:** `GET /api/cart/`

**Response:**
```json
{
    "id": 3,
    "user": 1,
    "items": [
        {
            "id": 15,
            "product": {
                "id": 519,
                "name": "Urine Test Strips 2025",
                "price": "89.99"
            },
            "variant": {
                "id": 551,
                "price": "89.99",
                "attributes": "Color: Blue, Size: XL"
            },
            "quantity": 2,
            "total_price": "179.98"
        }
    ],
    "total_price": "179.98",
    "total_items": 2,
    "created_at": "2025-10-13T10:30:00Z",
    "updated_at": "2025-10-13T10:35:00Z"
}
```

### Add Item to Cart
**Endpoint:** `POST /api/cart/add/`

**Request:**
```json
{
    "product_id": 519,
    "variant_id": 551,  // Optional
    "quantity": 2
}
```

**Response:**
```json
{
    "message": "Item added to cart",
    "cart_item": {
        "id": 15,
        "product_id": 519,
        "variant_id": 551,
        "quantity": 2,
        "total_price": "179.98"
    }
}
```

### Clear Cart
**Endpoint:** `DELETE /api/cart/clear/`

**Response:**
```json
{
    "message": "Cart cleared successfully"
}
```

## Payment Flow

### Step 1: Create Pathlog Wallet Payment
**Endpoint:** `POST /api/payments/create/`

**Request:**
```json
{
    "amount": 179.98,
    "currency": "INR",
    "payment_method": "pathlog_wallet",
    "cart_data": {
        "cart_id": 3,
        "total_price": 179.98,
        "items": [
            {
                "product_id": 519,
                "product_name": "Urine Test Strips 2025",
                "variant_id": 551,
                "variant_name": "Color: Blue, Size: XL",
                "quantity": 2,
                "price": 89.99,
                "total": 179.98
            }
        ]
    },
    "shipping_address": {
        "name": "John Doe",
        "phone": "+919876543210",
        "address": "123 Main Street, Apartment 4B",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400001"
    },
    "billing_address": {
        "name": "John Doe",
        "phone": "+919876543210",
        "address": "123 Main Street, Apartment 4B",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400001"
    },
    "coupon_code": "MEDIXMALL10"  // Optional
}
```

**Response:**
```json
{
    "payment_id": 29,
    "status": "pending",
    "amount": 179.98,
    "currency": "INR",
    "payment_method": "pathlog_wallet",
    "created_at": "2025-10-13T10:40:00Z",
    "message": "Pathlog Wallet payment created successfully"
}
```

### Step 2: Verify Pathlog Wallet
**Endpoint:** `POST /api/payments/pathlog/verify/`

**Request:**
```json
{
    "payment_id": 29,
    "mobile_number": "+919876543210",
    "otp": "123456"
}
```

**Response - Success:**
```json
{
    "success": true,
    "message": "Wallet verified successfully",
    "wallet_balance": 1302.00,
    "mobile_number": "+919876543210",
    "verified_at": "2025-10-13T10:41:00Z"
}
```

**Response - Error:**
```json
{
    "success": false,
    "message": "Invalid OTP",
    "error_code": "INVALID_OTP"
}
```

### Step 3: Process Pathlog Wallet Payment
**Endpoint:** `POST /api/payments/pathlog/process/`

**Request:**
```json
{
    "payment_id": 29
}
```

**Response - Success:**
```json
{
    "success": true,
    "message": "Payment successful. Order created: #202510130006",
    "payment_status": "successful",
    "transaction_id": "TXN292BC3BF2004",
    "order_number": "202510130006",
    "remaining_balance": 1122.02,
    "order": {
        "id": 123,
        "order_number": "202510130006",
        "total": 197.98,
        "payment_status": "paid",
        "status": "confirmed",
        "coupon_applied": "MEDIXMALL10",
        "coupon_discount": 17.98,
        "items": [
            {
                "product_name": "Urine Test Strips 2025",
                "quantity": 2,
                "price": 89.99,
                "total": 179.98
            }
        ]
    }
}
```

**Response - Insufficient Balance:**
```json
{
    "success": false,
    "message": "Insufficient wallet balance",
    "error_code": "INSUFFICIENT_BALANCE",
    "required_amount": 179.98,
    "available_balance": 150.00
}
```

## Pathlog Wallet Specific Endpoints

### Get Wallet Balance
**Endpoint:** `GET /api/payments/pathlog/balance/{payment_id}/`

**Response:**
```json
{
    "wallet_balance": 1302.00,
    "mobile_number": "+919876543210",
    "is_verified": true,
    "last_updated": "2025-10-13T10:41:00Z"
}
```

### Send OTP for Wallet Verification
**Endpoint:** `POST /api/payments/pathlog/send-otp/`

**Request:**
```json
{
    "mobile_number": "+919876543210"
}
```

**Response:**
```json
{
    "success": true,
    "message": "OTP sent successfully",
    "otp_sent_at": "2025-10-13T10:40:30Z",
    "expires_in": 300
}
```

## Error Handling

### Common Error Responses

**Authentication Error (401):**
```json
{
    "detail": "Given token not valid for any token type",
    "code": "token_not_valid",
    "messages": [
        {
            "token_class": "AccessToken",
            "token_type": "access",
            "message": "Token is invalid or expired"
        }
    ]
}
```

**Validation Error (400):**
```json
{
    "amount": ["This field is required."],
    "payment_method": ["Invalid choice: 'invalid_method'"]
}
```

**Insufficient Balance (400):**
```json
{
    "success": false,
    "message": "Insufficient wallet balance",
    "error_code": "INSUFFICIENT_BALANCE",
    "required_amount": 179.98,
    "available_balance": 150.00
}
```

**Wallet Not Verified (400):**
```json
{
    "success": false,
    "message": "Wallet not verified",
    "error_code": "WALLET_NOT_VERIFIED"
}
```

**Invalid OTP (400):**
```json
{
    "success": false,
    "message": "Invalid OTP",
    "error_code": "INVALID_OTP"
}
```

**Payment Not Found (404):**
```json
{
    "detail": "Payment not found",
    "error_code": "PAYMENT_NOT_FOUND"
}
```

### Error Handling Best Practices

1. **Always check response status codes**
2. **Handle network errors gracefully**
3. **Implement retry logic for temporary failures**
4. **Show user-friendly error messages**
5. **Log errors for debugging**

```javascript
// Example error handling in JavaScript
async function processPathlogPayment(paymentId) {
    try {
        const response = await fetch('/api/payments/pathlog/process/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ payment_id: paymentId })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            switch (data.error_code) {
                case 'INSUFFICIENT_BALANCE':
                    showError(`Insufficient balance. Required: ₹${data.required_amount}, Available: ₹${data.available_balance}`);
                    break;
                case 'WALLET_NOT_VERIFIED':
                    redirectToVerification();
                    break;
                default:
                    showError(data.message || 'Payment failed');
            }
            return null;
        }
        
        return data;
    } catch (error) {
        console.error('Network error:', error);
        showError('Network error. Please check your connection.');
        return null;
    }
}
```

## Testing

### Test Environment Setup
- **Base URL:** `http://127.0.0.1:8000/api`
- **Test User:** `user@example.com` / `User@123`
- **Test Mobile:** `+919876543210`
- **Test OTP:** `123456`
- **Test Balance:** `₹1302.00`

### Test Scenarios

#### 1. Successful Payment Flow
```javascript
// Test data
const testPayment = {
    amount: 179.98,
    payment_method: 'pathlog_wallet',
    cart_data: { /* cart data */ },
    shipping_address: { /* address */ },
    billing_address: { /* address */ },
    coupon_code: 'MEDIXMALL10'
};

// Steps
1. Create payment → expect payment_id
2. Verify wallet → expect success: true
3. Process payment → expect order_number
```

#### 2. Insufficient Balance
```javascript
const testPayment = {
    amount: 2000.00,  // More than available balance
    // ... other fields
};

// Expected response
{
    "success": false,
    "error_code": "INSUFFICIENT_BALANCE"
}
```

#### 3. Invalid OTP
```javascript
const verifyData = {
    payment_id: 29,
    mobile_number: "+919876543210",
    otp: "wrong-otp"
};

// Expected response
{
    "success": false,
    "error_code": "INVALID_OTP"
}
```

## Production Considerations

### Security
1. **Always use HTTPS in production**
2. **Validate all input data**
3. **Implement rate limiting for OTP requests**
4. **Use secure storage for JWT tokens**
5. **Implement CSRF protection**

### Performance
1. **Cache wallet balance when possible**
2. **Implement request timeouts**
3. **Use optimistic UI updates**
4. **Implement proper loading states**

### Monitoring
1. **Track payment success/failure rates**
2. **Monitor API response times**
3. **Log failed transactions for analysis**
4. **Set up alerts for unusual activity**

### Integration Example

```javascript
class PathlogWalletIntegration {
    constructor(baseUrl, token) {
        this.baseUrl = baseUrl;
        this.token = token;
    }
    
    async createPayment(paymentData) {
        const response = await this.makeRequest('POST', '/payments/create/', paymentData);
        return response;
    }
    
    async verifyWallet(paymentId, mobileNumber, otp) {
        const response = await this.makeRequest('POST', '/payments/pathlog/verify/', {
            payment_id: paymentId,
            mobile_number: mobileNumber,
            otp: otp
        });
        return response;
    }
    
    async processPayment(paymentId) {
        const response = await this.makeRequest('POST', '/payments/pathlog/process/', {
            payment_id: paymentId
        });
        return response;
    }
    
    async makeRequest(method, endpoint, data = null) {
        const config = {
            method,
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            }
        };
        
        if (data) {
            config.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, config);
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.message || 'Request failed');
            }
            
            return result;
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }
}

// Usage
const pathlogWallet = new PathlogWalletIntegration('https://api.example.com/api', userToken);

async function handlePathlogPayment(cartData, addresses, couponCode) {
    try {
        // Step 1: Create payment
        const payment = await pathlogWallet.createPayment({
            amount: cartData.total,
            payment_method: 'pathlog_wallet',
            cart_data: cartData,
            shipping_address: addresses.shipping,
            billing_address: addresses.billing,
            coupon_code: couponCode
        });
        
        // Step 2: Verify wallet
        const otp = await promptForOTP();
        const verification = await pathlogWallet.verifyWallet(
            payment.payment_id,
            addresses.shipping.phone,
            otp
        );
        
        if (!verification.success) {
            throw new Error(verification.message);
        }
        
        // Step 3: Process payment
        const result = await pathlogWallet.processPayment(payment.payment_id);
        
        if (result.success) {
            // Redirect to success page
            window.location.href = `/order-success/${result.order_number}`;
        } else {
            throw new Error(result.message);
        }
        
    } catch (error) {
        console.error('Payment failed:', error);
        showErrorMessage(error.message);
    }
}
```

## Support and Troubleshooting

### Common Issues

1. **"Wallet not verified" error**
   - Ensure OTP verification was successful
   - Check if verification timeout expired

2. **"Insufficient balance" error**
   - Check wallet balance before processing
   - Handle gracefully with top-up options

3. **"Payment not found" error**
   - Verify payment_id is correct
   - Check if payment was already processed

4. **Network timeouts**
   - Implement retry logic
   - Show appropriate loading states


*This documentation is for Pathlog Wallet integration version 1.0. Last updated: October 13, 2025*