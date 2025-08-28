# 🚀 ShipRocket Integration - UAT Mode Documentation

## Overview
Complete ShipRocket API integration for your e-commerce platform with UAT (User Acceptance Testing) mode support. This integration provides end-to-end shipping functionality including order creation, tracking, rate calculation, and webhook handling.

## 🎯 Features Implemented

### ✅ Core Functionality
- **API Connection Testing** - Test ShipRocket API connectivity
- **Serviceability Check** - Verify delivery availability between pincodes
- **Shipping Rate Calculation** - Get rates from multiple courier partners
- **Order Creation** - Create shipping orders in ShipRocket
- **Shipment Tracking** - Real-time tracking with events
- **Webhook Handling** - Automatic status updates
- **User Shipment Management** - List and manage user shipments

### ✅ Database Models
- **Shipment** - Complete shipment tracking
- **ShippingEvent** - Status update events
- **ShippingRate** - Rate caching
- **PickupRequest** - Pickup scheduling
- **ReturnRequest** - Return management
- **ShippingProvider** - Provider configuration

### ✅ API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/shipping/test/` | Test API connectivity |
| `GET` | `/api/shipping/serviceability/` | Check delivery serviceability |
| `GET` | `/api/shipping/rates/` | Get shipping rates |
| `POST` | `/api/shipping/shipments/create/` | Create new shipment |
| `GET` | `/api/shipping/shipments/` | List user shipments |
| `GET` | `/api/shipping/shipments/{order_id}/` | Get shipment details |
| `GET` | `/api/shipping/track/` | Track shipment |
| `POST` | `/api/shipping/webhook/` | ShipRocket webhook |

## 🔧 Setup Instructions

### 1. Initial Setup
```bash
# The shipping app is already added to INSTALLED_APPS
# Database migrations are already applied
# URL patterns are configured
```

### 2. Configure ShipRocket Credentials

#### Option A: Using Management Command
```bash
python manage.py setup_shiprocket --email your@email.com --password your_password --uat
```

#### Option B: Using Setup Script
```bash
python setup_shiprocket_test.py
```

#### Option C: Manual Configuration
Update `shiprocket_config.py`:
```python
SHIPROCKET_EMAIL = "your-uat-email@example.com"
SHIPROCKET_PASSWORD = "your-uat-password"
SHIPROCKET_UAT = True
```

### 3. Update Pickup Location
Edit `shiprocket_config.py` and update `DEFAULT_PICKUP_LOCATION`:
```python
DEFAULT_PICKUP_LOCATION = {
    "pickup_location": "Primary",
    "name": "Your Company Name",
    "email": "pickup@yourcompany.com",
    "phone": "9876543210",
    "address": "Your Company Address",
    "city": "Your City",
    "state": "Your State",
    "country": "India",
    "pin_code": "110001"
}
```

## 🧪 Testing

### Run Comprehensive Test
```bash
python test_shiprocket_uat.py
```

### Manual API Testing

#### 1. Test Connection
```bash
curl http://127.0.0.1:8000/api/shipping/test/
```

#### 2. Check Serviceability
```bash
curl "http://127.0.0.1:8000/api/shipping/serviceability/?pickup_pincode=110001&delivery_pincode=400001&weight=1.0"
```

#### 3. Get Shipping Rates
```bash
curl "http://127.0.0.1:8000/api/shipping/rates/?pickup_pincode=110001&delivery_pincode=560001&weight=2.5"
```

#### 4. Create Shipment (Authenticated)
```bash
curl -X POST http://127.0.0.1:8000/api/shipping/shipments/create/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
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
    "items": [
      {
        "name": "Test Product",
        "sku": "TEST001",
        "quantity": 1,
        "price": 999.00
      }
    ]
  }'
```

#### 5. Track Shipment
```bash
curl "http://127.0.0.1:8000/api/shipping/track/?order_id=TEST_001"
```

## 📊 Database Schema

### Shipment Model
```python
class Shipment(models.Model):
    order_id = CharField(max_length=100, unique=True)
    user = ForeignKey(User)
    shiprocket_order_id = CharField(max_length=100)
    shiprocket_shipment_id = CharField(max_length=100)
    awb_code = CharField(max_length=100)
    courier_name = CharField(max_length=100)
    status = CharField(max_length=50)
    # ... more fields
```

### ShippingEvent Model
```python
class ShippingEvent(models.Model):
    shipment = ForeignKey(Shipment)
    event_type = CharField(max_length=100)
    status = CharField(max_length=50)
    location = CharField(max_length=200)
    description = TextField()
    event_time = DateTimeField()
```

## 🔄 Workflow Integration

### 1. Order Creation Flow
```python
# When order is confirmed
from shiprocket_service import shiprocket_api

# Create shipment data
shipment_data = {
    "order_id": order.id,
    "customer_name": order.customer.name,
    "customer_email": order.customer.email,
    # ... other fields
}

# Create shipment
result = shiprocket_api.create_order(shipment_data)
if result['success']:
    # Save shipment to database
    shipment = Shipment.objects.create(**shipment_data)
```

### 2. Status Update Flow (Webhook)
```python
# ShipRocket sends webhook updates
# Automatic handling in /api/shipping/webhook/
# Updates shipment status and creates events
```

### 3. Tracking Flow
```python
# Get shipment tracking
shipment = Shipment.objects.get(order_id=order_id)
tracking_data = shiprocket_api.track_shipment(shipment.shiprocket_shipment_id)
```

## 🔐 Authentication & Security

### API Authentication
- Most endpoints require JWT authentication
- Public endpoints: `/test/`, `/serviceability/`, `/rates/`, `/track/`
- Protected endpoints: `/shipments/create/`, `/shipments/`

### Webhook Security
- Webhook endpoint accepts ShipRocket updates
- Validates AWB codes against database
- Logs all webhook activities

## 📱 Frontend Integration

### JavaScript Example
```javascript
// Check serviceability
async function checkServiceability(pickup, delivery, weight) {
  const response = await fetch(
    `/api/shipping/serviceability/?pickup_pincode=${pickup}&delivery_pincode=${delivery}&weight=${weight}`
  );
  return await response.json();
}

// Create shipment
async function createShipment(shipmentData) {
  const response = await fetch('/api/shipping/shipments/create/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(shipmentData)
  });
  return await response.json();
}

// Track shipment
async function trackShipment(orderId) {
  const response = await fetch(`/api/shipping/track/?order_id=${orderId}`);
  return await response.json();
}
```

## 🔧 Configuration Options

### Environment Variables (Optional)
```env
SHIPROCKET_EMAIL=your@email.com
SHIPROCKET_PASSWORD=your_password
SHIPROCKET_UAT=True
SHIPROCKET_BASE_URL=https://apiv2.shiprocket.in/v1/external/
```

### Django Settings Integration
```python
# In settings.py
SHIPROCKET_CONFIG = {
    'EMAIL': os.getenv('SHIPROCKET_EMAIL', 'test@example.com'),
    'PASSWORD': os.getenv('SHIPROCKET_PASSWORD', 'test123'),
    'UAT_MODE': os.getenv('SHIPROCKET_UAT', 'True').lower() == 'true',
}
```

## 🚨 Error Handling

### Common Issues & Solutions

#### 1. Authentication Failed
```
Error: "Authentication failed"
Solution: Check SHIPROCKET_EMAIL and SHIPROCKET_PASSWORD in config
```

#### 2. Serviceability Check Failed
```
Error: "Serviceability check failed"
Solution: Verify pincode format (should be 6 digits)
```

#### 3. Order Creation Failed
```
Error: "Order creation failed"
Solution: Check required fields and pickup location configuration
```

#### 4. JSON Serialization Error
```
Error: "Object of type Decimal is not JSON serializable"
Solution: Fixed in current implementation with convert_decimal function
```

### Error Logging
All errors are logged using Django's logging system:
```python
import logging
logger = logging.getLogger(__name__)
logger.error(f"ShipRocket error: {error_message}")
```

## 📈 Monitoring & Analytics

### Database Queries
```python
# Track shipment statistics
total_shipments = Shipment.objects.count()
delivered = Shipment.objects.filter(status='delivered').count()
in_transit = Shipment.objects.filter(status__in=['dispatched', 'in_transit']).count()

# Popular couriers
popular_couriers = Shipment.objects.values('courier_name').annotate(count=Count('id'))
```

### Performance Monitoring
- API response times
- Success/failure rates
- Courier performance
- Delivery times

## 🔄 Production Deployment

### 1. Update Configuration
```python
SHIPROCKET_UAT = False  # Switch to production
SHIPROCKET_EMAIL = "production@email.com"
SHIPROCKET_PASSWORD = "production_password"
```

### 2. Webhook Configuration
1. Login to ShipRocket dashboard
2. Go to Settings > Webhooks
3. Add webhook URL: `https://yourdomain.com/api/shipping/webhook/`
4. Enable status update notifications

### 3. SSL Certificate
Ensure webhook endpoint has valid SSL certificate for production.

### 4. Monitoring Setup
- Set up logging
- Configure error notifications
- Monitor API usage limits

## 🔗 API Documentation

Complete API documentation is available at:
- Swagger UI: `http://127.0.0.1:8000/swagger/`
- ReDoc: `http://127.0.0.1:8000/redoc/`

## 📞 Support

### ShipRocket Support
- UAT Environment: Contact ShipRocket support for UAT access
- Documentation: https://docs.shiprocket.co/
- Support: support@shiprocket.co

### Integration Support
- Check logs in Django admin
- Review error responses
- Test with minimal data first
- Use UAT mode for all testing

## 🎉 Ready for Production!

Your ShipRocket integration is now complete with:
- ✅ Full UAT testing capability
- ✅ Comprehensive error handling
- ✅ Database models for tracking
- ✅ Webhook support
- ✅ REST API endpoints
- ✅ Admin interface
- ✅ Frontend integration points

Update your credentials and start testing! 🚀