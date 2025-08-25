# Complete Payment Documentation
## Razorpay, COD, and Pathlog Wallet Integration

### 🔐 Authentication
All payment endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

---

## 🏦 Razorpay Payment Flow

### Step 1: Create Payment from Cart
**Endpoint:** `POST /api/payments/create-from-cart/`

**Payload:**
```json
{
    "amount": "999.99",
    "currency": "INR",
    "method": "razorpay",
    "cart_id": 123  // Optional, will use user's active cart if not provided
}
```

**Response (Success - 201):**
```json
{
    "payment_id": "payment_uuid_here",
    "razorpay_order_id": "order_abc123",
    "amount": "999.99",
    "currency": "INR",
    "status": "pending",
    "razorpay_key": "rzp_test_your_key_here",
    "order_receipt": "receipt_order_abc123"
}
```

**Frontend Integration:**
```javascript
// Use the response to initialize Razorpay
const options = {
    key: response.razorpay_key,
    amount: parseFloat(response.amount) * 100, // Convert to paise
    currency: response.currency,
    order_id: response.razorpay_order_id,
    name: "Your Store Name",
    description: "Payment for order",
    handler: function(razorpayResponse) {
        // This function is called when payment is successful
        verifyPayment(response.payment_id, razorpayResponse);
    },
    prefill: {
        name: "Customer Name",
        email: "customer@example.com",
        contact: "9876543210"
    }
};

const rzp = new Razorpay(options);
rzp.open();
```

### Step 2: Verify Payment (After Razorpay Success)
**Endpoint:** `POST /api/payments/confirm-razorpay/`

**Payload:**
```json
{
    "payment_id": "payment_uuid_from_step1",
    "razorpay_payment_id": "pay_xyz789",
    "razorpay_signature": "signature_from_razorpay"
}
```

**Success Response (200):**
```json
{
    "status": "success",
    "message": "Payment verified successfully",
    "payment_id": "payment_uuid_here",
    "order_id": "order_123",
    "amount": "999.99"
}
```

**Error Response (400):**
```json
{
    "status": "error",
    "message": "Payment verification failed"
}
```

**Frontend Verification Function:**
```javascript
async function verifyPayment(paymentId, razorpayResponse) {
    try {
        const response = await fetch('/api/payments/confirm-razorpay/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                payment_id: paymentId,
                razorpay_payment_id: razorpayResponse.razorpay_payment_id,
                razorpay_signature: razorpayResponse.razorpay_signature
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Payment verified successfully
            window.location.href = '/payment-success';
        } else {
            // Payment verification failed
            alert('Payment verification failed');
        }
    } catch (error) {
        console.error('Error verifying payment:', error);
        alert('Error verifying payment');
    }
}
```

### Alternative Verification Endpoint
**Endpoint:** `POST /api/payments/verify/`

**Payload:**
```json
{
    "payment_id": "payment_uuid_here",
    "razorpay_payment_id": "pay_xyz789",
    "razorpay_signature": "signature_from_razorpay"
}
```

---

## 💰 Cash on Delivery (COD) Flow

### Step 1: Create COD Payment
**Endpoint:** `POST /api/payments/create-from-cart/`

**Payload:**
```json
{
    "amount": "999.99",
    "currency": "INR",
    "method": "cod",
    "cart_id": 123  // Optional
}
```

**Response (Success - 201):**
```json
{
    "payment_id": "payment_uuid_here",
    "amount": "999.99",
    "currency": "INR",
    "status": "pending",
    "method": "cod"
}
```

### Step 2: Confirm COD Payment
**Endpoint:** `POST /api/payments/confirm-cod/`

**Payload:**
```json
{
    "payment_id": "payment_uuid_from_step1"
}
```

**Success Response (200):**
```json
{
    "status": "success",
    "message": "COD payment confirmed",
    "payment_id": "payment_uuid_here",
    "order_id": "order_123"
}
```

---

## 💳 Pathlog Wallet Flow

### Step 1: Create Wallet Payment
**Endpoint:** `POST /api/payments/create-from-cart/`

**Payload:**
```json
{
    "amount": "999.99",
    "currency": "INR",
    "method": "pathlog_wallet",
    "cart_id": 123  // Optional
}
```

### Step 2: Request OTP
**Endpoint:** `POST /api/payments/pathlog-wallet/otp/`

**Payload:**
```json
{
    "payment_id": "payment_uuid_here",
    "phone": "9876543210"
}
```

**Response (200):**
```json
{
    "status": "success",
    "message": "OTP sent successfully",
    "otp_id": "otp_123456"
}
```

### Step 3: Verify OTP and Complete Payment
**Endpoint:** `POST /api/payments/pathlog-wallet/verify/`

**Payload:**
```json
{
    "payment_id": "payment_uuid_here",
    "otp_id": "otp_123456",
    "otp": "1234"
}
```

**Success Response (200):**
```json
{
    "status": "success",
    "message": "Payment completed successfully",
    "payment_id": "payment_uuid_here",
    "wallet_transaction_id": "txn_abc123"
}
```

### Alternative: Direct Wallet Payment
**Endpoint:** `POST /api/payments/pathlog-wallet/pay/`

**Payload:**
```json
{
    "payment_id": "payment_uuid_here",
    "wallet_id": "wallet_123",
    "pin": "1234"
}
```

---

## 📱 Complete Frontend Integration Example

```html
<!DOCTYPE html>
<html>
<head>
    <title>Payment Integration</title>
    <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
</head>
<body>
    <button onclick="initiateRazorpayPayment()">Pay with Razorpay</button>
    <button onclick="initiateCODPayment()">Cash on Delivery</button>
    <button onclick="initiateWalletPayment()">Pathlog Wallet</button>

    <script>
        const authToken = 'your_jwt_token_here';
        const baseURL = 'http://your-api-domain.com';

        async function initiateRazorpayPayment() {
            try {
                // Step 1: Create payment
                const response = await fetch(`${baseURL}/api/payments/create-from-cart/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${authToken}`
                    },
                    body: JSON.stringify({
                        amount: "999.99",
                        currency: "INR",
                        method: "razorpay"
                    })
                });

                const paymentData = await response.json();

                // Step 2: Initialize Razorpay
                const options = {
                    key: paymentData.razorpay_key,
                    amount: parseFloat(paymentData.amount) * 100,
                    currency: paymentData.currency,
                    order_id: paymentData.razorpay_order_id,
                    name: "Your Store",
                    description: "Payment for order",
                    handler: function(razorpayResponse) {
                        verifyRazorpayPayment(paymentData.payment_id, razorpayResponse);
                    }
                };

                const rzp = new Razorpay(options);
                rzp.open();
            } catch (error) {
                console.error('Error initiating payment:', error);
            }
        }

        async function verifyRazorpayPayment(paymentId, razorpayResponse) {
            try {
                const response = await fetch(`${baseURL}/api/payments/confirm-razorpay/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${authToken}`
                    },
                    body: JSON.stringify({
                        payment_id: paymentId,
                        razorpay_payment_id: razorpayResponse.razorpay_payment_id,
                        razorpay_signature: razorpayResponse.razorpay_signature
                    })
                });

                const result = await response.json();
                
                if (response.ok) {
                    alert('Payment successful!');
                    window.location.href = '/success';
                } else {
                    alert('Payment verification failed');
                }
            } catch (error) {
                console.error('Error verifying payment:', error);
            }
        }

        async function initiateCODPayment() {
            try {
                // Step 1: Create COD payment
                const response = await fetch(`${baseURL}/api/payments/create-from-cart/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${authToken}`
                    },
                    body: JSON.stringify({
                        amount: "999.99",
                        currency: "INR",
                        method: "cod"
                    })
                });

                const paymentData = await response.json();

                // Step 2: Confirm COD
                const confirmResponse = await fetch(`${baseURL}/api/payments/confirm-cod/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${authToken}`
                    },
                    body: JSON.stringify({
                        payment_id: paymentData.payment_id
                    })
                });

                if (confirmResponse.ok) {
                    alert('COD order placed successfully!');
                    window.location.href = '/success';
                }
            } catch (error) {
                console.error('Error with COD payment:', error);
            }
        }

        async function initiateWalletPayment() {
            try {
                // Step 1: Create wallet payment
                const response = await fetch(`${baseURL}/api/payments/create-from-cart/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${authToken}`
                    },
                    body: JSON.stringify({
                        amount: "999.99",
                        currency: "INR",
                        method: "pathlog_wallet"
                    })
                });

                const paymentData = await response.json();

                // Step 2: Request OTP
                const phone = prompt('Enter your phone number:');
                const otpResponse = await fetch(`${baseURL}/api/payments/pathlog-wallet/otp/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${authToken}`
                    },
                    body: JSON.stringify({
                        payment_id: paymentData.payment_id,
                        phone: phone
                    })
                });

                const otpData = await otpResponse.json();

                // Step 3: Verify OTP
                const otp = prompt('Enter OTP:');
                const verifyResponse = await fetch(`${baseURL}/api/payments/pathlog-wallet/verify/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${authToken}`
                    },
                    body: JSON.stringify({
                        payment_id: paymentData.payment_id,
                        otp_id: otpData.otp_id,
                        otp: otp
                    })
                });

                if (verifyResponse.ok) {
                    alert('Wallet payment successful!');
                    window.location.href = '/success';
                }
            } catch (error) {
                console.error('Error with wallet payment:', error);
            }
        }
    </script>
</body>
</html>
```

---

## 🔧 Testing and Troubleshooting

### Test Payment Verification
Use the provided test script to verify your payment integration:

```bash
python comprehensive_payment_verification_test.py
```

### Common Issues and Solutions

1. **"Razorpay key not provided by server"**
   - Ensure `RAZORPAY_API_KEY` is set in your `.env` file
   - Check that the key is being returned in the payment creation response

2. **Payment verification failing**
   - Verify that `RAZORPAY_API_SECRET` is correctly set
   - Ensure the signature is being passed correctly from frontend
   - Check that the payment_id matches between creation and verification

3. **Cart not found errors**
   - Ensure the user has items in their cart before creating payment
   - The `cart_id` parameter is optional and will use the user's active cart

4. **Authentication errors**
   - Ensure JWT token is valid and included in Authorization header
   - Check token expiration and refresh if needed

### Environment Variables Required
```env
RAZORPAY_API_KEY=rzp_test_your_key_here
RAZORPAY_API_SECRET=your_secret_here
PATHLOG_WALLET_API_KEY=your_pathlog_key
PATHLOG_WALLET_SECRET=your_pathlog_secret
```

---

## 📊 Payment Status Flow

```
pending → processing → completed
pending → processing → failed
pending → cancelled
```

**Status Descriptions:**
- `pending`: Payment created but not yet processed
- `processing`: Payment is being verified/processed
- `completed`: Payment successfully completed
- `failed`: Payment failed or verification failed
- `cancelled`: Payment was cancelled by user

---

## 🎯 Next Steps

1. **Test Integration**: Use the comprehensive test script to verify all payment flows
2. **Frontend Integration**: Implement the provided JavaScript examples
3. **Webhook Setup**: Configure Razorpay webhooks for automatic payment updates
4. **Error Handling**: Implement proper error handling and user feedback
5. **Security**: Ensure all sensitive data is properly secured and validated

This documentation provides complete end-to-end payment integration for all three payment methods. Each flow has been tested and verified to work with the current backend implementation.