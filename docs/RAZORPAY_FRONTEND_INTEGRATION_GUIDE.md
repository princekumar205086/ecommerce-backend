# Razorpay Payment Integration - Complete Frontend Guide

## Overview
This guide provides comprehensive documentation for integrating Razorpay payments with the fixed checkout system. All issues related to cart creation and order processing have been resolved.

## 🔧 Recent Fixes Applied

### 1. Cart Auto-Creation
- **Issue**: "No active cart found" error for new users
- **Fix**: Automatic cart creation when users access checkout
- **Behavior**: System now creates empty cart and provides helpful error message

### 2. Empty Cart Handling  
- **Issue**: Users with empty carts couldn't proceed to checkout
- **Fix**: Clear error messages and cart ID provided for troubleshooting
- **Behavior**: Informative error with guidance to add items first

### 3. Order Creation Reliability
- **Issue**: "Payment successful but order creation failed"
- **Fix**: Enhanced error logging and improved cart data validation
- **Behavior**: Robust order creation with detailed error tracking

## 🚀 Complete Payment Flow

### Step 1: Authentication & Cart Setup

```javascript
// Authenticate user
const loginResponse = await fetch('/api/token/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        email: 'user@example.com',
        password: 'password123'
    })
});

const { access: token } = await loginResponse.json();

// Check/create cart (automatic cart creation if needed)
const cartResponse = await fetch('/api/cart/', {
    headers: { 'Authorization': `Bearer ${token}` }
});

const cartData = await cartResponse.json();
console.log(`Cart has ${cartData.items.length} items`);
```

### Step 2: Add Items to Cart (if empty)

```javascript
// Add item to cart if empty
if (cartData.items.length === 0) {
    const addResponse = await fetch('/api/cart/add/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            product_id: 123,
            variant_id: 456,  // Optional
            quantity: 2
        })
    });
    
    if (!addResponse.ok) {
        const error = await addResponse.json();
        console.error('Failed to add item:', error);
        return;
    }
}
```

### Step 3: Create Razorpay Payment

```javascript
async function createRazorpayPayment() {
    const paymentData = {
        payment_method: 'razorpay',
        shipping_address: {
            full_name: 'John Doe',
            address_line_1: '123 Main Street',
            city: 'Mumbai',
            state: 'Maharashtra',
            postal_code: '400001',
            country: 'India',
            phone: '+91-9876543210'
        },
        billing_address: {
            full_name: 'John Doe',
            address_line_1: '123 Main Street', 
            city: 'Mumbai',
            state: 'Maharashtra',
            postal_code: '400001',
            country: 'India',
            phone: '+91-9876543210'
        },
        currency: 'INR'
    };
    
    try {
        const response = await fetch('/api/payments/create-from-cart/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(paymentData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            
            // Handle specific errors
            if (error.error && error.error.includes('Cart is empty')) {
                alert('Please add items to your cart before checkout');
                window.location.href = '/products';
                return null;
            }
            
            throw new Error(error.error || 'Payment creation failed');
        }
        
        const paymentResult = await response.json();
        console.log('Payment created:', paymentResult);
        return paymentResult;
        
    } catch (error) {
        console.error('Payment creation error:', error);
        alert(`Payment creation failed: ${error.message}`);
        return null;
    }
}
```

### Step 4: Launch Razorpay Checkout

```javascript
function launchRazorpay(paymentData) {
    const options = {
        key: paymentData.razorpay_key,
        amount: paymentData.amount * 100, // Convert to paise
        currency: paymentData.currency,
        order_id: paymentData.razorpay_order_id,
        name: 'Your Store Name',
        description: 'Purchase from Your Store',
        image: '/logo.png', // Your logo
        prefill: {
            name: 'Customer Name',
            email: 'customer@example.com',
            contact: '+919876543210'
        },
        theme: {
            color: '#3399cc'
        },
        handler: function(response) {
            // Payment successful - confirm with backend
            confirmPayment(paymentData.payment_id, response);
        },
        modal: {
            ondismiss: function() {
                console.log('Payment cancelled by user');
                alert('Payment was cancelled');
            }
        }
    };
    
    const rzp = new Razorpay(options);
    rzp.open();
}
```

### Step 5: Confirm Payment with Backend

```javascript
async function confirmPayment(paymentId, razorpayResponse) {
    const confirmData = {
        payment_id: paymentId,
        razorpay_order_id: razorpayResponse.razorpay_order_id,
        razorpay_payment_id: razorpayResponse.razorpay_payment_id,
        razorpay_signature: razorpayResponse.razorpay_signature
    };
    
    try {
        const response = await fetch('/api/payments/confirm-razorpay/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(confirmData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            if (result.order_created) {
                // Success! Order created automatically
                alert(`Payment successful! Order #${result.order_number} created.`);
                
                // Redirect to success page
                window.location.href = `/order-success/${result.order_number}`;
            } else {
                // Payment successful but order creation failed
                alert('Payment successful but there was an issue creating your order. Please contact support.');
                console.error('Order creation failed:', result);
            }
        } else {
            // Payment verification failed
            alert('Payment verification failed. Please contact support if amount was deducted.');
            console.error('Payment verification failed:', result);
        }
        
    } catch (error) {
        console.error('Payment confirmation error:', error);
        alert('Payment confirmation failed. Please contact support if amount was deducted.');
    }
}
```

### Complete Integration Example

```javascript
class RazorpayCheckout {
    constructor(authToken) {
        this.token = authToken;
        this.baseUrl = '/api';
    }
    
    async startCheckout() {
        try {
            // Step 1: Verify cart has items
            const cart = await this.getCart();
            if (!cart || cart.items.length === 0) {
                alert('Please add items to your cart first');
                return;
            }
            
            // Step 2: Create payment
            const paymentData = await this.createPayment();
            if (!paymentData) return;
            
            // Step 3: Launch Razorpay
            this.launchRazorpay(paymentData);
            
        } catch (error) {
            console.error('Checkout error:', error);
            alert('Checkout failed. Please try again.');
        }
    }
    
    async getCart() {
        const response = await fetch(`${this.baseUrl}/cart/`, {
            headers: { 'Authorization': `Bearer ${this.token}` }
        });
        
        if (response.ok) {
            return await response.json();
        }
        return null;
    }
    
    async createPayment() {
        // Get addresses from form or user profile
        const addresses = this.getAddressData();
        
        const paymentData = {
            payment_method: 'razorpay',
            shipping_address: addresses.shipping,
            billing_address: addresses.billing,
            currency: 'INR'
        };
        
        const response = await fetch(`${this.baseUrl}/payments/create-from-cart/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(paymentData)
        });
        
        if (response.ok) {
            return await response.json();
        } else {
            const error = await response.json();
            throw new Error(error.error || 'Payment creation failed');
        }
    }
    
    launchRazorpay(paymentData) {
        const options = {
            key: paymentData.razorpay_key,
            amount: paymentData.amount * 100,
            currency: paymentData.currency,
            order_id: paymentData.razorpay_order_id,
            name: 'Your Store',
            description: 'Online Purchase',
            handler: (response) => {
                this.confirmPayment(paymentData.payment_id, response);
            },
            modal: {
                ondismiss: () => {
                    console.log('Payment dismissed');
                }
            }
        };
        
        const rzp = new Razorpay(options);
        rzp.open();
    }
    
    async confirmPayment(paymentId, razorpayResponse) {
        const confirmData = {
            payment_id: paymentId,
            razorpay_order_id: razorpayResponse.razorpay_order_id,
            razorpay_payment_id: razorpayResponse.razorpay_payment_id,
            razorpay_signature: razorpayResponse.razorpay_signature
        };
        
        const response = await fetch(`${this.baseUrl}/payments/confirm-razorpay/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(confirmData)
        });
        
        const result = await response.json();
        
        if (response.ok && result.order_created) {
            // Success
            window.location.href = `/order-success/${result.order_number}`;
        } else {
            // Handle error
            console.error('Payment confirmation failed:', result);
            alert('Payment confirmation failed');
        }
    }
    
    getAddressData() {
        // Return address data from form or stored data
        return {
            shipping: {
                full_name: document.getElementById('shipping_name').value,
                address_line_1: document.getElementById('shipping_address').value,
                city: document.getElementById('shipping_city').value,
                state: document.getElementById('shipping_state').value,
                postal_code: document.getElementById('shipping_postal').value,
                country: 'India',
                phone: document.getElementById('shipping_phone').value
            },
            billing: {
                full_name: document.getElementById('billing_name').value,
                address_line_1: document.getElementById('billing_address').value,
                city: document.getElementById('billing_city').value,
                state: document.getElementById('billing_state').value,
                postal_code: document.getElementById('billing_postal').value,
                country: 'India',
                phone: document.getElementById('billing_phone').value
            }
        };
    }
}

// Usage
const checkout = new RazorpayCheckout(userToken);
document.getElementById('checkout-btn').onclick = () => checkout.startCheckout();
```

## 🎯 API Endpoints Reference

### Payment Creation
- **Endpoint**: `POST /api/payments/create-from-cart/`
- **Headers**: `Authorization: Bearer <token>`
- **Success**: `200 OK` with payment details
- **Errors**: 
  - `400` - Cart is empty
  - `401` - Unauthorized
  - `500` - Server error

### Payment Confirmation  
- **Endpoint**: `POST /api/payments/confirm-razorpay/`
- **Headers**: `Authorization: Bearer <token>`
- **Success**: `200 OK` with order details
- **Errors**:
  - `400` - Verification failed or order creation failed
  - `404` - Payment not found
  - `500` - Server error

### Cart Management
- **Get Cart**: `GET /api/cart/` (auto-creates if needed)
- **Add Item**: `POST /api/cart/add/`
- **Clear Cart**: `DELETE /api/cart/clear/`

## 🚨 Error Handling

### Common Error Scenarios

1. **Empty Cart Error**
   ```json
   {
     "error": "Cart is empty. Please add items to cart before checkout.",
     "cart_id": 123
   }
   ```
   **Solution**: Redirect user to products page

2. **Payment Verification Failed**
   ```json
   {
     "error": "Payment verification failed"
   }
   ```
   **Solution**: Show support contact information

3. **Order Creation Failed**
   ```json
   {
     "status": "Payment successful but order creation failed",
     "order_created": false
   }
   ```
   **Solution**: Contact support with payment ID

## 🧪 Testing

### Test Users
- **user@example.com** / User@123 ✅ Working
- **programmar.prince@gmail.com** / Prince@123 ✅ Working

### Test Flow
1. Authenticate with test user
2. Add items to cart
3. Create Razorpay payment
4. Use test payment details:
   - **Card**: 4111 1111 1111 1111
   - **Expiry**: Any future date
   - **CVV**: Any 3 digits

## 🔒 Security Considerations

1. **Never expose Razorpay secret key on frontend**
2. **Always verify payments on backend**
3. **Use HTTPS in production**
4. **Validate all user inputs**
5. **Implement proper error logging**

## 🎉 Production Checklist

- ✅ Cart auto-creation implemented
- ✅ Empty cart handling added
- ✅ Payment verification working
- ✅ Order creation from cart working
- ✅ Error handling comprehensive
- ✅ Multiple user testing completed
- ✅ Frontend integration documented

## 🆘 Support & Troubleshooting

### If payments fail:
1. Check browser console for errors
2. Verify authentication token is valid
3. Ensure cart has items before checkout
4. Check network connectivity
5. Verify Razorpay key configuration

### Contact Information
- **Technical Support**: Check server logs for detailed error messages
- **Payment Issues**: Use payment ID for tracking
- **Order Issues**: Reference order number from confirmation

---

*Last Updated: October 15, 2025*  
*Version: 2.0 (Post-Fix)*