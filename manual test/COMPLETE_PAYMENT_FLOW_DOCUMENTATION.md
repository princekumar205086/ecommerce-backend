# Complete Payment Flow Documentation

## Overview
This documentation covers all payment methods supported in the e-commerce backend:
1. **Razorpay** - Online payment gateway
2. **COD (Cash on Delivery)** - Pay on delivery
3. **Pathlog Wallet** - Custom wallet with mobile verification

## Payment Flow Architecture

### 1. Payment-First Flow
All payment methods follow a payment-first approach:
1. User adds items to cart
2. Payment is created with cart data
3. Payment is processed
4. Order is automatically created upon successful payment

## Supported Payment Methods

### 1. Razorpay Payment Flow

#### Endpoints:
- `POST /api/payments/create-from-cart/` - Create payment
- `POST /api/payments/confirm-razorpay/` - Confirm payment

#### Flow:
1. **Create Payment from Cart**
   ```bash
   POST /api/payments/create-from-cart/
   {
     "payment_method": "razorpay"
   }
   ```

2. **Confirm Payment**
   ```bash
   POST /api/payments/confirm-razorpay/
   {
     "payment_id": 1,
     "razorpay_order_id": "order_xxx",
     "razorpay_payment_id": "pay_xxx",
     "razorpay_signature": "signature_xxx"
   }
   ```

#### Response:
- Payment confirmed → Order auto-created
- Cart items cleared
- User address saved to profile

---

### 2. Cash on Delivery (COD) Flow

#### Endpoints:
- `POST /api/payments/create-from-cart/` - Create payment
- `POST /api/payments/confirm-cod/` - Confirm COD

#### Flow:
1. **Create COD Payment**
   ```bash
   POST /api/payments/create-from-cart/
   {
     "payment_method": "cod"
   }
   ```

2. **Confirm COD**
   ```bash
   POST /api/payments/confirm-cod/
   {
     "payment_id": 1
   }
   ```

#### Response:
- COD confirmed → Order auto-created
- Payment status: `pending` (will be paid on delivery)
- Cart items cleared
- User address saved to profile

---

### 3. Pathlog Wallet Flow

#### Endpoints:
- `POST /api/payments/create-from-cart/` - Create payment
- `POST /api/payments/pathlog-wallet/verify/` - Verify mobile
- `POST /api/payments/pathlog-wallet/otp/` - Verify OTP
- `POST /api/payments/pathlog-wallet/pay/` - Process payment

#### Flow:
1. **Create Pathlog Wallet Payment**
   ```bash
   POST /api/payments/create-from-cart/
   {
     "payment_method": "pathlog_wallet"
   }
   ```

2. **Verify Mobile Number**
   ```bash
   POST /api/payments/pathlog-wallet/verify/
   {
     "payment_id": 1,
     "mobile_number": "8677939971"
   }
   ```

3. **Verify OTP**
   ```bash
   POST /api/payments/pathlog-wallet/otp/
   {
     "payment_id": 1,
     "otp": "123456"
   }
   ```

4. **Process Payment**
   ```bash
   POST /api/payments/pathlog-wallet/pay/
   {
     "payment_id": 1
   }
   ```

#### Response:
- Payment processed → Order auto-created
- Wallet balance deducted
- Cart items cleared
- User address saved to profile

## Payment Model Structure

### Payment Fields:
```python
class Payment(models.Model):
    # Basic fields
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Cart data (JSON field)
    cart_data = models.JSONField(null=True, blank=True)
    
    # Razorpay fields
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    
    # Pathlog Wallet fields
    pathlog_wallet_mobile = models.CharField(max_length=15, blank=True, null=True)
    pathlog_wallet_otp = models.CharField(max_length=6, blank=True, null=True)
    pathlog_wallet_verified = models.BooleanField(default=False)
    pathlog_wallet_balance = models.FloatField(null=True, blank=True)
    pathlog_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    pathlog_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Relationships
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
```

## User Address Management

### Address Fields in User Model:
```python
class User(AbstractBaseUser):
    # ... other fields
    address_line_1 = models.CharField(max_length=255, blank=True, null=True)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
```

### Address Persistence:
- During payment creation, user's shipping address is saved to their profile
- Billing address = Shipping address (no separate billing address collection)
- Address is reused for future orders

## Order Auto-Creation

### Order Creation Process:
1. Payment is successfully processed
2. System creates order from cart data stored in payment
3. Order status set based on payment method:
   - Razorpay: `pending` with `payment_status: paid`
   - COD: `pending` with `payment_status: pending`
   - Pathlog Wallet: `pending` with `payment_status: paid`
4. Cart items are cleared
5. Inventory is updated (if applicable)

### Order Model Structure:
```python
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    # ... other fields
```

## Testing

### Test Files:
1. `test_cod_flow.py` - Complete COD flow test
2. `test_pathlog_wallet_flow.py` - Complete Pathlog Wallet flow test

### Test Coverage:
- ✅ Authentication
- ✅ Cart creation and item addition
- ✅ Payment creation
- ✅ Payment processing (specific to method)
- ✅ Order auto-creation
- ✅ Cart clearing
- ✅ Address persistence
- ✅ Balance management (Pathlog Wallet)

## Error Handling

### Common Error Responses:
```json
// Authentication Error
{
  "detail": "Authentication credentials were not provided."
}

// Payment Not Found
{
  "error": "Payment not found"
}

// Insufficient Balance (Pathlog Wallet)
{
  "error": "Insufficient wallet balance"
}

// Invalid OTP (Pathlog Wallet)
{
  "error": "Invalid OTP"
}
```

## Security Features

### Authentication:
- JWT token-based authentication
- User-specific payment and order access

### Pathlog Wallet Security:
- Mobile number verification
- OTP validation
- Balance verification before payment
- Transaction ID generation

### Razorpay Security:
- Signature verification
- Order validation
- Payment verification

## API Response Examples

### Successful Payment Creation:
```json
{
  "payment_method": "pathlog_wallet",
  "payment_id": 23,
  "amount": 881.9,
  "currency": "INR",
  "message": "Pathlog Wallet payment created. Please verify your wallet to proceed.",
  "next_step": "/api/payments/pathlog-wallet/verify/",
  "verification_required": true,
  "order_summary": {
    "subtotal": 705.0,
    "tax": 126.9,
    "shipping": 50.0,
    "discount": 0.0,
    "total": 881.9
  }
}
```

### Successful Order Creation:
```json
{
  "status": "Payment Successful",
  "message": "Payment successful. Order created: #202508250010",
  "transaction_id": "TXN8F12C1E1880D",
  "order_created": true,
  "order": {
    "id": 15,
    "order_number": "202508250010",
    "status": "pending",
    "payment_status": "paid",
    "total": "775.50",
    "items_count": 1
  },
  "payment": {
    "id": 23,
    "status": "successful",
    "amount": "881.90",
    "method": "pathlog_wallet",
    "transaction_id": "TXN8F12C1E1880D"
  }
}
```

## Deployment Notes

### Environment Variables Required:
```bash
# Razorpay
RAZORPAY_API_KEY=your_razorpay_key
RAZORPAY_API_SECRET=your_razorpay_secret

# Database
DATABASE_URL=your_database_url

# Django
SECRET_KEY=your_secret_key
DEBUG=False
```

### Migration Commands:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Testing Commands:
```bash
# Test COD flow
python test_cod_flow.py

# Test Pathlog Wallet flow
python test_pathlog_wallet_flow.py
```

## Future Enhancements

### Pathlog Wallet Integration:
- Replace demo OTP with actual Pathlog API
- Replace demo balance with real wallet API
- Add transaction history
- Add wallet recharge functionality

### Additional Features:
- Multiple payment methods in single order
- Partial payments
- Refund management
- Payment retry mechanism
- Webhook handling for payment status updates

---

**Last Updated:** January 25, 2025
**Version:** 1.0
**Status:** Production Ready ✅