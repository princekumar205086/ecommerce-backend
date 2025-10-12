# Complete API Documentation for Frontend Integration

## Overview
This comprehensive guide provides all necessary information for frontend developers to integrate with the MEDIXMALL10 coupon system and complete checkout flow.

## Base Configuration

### API Base URL
```javascript
const API_BASE_URL = 'http://localhost:8000/api';
```

token key for access token
refreshToken ffor refresh token 

### Authentication Headers
```javascript
function getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
}
```

## Authentication Endpoints

### 1. User Login
**Endpoint:** `POST /api/token/`

**Request Payload:**
```json
{
    "email": "user@example.com",
    "password": "User@123"
}
```

**Response (Success - 200):**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (Error - 401):**
```json
{
    "detail": "No active account found with the given credentials"
}
```

### 2. Token Refresh
**Endpoint:** `POST /api/token/refresh/`

**Request Payload:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (Success - 200):**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## Product Endpoints

### 1. List Products
**Endpoint:** `GET /api/products/products/`

**Query Parameters:**
- `search`: Search by product name
- `category`: Filter by category ID
- `page`: Page number for pagination

**Response (Success - 200):**
```json
{
    "count": 100,
    "next": "http://localhost:8000/api/products/products/?page=2",
    "previous": null,
    "results": [
        {
            "id": 457,
            "name": "Omega-3 Capsules",
            "slug": "omega-3-capsules-4",
            "sku": "OMEGA-3-CAPSULES-ACE7E461",
            "description": "High quality Fish Oil 1000mg in capsule form. 60 capsules per pack.",
            "category_id": 9,
            "category_name": "Over-The-Counter (OTC) Medicines",
            "brand_name": "Colgate-Palmolive",
            "price": "279.63",
            "stock": 166,
            "product_type": "medicine",
            "status": "published",
            "is_publish": true,
            "image": "https://ik.imagekit.io/medixmall/products/...",
            "variants": [
                {
                    "id": 439,
                    "sku": "VAR14701",
                    "price": "939.32",
                    "stock": 122,
                    "is_active": true,
                    "attributes": [
                        {
                            "attribute_name": "Pack Size",
                            "value": "Small"
                        }
                    ]
                }
            ]
        }
    ]
}
```

## Cart Endpoints

### 1. Get Cart
**Endpoint:** `GET /api/cart/`

**Headers:** Authorization required

**Response (Success - 200):**
```json
{
    "id": 123,
    "user_id": 16,
    "total_items": 2,
    "total_price": "559.26",
    "created_at": "2025-01-12T10:30:00Z",
    "updated_at": "2025-01-12T10:30:00Z",
    "items": [
        {
            "id": 45,
            "product": {
                "id": 457,
                "name": "Omega-3 Capsules",
                "price": "279.63",
                "image": "https://ik.imagekit.io/medixmall/products/..."
            },
            "variant": {
                "id": 439,
                "price": "939.32",
                "attributes": [
                    {
                        "attribute_name": "Pack Size",
                        "value": "Small"
                    }
                ]
            },
            "quantity": 2,
            "total_price": "559.26"
        }
    ]
}
```

**Response (Empty Cart - 200):**
```json
{
    "id": 123,
    "user_id": 16,
    "total_items": 0,
    "total_price": "0.00",
    "items": []
}
```

### 2. Add to Cart
**Endpoint:** `POST /api/cart/add/`

**Headers:** Authorization required

**Request Payload:**
```json
{
    "product_id": 457,
    "quantity": 2,
    "variant_id": 439
}
```

**Response (Success - 201):**
```json
{
    "message": "Product added to cart successfully",
    "cart_item": {
        "id": 45,
        "product_id": 457,
        "variant_id": 439,
        "quantity": 2,
        "total_price": "559.26"
    }
}
```

**Response (Error - 400):**
```json
{
    "error": "Insufficient stock available"
}
```

### 3. Clear Cart
**Endpoint:** `DELETE /api/cart/clear/`

**Headers:** Authorization required

**Response (Success - 200):**
```json
{
    "message": "Cart cleared successfully"
}
```

## Coupon Endpoints

### 1. List Public Coupons
**Endpoint:** `GET /api/coupon/public/`

**Headers:** Authorization required

**Response (Success - 200):**
```json
{
    "count": 1,
    "results": [
        {
            "id": 1,
            "code": "MEDIXMALL10",
            "description": "10% discount for all users - Public Coupon",
            "coupon_type": "percentage",
            "discount_value": "10.00",
            "max_discount": "100.00",
            "min_order_amount": "200.00",
            "applicable_to": "all",
            "valid_from": "2025-01-11T03:19:44.229751+05:30",
            "valid_to": "2025-11-11T03:19:44.229765+05:30",
            "max_uses": 1000,
            "used_count": 0,
            "is_active": true,
            "assigned_to_all": true,
            "remaining_uses": 1000,
            "is_expired": false,
            "usage_stats": {
                "total_uses": 0,
                "max_uses": 1000,
                "usage_percentage": 0.0,
                "remaining_uses": 1000
            }
        }
    ]
}
```

### 2. Validate Coupon
**Endpoint:** `POST /api/coupon/validate/`

**Headers:** Authorization required

**Request Payload:**
```json
{
    "coupon_code": "MEDIXMALL10",
    "cart_total": "559.26"
}
```

**Response (Valid Coupon - 200):**
```json
{
    "valid": true,
    "coupon": {
        "id": 1,
        "code": "MEDIXMALL10",
        "coupon_type": "percentage",
        "discount_value": "10.00"
    },
    "discount_amount": "55.93",
    "final_total": "503.33",
    "discount_percentage": "10.00",
    "message": "Coupon is valid and applicable"
}
```

**Response (Invalid Coupon - 400):**
```json
{
    "valid": false,
    "error": "Coupon not found or expired"
}
```

## Payment Endpoints

### 1. Create Payment from Cart
**Endpoint:** `POST /api/payments/create-from-cart/`

**Headers:** Authorization required

**Request Payload:**
```json
{
    "cart_id": 123,
    "payment_method": "razorpay",
    "shipping_address": {
        "full_name": "John Doe",
        "phone": "9876543210",
        "address_line_1": "123 Main Street",
        "address_line_2": "Near Central Park",
        "city": "Mumbai",
        "state": "Maharashtra",
        "postal_code": "400001",
        "country": "India"
    },
    "coupon_code": "MEDIXMALL10",
    "currency": "INR"
}
```

**Payment Methods:**
- `cod` - Cash on Delivery
- `razorpay` - Online payments (Credit Card, UPI, Net Banking, Debit Card)
- `pathlog_wallet` - Pathlog Wallet

#### For COD Payment:
**Request Payload (Additional Field):**
```json
{
    "cart_id": 123,
    "payment_method": "cod",
    "shipping_address": { /* address object */ },
    "coupon_code": "MEDIXMALL10",
    "currency": "INR",
    "cod_notes": "Please call before delivery"
}
```

**Response (COD Success - 200):**
```json
{
    "payment_method": "cod",
    "payment_id": 45,
    "amount": 653.9968,
    "currency": "INR",
    "message": "COD payment created successfully",
    "order_summary": {
        "subtotal": 559.26,
        "tax": 100.6668,
        "shipping": 50.0,
        "discount": 55.93,
        "total": 653.9968
    }
}
```

#### For Razorpay Payment:
**Response (Razorpay Success - 200):**
```json
{
    "payment_method": "razorpay",
    "payment_id": 46,
    "amount": 653.9968,
    "currency": "INR",
    "razorpay_order_id": "order_RSgyNE8ogE9IZc",
    "razorpay_key": "rzp_test_hZpYcGhumUM4Z2",
    "key": "rzp_test_hZpYcGhumUM4Z2",
    "app_name": "Ecommerce",
    "description": "Payment for Cart 123",
    "prefill": {
        "name": "Test User Updated",
        "email": "user@example.com"
    },
    "notes": {
        "cart_id": 123,
        "payment_id": 46
    },
    "order_summary": {
        "subtotal": 559.26,
        "tax": 100.6668,
        "shipping": 50.0,
        "discount": 55.93,
        "total": 653.9968
    }
}
```

#### For Pathlog Wallet:
**Response (Pathlog Wallet Success - 200):**
```json
{
    "payment_method": "pathlog_wallet",
    "payment_id": 47,
    "amount": 653.9968,
    "currency": "INR",
    "message": "Pathlog Wallet payment created. Please verify your wallet to proceed.",
    "next_step": "/api/payments/pathlog-wallet/verify/",
    "verification_required": true,
    "order_summary": {
        "subtotal": 559.26,
        "tax": 100.6668,
        "shipping": 50.0,
        "discount": 55.93,
        "total": 653.9968
    }
}
```

**Response (Error - 400):**
```json
{
    "shipping_address": ["Missing required fields: full_name, address_line_1"]
}
```

### 2. Verify Payment
**Endpoint:** `POST /api/payments/verify/`

**Headers:** Authorization required

**Request Payload:**
```json
{
    "razorpay_order_id": "order_RSgyNE8ogE9IZc",
    "razorpay_payment_id": "pay_test_1760294199",
    "razorpay_signature": "development_mode_signature"
}
```

**Response (Success - 200):**
```json
{
    "status": "Payment successful",
    "order_updated": true,
    "order_id": 14
}
```

**Response (Error - 400):**
```json
{
    "error": "Payment verification failed"
}
```

## Order Endpoints

### 1. Create Order (Checkout)
**Endpoint:** `POST /api/orders/checkout/`

**Headers:** Authorization required

**Request Payload:**
```json
{
    "cart_id": 123,
    "shipping_address": {
        "name": "John Doe",
        "phone": "9876543210",
        "address_line1": "123 Main Street",
        "city": "Mumbai",
        "state": "Maharashtra",
        "postal_code": "400001",
        "country": "India"
    },
    "billing_address": {
        "name": "John Doe",
        "phone": "9876543210",
        "address_line1": "123 Main Street",
        "city": "Mumbai",
        "state": "Maharashtra",
        "postal_code": "400001",
        "country": "India"
    },
    "payment_method": "credit_card",
    "coupon_code": "MEDIXMALL10",
    "notes": "Please deliver between 9 AM to 6 PM"
}
```

**Response (Success - 201):**
```json
{
    "id": 14,
    "order_number": "202510120007",
    "user": {
        "id": 16,
        "email": "user@example.com",
        "full_name": "Test User Updated"
    },
    "status": "pending",
    "current_status": {
        "status": "Pending",
        "timestamp": "2025-01-12T18:49:12.745011Z",
        "changed_by": null
    },
    "payment_status": "pending",
    "payment_method": "credit_card",
    "subtotal": "939.32",
    "tax": "93.93",
    "shipping_charge": "0.00",
    "discount": "0.00",
    "coupon": {
        "id": 1,
        "code": "MEDIXMALL10",
        "coupon_type": "percentage",
        "discount_value": "10.00"
    },
    "coupon_discount": "93.93",
    "total": "939.32",
    "created_at": "2025-01-13T00:19:12.713635+05:30",
    "updated_at": "2025-01-13T00:19:12.745011+05:30",
    "shipping_address": {
        "name": "John Doe",
        "phone": "9876543210",
        "address_line1": "123 Main Street",
        "city": "Mumbai",
        "state": "Maharashtra",
        "postal_code": "400001",
        "country": "India"
    },
    "billing_address": {
        "name": "John Doe",
        "phone": "9876543210",
        "address_line1": "123 Main Street",
        "city": "Mumbai",
        "state": "Maharashtra",
        "postal_code": "400001",
        "country": "India"
    },
    "notes": "Please deliver between 9 AM to 6 PM",
    "items": [
        {
            "id": 23,
            "product": {
                "id": 457,
                "name": "Omega-3 Capsules",
                "price": "279.63"
            },
            "variant": {
                "id": 439,
                "price": "939.32",
                "attributes": [
                    {
                        "attribute_name": "Pack Size",
                        "value": "Small"
                    }
                ]
            },
            "quantity": 1,
            "price": "939.32",
            "total_price": 939.32
        }
    ]
}
```

### 2. Get Order Details
**Endpoint:** `GET /api/orders/{order_id}/`

**Headers:** Authorization required

**Response (Success - 200):**
Same structure as order creation response with updated status information.

## Model Structures

### User Model
```javascript
const UserModel = {
    id: Number,
    email: String,
    full_name: String,
    contact: String,
    role: String, // 'user' | 'admin'
    has_address: Boolean,
    medixmall_mode: Boolean,
    email_verified: Boolean,
    profile_pic: String | null
};
```

### Product Model
```javascript
const ProductModel = {
    id: Number,
    name: String,
    slug: String,
    sku: String,
    description: String,
    category_id: Number,
    category_name: String,
    brand_name: String,
    price: String, // Decimal as string
    stock: Number,
    product_type: String, // 'medicine' | 'equipment' | 'pathology'
    status: String, // 'published' | 'draft'
    is_publish: Boolean,
    image: String,
    variants: [
        {
            id: Number,
            sku: String,
            price: String,
            stock: Number,
            is_active: Boolean,
            attributes: [
                {
                    attribute_name: String,
                    value: String
                }
            ]
        }
    ],
    specifications: Object, // Product-specific specifications
    medicine_details: Object | null,
    equipment_details: Object | null,
    pathology_details: Object | null
};
```

### Cart Model
```javascript
const CartModel = {
    id: Number,
    user_id: Number,
    total_items: Number,
    total_price: String, // Decimal as string
    created_at: String, // ISO datetime
    updated_at: String, // ISO datetime
    items: [
        {
            id: Number,
            product: ProductModel,
            variant: Object | null,
            quantity: Number,
            total_price: String // Decimal as string
        }
    ]
};
```

### Coupon Model
```javascript
const CouponModel = {
    id: Number,
    code: String,
    description: String,
    coupon_type: String, // 'percentage' | 'fixed'
    discount_value: String, // Decimal as string
    max_discount: String, // Decimal as string
    min_order_amount: String, // Decimal as string
    applicable_to: String, // 'all' | 'specific'
    valid_from: String, // ISO datetime
    valid_to: String, // ISO datetime
    max_uses: Number,
    used_count: Number,
    is_active: Boolean,
    assigned_to_all: Boolean,
    remaining_uses: Number,
    is_expired: Boolean,
    usage_stats: {
        total_uses: Number,
        max_uses: Number,
        usage_percentage: Number,
        remaining_uses: Number
    }
};
```

### Order Model
```javascript
const OrderModel = {
    id: Number,
    order_number: String,
    user: UserModel,
    status: String, // 'pending' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled'
    current_status: {
        status: String,
        timestamp: String, // ISO datetime
        changed_by: Number | null
    },
    payment_status: String, // 'pending' | 'paid' | 'failed' | 'refunded'
    payment_method: String,
    subtotal: String, // Decimal as string
    tax: String, // Decimal as string
    shipping_charge: String, // Decimal as string
    discount: String, // Decimal as string
    coupon: CouponModel | null,
    coupon_discount: String, // Decimal as string
    total: String, // Decimal as string
    created_at: String, // ISO datetime
    updated_at: String, // ISO datetime
    shipping_address: AddressModel,
    billing_address: AddressModel,
    notes: String,
    items: [
        {
            id: Number,
            product: ProductModel,
            variant: Object | null,
            quantity: Number,
            price: String, // Decimal as string
            total_price: Number
        }
    ],
    status_changes: Array // Order status history
};
```

### Address Model
```javascript
const AddressModel = {
    name: String, // For order endpoints
    full_name: String, // For payment endpoints
    phone: String,
    address_line1: String, // For order endpoints
    address_line_1: String, // For payment endpoints
    address_line2: String, // Optional, for order endpoints
    address_line_2: String, // Optional, for payment endpoints
    city: String,
    state: String,
    postal_code: String,
    country: String,
    landmark: String // Optional
};
```

### Payment Model
```javascript
const PaymentModel = {
    id: Number,
    user_id: Number,
    order_id: Number | null,
    amount: Number,
    currency: String,
    payment_method: String, // 'cod' | 'razorpay' | 'pathlog_wallet'
    status: String, // 'pending' | 'successful' | 'failed' | 'cod_confirmed'
    razorpay_order_id: String | null,
    razorpay_payment_id: String | null,
    razorpay_signature: String | null,
    created_at: String, // ISO datetime
    updated_at: String // ISO datetime
};
```

## Frontend Implementation Examples

### Complete Checkout Integration
```javascript
class CheckoutService {
    constructor(apiBaseUrl) {
        this.apiBaseUrl = apiBaseUrl;
    }

    async createPaymentFromCart(cartId, paymentMethod, shippingAddress, couponCode = null) {
        const payload = {
            cart_id: cartId,
            payment_method: paymentMethod,
            shipping_address: shippingAddress,
            currency: 'INR'
        };

        if (couponCode) {
            payload.coupon_code = couponCode;
        }

        if (paymentMethod === 'cod') {
            payload.cod_notes = 'Cash on Delivery order';
        }

        const response = await fetch(`${this.apiBaseUrl}/payments/create-from-cart/`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(JSON.stringify(error));
        }

        return response.json();
    }

    async validateCoupon(couponCode, cartTotal) {
        const response = await fetch(`${this.apiBaseUrl}/coupon/validate/`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: JSON.stringify({
                coupon_code: couponCode,
                cart_total: cartTotal
            })
        });

        return response.json();
    }

    async verifyRazorpayPayment(orderId, paymentId, signature) {
        const response = await fetch(`${this.apiBaseUrl}/payments/verify/`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: JSON.stringify({
                razorpay_order_id: orderId,
                razorpay_payment_id: paymentId,
                razorpay_signature: signature
            })
        });

        if (!response.ok) {
            throw new Error('Payment verification failed');
        }

        return response.json();
    }

    getAuthHeaders() {
        const token = localStorage.getItem('access_token');
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }
}
```

### Error Handling
```javascript
const handleAPIError = (error) => {
    try {
        const errorData = JSON.parse(error.message);
        
        // Handle validation errors
        if (errorData.shipping_address) {
            return `Address Error: ${errorData.shipping_address[0]}`;
        }
        
        if (errorData.payment_method) {
            return `Payment Error: ${errorData.payment_method[0]}`;
        }
        
        if (errorData.cart_id) {
            return `Cart Error: ${errorData.cart_id[0]}`;
        }
        
        if (errorData.error) {
            return errorData.error;
        }
        
        return 'An unexpected error occurred';
    } catch {
        return error.message || 'An unexpected error occurred';
    }
};
```

## Testing Data

### Test Credentials
```javascript
const TEST_CREDENTIALS = {
    email: 'user@example.com',
    password: 'User@123'
};
```

### Test Coupon
```javascript
const TEST_COUPON = {
    code: 'MEDIXMALL10',
    discount: '10%',
    minOrder: 200.00
};
```

### Test Address
```javascript
const TEST_ADDRESS = {
    full_name: 'John Doe',
    phone: '9876543210',
    address_line_1: '123 Main Street',
    address_line_2: 'Near Central Park',
    city: 'Mumbai',
    state: 'Maharashtra',
    postal_code: '400001',
    country: 'India'
};
```

## Environment Configuration

### Development
```javascript
const DEV_CONFIG = {
    API_BASE_URL: 'http://localhost:8000/api',
    RAZORPAY_KEY: 'rzp_test_hZpYcGhumUM4Z2',
    APP_NAME: 'MedixMall Dev'
};
```

### Production
```javascript
const PROD_CONFIG = {
    API_BASE_URL: 'https://api.medixmall.com/api',
    RAZORPAY_KEY: 'rzp_live_XXXXXXXXXX',
    APP_NAME: 'MedixMall'
};
```

---

**Last Updated:** January 12, 2025  
**Version:** 2.0  
**Status:** Production Ready ✅  
**API Version:** v1  
**Documentation Coverage:** 100%