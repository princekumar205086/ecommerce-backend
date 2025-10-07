# ShipRocket API Integration Summary

## 🚀 Quick Start Guide

This document provides a quick reference for integrating ShipRocket API into your frontend application.

## 📋 Test Results Summary

**Test Execution Date:** October 7, 2025
- **Total Endpoints Tested:** 17
- **Successful Tests:** 11 ✅
- **Failed Tests:** 6 ❌
- **Success Rate:** 64.7%

### ✅ Working Endpoints
1. **Authentication** - Login and token generation
2. **Serviceability Check** - Pincode to pincode delivery check
3. **Order Management** - Get orders list
4. **Tracking** - Track shipments by AWB
5. **Pickup Locations** - Get pickup locations
6. **Courier Services** - Get available couriers
7. **Returns** - Create return orders

### ❌ Endpoints with Issues
1. **Order Creation** - 400 Bad Request (validation issues)
2. **Pickup Location Creation** - 405 Method Not Allowed
3. **Recommended Courier** - 404 Not Found
4. **Pincode Validation** - 404 Not Found
5. **Pickup Generation** - 405 Method Not Allowed

## 🔑 Essential Endpoints for Frontend

### 1. Authentication
```javascript
// Login to get access token
POST https://apiv2.shiprocket.in/v1/external/auth/login

// Payload
{
    "email": "your-email@domain.com",
    "password": "your-password"
}

// Response
{
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "company_id": 7538730,
    "email": "your-email@domain.com"
}
```

### 2. Check Serviceability
```javascript
// Check if delivery is possible between pincodes
GET https://apiv2.shiprocket.in/v1/external/courier/serviceability/

// Parameters
{
    "pickup_postcode": "110001",
    "delivery_postcode": "400001", 
    "weight": "1",
    "cod": "0" // 0 for prepaid, 1 for COD
}
```

### 3. Create Shipping Order
```javascript
// Create new shipping order
POST https://apiv2.shiprocket.in/v1/external/orders/create/adhoc

// Payload (simplified)
{
    "order_id": "ORDER_12345",
    "order_date": "2025-10-07 12:00",
    "pickup_location": "Primary",
    "billing_customer_name": "John Doe",
    "billing_address": "123 Main Street",
    "billing_city": "Delhi",
    "billing_pincode": "110001",
    "billing_state": "Delhi",
    "billing_country": "India",
    "billing_email": "john@example.com",
    "billing_phone": "9876543210",
    "shipping_is_billing": true,
    "order_items": [
        {
            "name": "Product Name",
            "sku": "PROD001",
            "units": 1,
            "selling_price": 100,
            "discount": 0,
            "tax": 18
        }
    ],
    "payment_method": "Prepaid",
    "sub_total": 118,
    "length": 10,
    "breadth": 10, 
    "height": 5,
    "weight": 0.5
}
```

### 4. Track Shipment
```javascript
// Track by Shipment ID
GET https://apiv2.shiprocket.in/v1/external/courier/track/shipment/{shipment_id}

// Track by AWB Number
GET https://apiv2.shiprocket.in/v1/external/courier/track/awb/{awb_number}
```

## 🛠️ Frontend Implementation

### React Hook Example
```javascript
import { useState, useCallback } from 'react';
import axios from 'axios';

const useShipRocket = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [token, setToken] = useState(localStorage.getItem('shiprocket_token'));

    const BASE_URL = 'https://apiv2.shiprocket.in/v1/external/';

    // Authenticate and get token
    const authenticate = useCallback(async () => {
        setLoading(true);
        try {
            const response = await axios.post(`${BASE_URL}auth/login`, {
                email: process.env.REACT_APP_SHIPROCKET_EMAIL,
                password: process.env.REACT_APP_SHIPROCKET_PASSWORD
            });
            
            const newToken = response.data.token;
            setToken(newToken);
            localStorage.setItem('shiprocket_token', newToken);
            setError(null);
            return newToken;
        } catch (err) {
            setError(err.response?.data?.message || 'Authentication failed');
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    // Make authenticated request
    const makeRequest = useCallback(async (endpoint, method = 'GET', data = null) => {
        let currentToken = token;
        
        // Get token if not available
        if (!currentToken) {
            currentToken = await authenticate();
        }

        try {
            const config = {
                method,
                url: `${BASE_URL}${endpoint}`,
                headers: {
                    'Authorization': `Bearer ${currentToken}`,
                    'Content-Type': 'application/json'
                }
            };

            if (data) {
                config.data = data;
            }

            const response = await axios(config);
            return response.data;
        } catch (err) {
            if (err.response?.status === 401) {
                // Token expired, re-authenticate
                currentToken = await authenticate();
                return makeRequest(endpoint, method, data);
            }
            throw err;
        }
    }, [token, authenticate]);

    // Check serviceability
    const checkServiceability = useCallback(async (pickupPin, deliveryPin, weight = 1, isCOD = false) => {
        const params = new URLSearchParams({
            pickup_postcode: pickupPin,
            delivery_postcode: deliveryPin,
            weight: weight.toString(),
            cod: isCOD ? '1' : '0'
        });
        
        return await makeRequest(`courier/serviceability/?${params}`);
    }, [makeRequest]);

    // Create order
    const createOrder = useCallback(async (orderData) => {
        return await makeRequest('orders/create/adhoc', 'POST', orderData);
    }, [makeRequest]);

    // Track shipment
    const trackShipment = useCallback(async (shipmentId) => {
        return await makeRequest(`courier/track/shipment/${shipmentId}`);
    }, [makeRequest]);

    return {
        loading,
        error,
        authenticate,
        checkServiceability,
        createOrder,
        trackShipment,
        makeRequest
    };
};

export default useShipRocket;
```

### Usage in Component
```javascript
import React, { useState } from 'react';
import useShipRocket from './hooks/useShipRocket';

const ShippingComponent = () => {
    const { checkServiceability, createOrder, loading, error } = useShipRocket();
    const [serviceResult, setServiceResult] = useState(null);

    const handleServiceCheck = async () => {
        try {
            const result = await checkServiceability('110001', '400001', 1, false);
            setServiceResult(result);
        } catch (err) {
            console.error('Service check failed:', err);
        }
    };

    const handleCreateOrder = async (orderData) => {
        try {
            const result = await createOrder(orderData);
            console.log('Order created:', result);
        } catch (err) {
            console.error('Order creation failed:', err);
        }
    };

    return (
        <div>
            <button onClick={handleServiceCheck} disabled={loading}>
                Check Serviceability
            </button>
            {error && <p style={{color: 'red'}}>Error: {error}</p>}
            {serviceResult && (
                <div>
                    <h3>Available Couriers:</h3>
                    {serviceResult.data?.available_courier_companies?.map(courier => (
                        <div key={courier.courier_company_id}>
                            <p>{courier.courier_name}: ₹{courier.freight_charge}</p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};
```

## 🔐 Security Best Practices

### Environment Variables
```javascript
// .env file
REACT_APP_SHIPROCKET_BASE_URL=https://apiv2.shiprocket.in/v1/external/
REACT_APP_SHIPROCKET_EMAIL=your-email@domain.com
REACT_APP_SHIPROCKET_PASSWORD=your-password

// Never expose credentials in frontend code
// Use backend proxy for sensitive operations
```

### Backend Proxy (Recommended)
```javascript
// Instead of direct frontend calls, use your backend as proxy
// Frontend -> Your Backend -> ShipRocket API

// Frontend call
const response = await axios.post('/api/shipping/create-order', orderData);

// Your backend handles ShipRocket authentication and API calls
```

## 📊 Rate Limiting

| Endpoint | Limit | Window |
|----------|--------|---------|
| Authentication | 100/hour | 1 hour |
| Order Creation | 1000/hour | 1 hour |
| Tracking | 5000/hour | 1 hour |
| Serviceability | 10000/hour | 1 hour |

## 🐛 Common Issues & Solutions

### 1. Order Creation Fails (400 Bad Request)
**Problem:** Missing required fields or invalid format
**Solution:** 
- Ensure all required fields are present
- Validate pincode format (6 digits)
- Check weight and dimensions are numeric
- Verify pickup location exists

### 2. Authentication Token Expires
**Problem:** 401 Unauthorized after some time
**Solution:**
- Implement automatic token refresh
- Cache token with expiry time
- Retry failed requests after re-authentication

### 3. Serviceability Returns Empty
**Problem:** No couriers available for pincode combination
**Solution:**
- Verify both pincodes are valid
- Check if area is serviceable by ShipRocket
- Try with different weight/COD combinations

## 🔄 Webhook Integration

### Setup Webhook Endpoint
```javascript
// Backend webhook handler
app.post('/api/shiprocket/webhook', express.raw({type: 'application/json'}), (req, res) => {
    const event = req.body;
    
    // Verify webhook signature (recommended)
    // const signature = req.headers['x-shiprocket-signature'];
    
    switch (event.current_status) {
        case 'Delivered':
            // Update order status in your database
            updateOrderStatus(event.order_id, 'delivered');
            break;
        case 'Out for Delivery':
            updateOrderStatus(event.order_id, 'out_for_delivery');
            break;
        case 'In Transit':
            updateOrderStatus(event.order_id, 'in_transit');
            break;
        case 'RTO':
            updateOrderStatus(event.order_id, 'returned');
            break;
    }
    
    res.status(200).send('OK');
});
```

## 📚 Additional Resources

- **Full API Documentation:** `SHIPROCKET_API_COMPREHENSIVE_DOCUMENTATION.md`
- **ShipRocket Dashboard:** https://app.shiprocket.in/
- **API Reference:** https://apidocs.shiprocket.in/
- **Support:** https://support.shiprocket.in/

## ⚠️ Important Notes

1. **Test Environment:** Currently configured for UAT (testing)
2. **Production Setup:** Update credentials and base URL for production
3. **Error Handling:** Always implement comprehensive error handling
4. **Rate Limits:** Respect API rate limits to avoid blocking
5. **Security:** Never expose API credentials in frontend code

---

*Generated on October 7, 2025 - For MedixMall E-commerce Backend*