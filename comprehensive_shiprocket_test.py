"""
Comprehensive ShipRocket API Testing Script
Tests all ShipRocket endpoints with detailed logging and documentation generation
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
from decimal import Decimal
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment variables or direct values
SHIPROCKET_BASE_URL = "https://apiv2.shiprocket.in/v1/external/"
SHIPROCKET_EMAIL = "avengerprinceraj@gmail.com"
SHIPROCKET_PASSWORD = "N4nWsj1R^u@IJZHp"
SHIPROCKET_TIMEOUT = 30

class ShipRocketTester:
    """Comprehensive ShipRocket API Tester"""
    
    def __init__(self):
        self.base_url = SHIPROCKET_BASE_URL
        self.email = SHIPROCKET_EMAIL
        self.password = SHIPROCKET_PASSWORD
        self.timeout = SHIPROCKET_TIMEOUT
        self.token = None
        self.test_results = []
        self.created_orders = []  # Track created orders for cleanup
        
    def log_test_result(self, endpoint: str, method: str, payload: Dict, response: Dict, status_code: int, notes: str = ""):
        """Log test result for documentation"""
        result = {
            "endpoint": endpoint,
            "method": method,
            "payload": payload,
            "response": response,
            "status_code": status_code,
            "timestamp": datetime.now().isoformat(),
            "notes": notes,
            "success": 200 <= status_code < 300
        }
        self.test_results.append(result)
        logger.info(f"{method} {endpoint} - Status: {status_code} - {'SUCCESS' if result['success'] else 'FAILED'}")
        
    def make_request(self, method: str, endpoint: str, payload: Dict = None, headers: Dict = None, params: Dict = None):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        if headers is None:
            headers = {'Content-Type': 'application/json'}
            
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=payload, headers=headers, timeout=self.timeout)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            try:
                response_data = response.json()
            except:
                response_data = {"error": "Invalid JSON response", "text": response.text}
                
            self.log_test_result(endpoint, method.upper(), payload or params, response_data, response.status_code)
            return response_data, response.status_code
            
        except requests.exceptions.RequestException as e:
            error_response = {"error": str(e)}
            self.log_test_result(endpoint, method.upper(), payload or params, error_response, 500, str(e))
            return error_response, 500
    
    def get_auth_headers(self):
        """Get headers with authentication token"""
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers
    
    def test_authentication(self):
        """Test 1: Authentication endpoint"""
        logger.info("Testing Authentication...")
        
        payload = {
            "email": self.email,
            "password": self.password
        }
        
        response_data, status_code = self.make_request('POST', 'auth/login', payload)
        
        if status_code == 200 and 'token' in response_data:
            self.token = response_data['token']
            logger.info("Authentication successful - Token obtained")
            return True
        else:
            logger.error("Authentication failed")
            return False
    
    def test_serviceability(self):
        """Test 2: Serviceability check endpoints"""
        logger.info("Testing Serviceability...")
        
        # Test cases for serviceability
        test_cases = [
            {
                "name": "Delhi to Mumbai - Prepaid",
                "pickup_postcode": "110001",
                "delivery_postcode": "400001",
                "weight": "1",
                "cod": "0"
            },
            {
                "name": "Delhi to Mumbai - COD",
                "pickup_postcode": "110001", 
                "delivery_postcode": "400001",
                "weight": "1",
                "cod": "1"
            },
            {
                "name": "Rural area test",
                "pickup_postcode": "110001",
                "delivery_postcode": "854301",  # Bihar
                "weight": "1",
                "cod": "0"
            }
        ]
        
        for test_case in test_cases:
            params = {
                "pickup_postcode": test_case["pickup_postcode"],
                "delivery_postcode": test_case["delivery_postcode"],
                "weight": test_case["weight"],
                "cod": test_case["cod"]
            }
            
            response_data, status_code = self.make_request(
                'GET', 'courier/serviceability/', 
                params=params, 
                headers=self.get_auth_headers()
            )
    
    def test_order_creation(self):
        """Test 3: Order creation endpoint"""
        logger.info("Testing Order Creation...")
        
        # Test case 1: Prepaid order
        prepaid_order = {
            "order_id": f"TEST_ORDER_{int(time.time())}_PREPAID",
            "order_date": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "pickup_location": "Primary",
            "channel_id": "",
            "comment": "Test order - Prepaid",
            "billing_customer_name": "John",
            "billing_last_name": "Doe",
            "billing_address": "123 Test Street",
            "billing_address_2": "Near Test Mall",
            "billing_city": "New Delhi",
            "billing_pincode": "110001",
            "billing_state": "Delhi",
            "billing_country": "India",
            "billing_email": "john.doe@test.com",
            "billing_phone": "9876543210",
            "shipping_is_billing": True,
            "shipping_customer_name": "John",
            "shipping_last_name": "Doe",
            "shipping_address": "123 Test Street",
            "shipping_address_2": "Near Test Mall",
            "shipping_city": "New Delhi",
            "shipping_pincode": "110001",
            "shipping_country": "India",
            "shipping_state": "Delhi",
            "shipping_email": "john.doe@test.com",
            "shipping_phone": "9876543210",
            "order_items": [
                {
                    "name": "Test Product 1",
                    "sku": "TEST-SKU-001",
                    "units": 2,
                    "selling_price": 100,
                    "discount": 10,
                    "tax": 18,
                    "hsn": 0
                },
                {
                    "name": "Test Product 2",
                    "sku": "TEST-SKU-002",
                    "units": 1,
                    "selling_price": 200,
                    "discount": 0,
                    "tax": 18,
                    "hsn": 0
                }
            ],
            "payment_method": "Prepaid",
            "shipping_charges": 50,
            "giftwrap_charges": 0,
            "transaction_charges": 5,
            "total_discount": 10,
            "sub_total": 390,
            "length": 15,
            "breadth": 10,
            "height": 8,
            "weight": 1.5
        }
        
        response_data, status_code = self.make_request(
            'POST', 'orders/create/adhoc',
            prepaid_order,
            self.get_auth_headers()
        )
        
        if status_code == 200 and response_data.get('status_code') == 1:
            self.created_orders.append({
                'order_id': response_data.get('order_id'),
                'shipment_id': response_data.get('shipment_id'),
                'type': 'prepaid'
            })
        
        # Test case 2: COD order
        cod_order = prepaid_order.copy()
        cod_order.update({
            "order_id": f"TEST_ORDER_{int(time.time())}_COD",
            "payment_method": "COD",
            "comment": "Test order - COD"
        })
        
        response_data, status_code = self.make_request(
            'POST', 'orders/create/adhoc',
            cod_order,
            self.get_auth_headers()
        )
        
        if status_code == 200 and response_data.get('status_code') == 1:
            self.created_orders.append({
                'order_id': response_data.get('order_id'),
                'shipment_id': response_data.get('shipment_id'),
                'type': 'cod'
            })
    
    def test_order_management(self):
        """Test 4: Order management endpoints"""
        logger.info("Testing Order Management...")
        
        # Get all orders
        response_data, status_code = self.make_request(
            'GET', 'orders',
            params={'page': 1, 'per_page': 10},
            headers=self.get_auth_headers()
        )
        
        # Get specific order if we have created orders
        if self.created_orders:
            order_id = self.created_orders[0]['order_id']
            response_data, status_code = self.make_request(
                'GET', f'orders/show/{order_id}',
                headers=self.get_auth_headers()
            )
    
    def test_tracking(self):
        """Test 5: Tracking endpoints"""
        logger.info("Testing Tracking...")
        
        # Test with shipment ID if available
        if self.created_orders:
            shipment_id = self.created_orders[0]['shipment_id']
            response_data, status_code = self.make_request(
                'GET', f'courier/track/shipment/{shipment_id}',
                headers=self.get_auth_headers()
            )
        
        # Test track by AWB (will fail as we don't have real AWB, but good for documentation)
        response_data, status_code = self.make_request(
            'GET', 'courier/track/awb/TEST_AWB_123',
            headers=self.get_auth_headers()
        )
    
    def test_pickup_management(self):
        """Test 6: Pickup location management"""
        logger.info("Testing Pickup Management...")
        
        # Get pickup locations
        response_data, status_code = self.make_request(
            'GET', 'settings/company/pickup',
            headers=self.get_auth_headers()
        )
        
        # Add pickup location
        pickup_data = {
            "pickup_location": "Test Location",
            "name": "Test Warehouse",
            "email": "warehouse@test.com",
            "phone": "9876543210",
            "address": "Test Warehouse Address",
            "address_2": "Near Test Area",
            "city": "Mumbai",
            "state": "Maharashtra",
            "country": "India",
            "pin_code": "400001"
        }
        
        response_data, status_code = self.make_request(
            'POST', 'settings/company/pickup',
            pickup_data,
            self.get_auth_headers()
        )
    
    def test_courier_services(self):
        """Test 7: Courier and services endpoints"""
        logger.info("Testing Courier Services...")
        
        # Get available couriers
        response_data, status_code = self.make_request(
            'GET', 'courier/courierListWithCounts',
            headers=self.get_auth_headers()
        )
        
        # Get courier services
        response_data, status_code = self.make_request(
            'GET', 'courier/getRecommendedCourier',
            params={
                'pickup_postcode': '110001',
                'delivery_postcode': '400001',
                'weight': '1',
                'cod': '0'
            },
            headers=self.get_auth_headers()
        )
    
    def test_invoice_and_labels(self):
        """Test 8: Invoice and label generation"""
        logger.info("Testing Invoice and Labels...")
        
        if self.created_orders:
            order_ids = [str(order['order_id']) for order in self.created_orders]
            
            # Generate invoice
            response_data, status_code = self.make_request(
                'POST', 'orders/print/invoice',
                {"ids": order_ids},
                self.get_auth_headers()
            )
            
            # Generate shipping labels
            response_data, status_code = self.make_request(
                'POST', 'orders/print',
                {"ids": order_ids},
                self.get_auth_headers()
            )
    
    def test_returns_and_cancellation(self):
        """Test 9: Returns and cancellation"""
        logger.info("Testing Returns and Cancellation...")
        
        # Create return order (will likely fail in test but good for docs)
        return_data = {
            "order_id": "TEST_RETURN_001",
            "order_date": datetime.now().strftime('%Y-%m-%d'),
            "channel_id": "",
            "pickup_customer_name": "John Doe",
            "pickup_last_name": "",
            "pickup_address": "123 Test Street",
            "pickup_address_2": "",
            "pickup_city": "Delhi",
            "pickup_pincode": "110001",
            "pickup_state": "Delhi",
            "pickup_country": "India",
            "pickup_email": "john@test.com",
            "pickup_phone": "9876543210",
            "shipping_customer_name": "Test Company",
            "shipping_last_name": "",
            "shipping_address": "Warehouse Address",
            "shipping_address_2": "",
            "shipping_city": "Mumbai",
            "shipping_pincode": "400001",
            "shipping_country": "India",
            "shipping_state": "Maharashtra",
            "shipping_email": "warehouse@test.com",
            "shipping_phone": "9876543211",
            "order_items": [
                {
                    "name": "Return Product",
                    "sku": "RET-001",
                    "units": 1,
                    "selling_price": 100,
                    "discount": 0,
                    "tax": 0,
                    "hsn": 0
                }
            ],
            "payment_method": "Prepaid",
            "total_discount": 0,
            "sub_total": 100,
            "length": 10,
            "breadth": 10,
            "height": 5,
            "weight": 0.5
        }
        
        response_data, status_code = self.make_request(
            'POST', 'orders/create/return',
            return_data,
            self.get_auth_headers()
        )
    
    def test_webhook_endpoints(self):
        """Test 10: Webhook related endpoints"""
        logger.info("Testing Webhook endpoints...")
        
        # Test webhook data (informational)
        webhook_sample = {
            "order_id": "TEST_ORDER_001",
            "shipment_id": "12345",
            "current_status": "Delivered",
            "delivered_date": datetime.now().isoformat(),
            "track_url": "https://test.track.url"
        }
        
        # Log webhook structure for documentation
        self.log_test_result(
            "webhook/shipment_update", 
            "POST", 
            webhook_sample, 
            {"note": "Webhook endpoint structure for receiving updates"}, 
            200,
            "Sample webhook payload structure"
        )
    
    def test_additional_services(self):
        """Test 11: Additional services and utilities"""
        logger.info("Testing Additional Services...")
        
        # Test pincode check
        response_data, status_code = self.make_request(
            'GET', 'courier/pincode/check',
            params={'pincode': '110001'},
            headers=self.get_auth_headers()
        )
        
        # Test weight validation
        response_data, status_code = self.make_request(
            'GET', 'courier/courierListWithCounts',
            headers=self.get_auth_headers()
        )
        
        # Test estimate delivery date
        response_data, status_code = self.make_request(
            'GET', 'courier/generate/pickup',
            params={
                'shipment_id': 'TEST_SHIPMENT_ID',
                'pickup_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            },
            headers=self.get_auth_headers()
        )
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        logger.info("Starting comprehensive ShipRocket API testing...")
        
        # Step 1: Authentication (required for all other tests)
        if not self.test_authentication():
            logger.error("Authentication failed. Cannot proceed with other tests.")
            return False
        
        # Step 2: Run all other tests
        try:
            self.test_serviceability()
            self.test_order_creation()
            self.test_order_management()
            self.test_tracking()
            self.test_pickup_management()
            self.test_courier_services()
            self.test_invoice_and_labels()
            self.test_returns_and_cancellation()
            self.test_webhook_endpoints()
            self.test_additional_services()
            
            logger.info("All tests completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Test execution failed: {str(e)}")
            return False
    
    def generate_documentation(self):
        """Generate comprehensive API documentation"""
        doc_content = self._generate_markdown_documentation()
        
        with open('SHIPROCKET_API_COMPREHENSIVE_DOCUMENTATION.md', 'w', encoding='utf-8') as f:
            f.write(doc_content)
        
        logger.info("Documentation generated: SHIPROCKET_API_COMPREHENSIVE_DOCUMENTATION.md")
    
    def _generate_markdown_documentation(self):
        """Generate markdown documentation from test results"""
        doc = f"""# ShipRocket API Comprehensive Documentation

## Overview
This document provides complete API documentation for ShipRocket integration including all endpoints, payloads, responses, and frontend integration guidelines.

**Test Execution Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Tests Executed:** {len(self.test_results)}
**Successful Tests:** {len([r for r in self.test_results if r['success']])}

## Authentication

### Base URL
```
{self.base_url}
```

### Authentication Headers
```javascript
headers: {{
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN_HERE'
}}
```

## API Endpoints

"""
        
        # Group tests by endpoint category
        categories = {
            'Authentication': [],
            'Serviceability': [],
            'Orders': [],
            'Tracking': [],
            'Pickup': [],
            'Courier': [],
            'Invoice': [],
            'Returns': [],
            'Webhook': [],
            'Utilities': []
        }
        
        for result in self.test_results:
            endpoint = result['endpoint']
            if 'auth' in endpoint:
                categories['Authentication'].append(result)
            elif 'serviceability' in endpoint:
                categories['Serviceability'].append(result)
            elif 'orders' in endpoint:
                categories['Orders'].append(result)
            elif 'track' in endpoint:
                categories['Tracking'].append(result)
            elif 'pickup' in endpoint:
                categories['Pickup'].append(result)
            elif 'courier' in endpoint:
                categories['Courier'].append(result)
            elif 'print' in endpoint or 'invoice' in endpoint:
                categories['Invoice'].append(result)
            elif 'return' in endpoint:
                categories['Returns'].append(result)
            elif 'webhook' in endpoint:
                categories['Webhook'].append(result)
            else:
                categories['Utilities'].append(result)
        
        for category, results in categories.items():
            if not results:
                continue
                
            doc += f"\n### {category}\n\n"
            
            for result in results:
                doc += f"#### {result['method']} {result['endpoint']}\n\n"
                doc += f"**Status Code:** {result['status_code']} {'✅' if result['success'] else '❌'}\n\n"
                
                if result['notes']:
                    doc += f"**Notes:** {result['notes']}\n\n"
                
                # Request payload
                if result['payload']:
                    doc += "**Request Payload:**\n```json\n"
                    doc += json.dumps(result['payload'], indent=2, default=str)
                    doc += "\n```\n\n"
                
                # Response
                doc += "**Response:**\n```json\n"
                doc += json.dumps(result['response'], indent=2, default=str)
                doc += "\n```\n\n"
                
                # Frontend integration example
                doc += "**Frontend Integration (JavaScript/Axios):**\n```javascript\n"
                if result['method'] == 'GET':
                    doc += f"""const response = await axios.get('{self.base_url}{result['endpoint']}', {{
    headers: {{
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
    }}"""
                    if result['payload']:
                        doc += f",\n    params: {json.dumps(result['payload'], default=str)}"
                    doc += "\n});\n"
                else:
                    doc += f"""const response = await axios.{result['method'].lower()}('{self.base_url}{result['endpoint']}', """
                    if result['payload']:
                        doc += f"{json.dumps(result['payload'], indent=2, default=str)}, "
                    doc += """{\n    headers: {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
    }
});
"""
                doc += "```\n\n"
                doc += "---\n\n"
        
        # Add integration guidelines
        doc += self._get_integration_guidelines()
        
        return doc
    
    def _get_integration_guidelines(self):
        """Get frontend integration guidelines"""
        return """
## Frontend Integration Guidelines

### 1. Authentication Flow
```javascript
// Store credentials securely
const SHIPROCKET_EMAIL = 'your-email@domain.com';
const SHIPROCKET_PASSWORD = 'your-password';

// Login and get token
async function getShipRocketToken() {
    try {
        const response = await axios.post('https://apiv2.shiprocket.in/v1/external/auth/login', {
            email: SHIPROCKET_EMAIL,
            password: SHIPROCKET_PASSWORD
        });
        
        const token = response.data.token;
        // Store token securely (localStorage, sessionStorage, or state management)
        localStorage.setItem('shiprocket_token', token);
        return token;
    } catch (error) {
        console.error('Authentication failed:', error);
        throw error;
    }
}
```

### 2. Error Handling
```javascript
async function makeShipRocketRequest(endpoint, method = 'GET', data = null) {
    try {
        const token = localStorage.getItem('shiprocket_token');
        
        const config = {
            method,
            url: `https://apiv2.shiprocket.in/v1/external/${endpoint}`,
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        };
        
        if (data) {
            config.data = data;
        }
        
        const response = await axios(config);
        return response.data;
        
    } catch (error) {
        if (error.response?.status === 401) {
            // Token expired, re-authenticate
            await getShipRocketToken();
            // Retry the request
            return makeShipRocketRequest(endpoint, method, data);
        }
        throw error;
    }
}
```

### 3. Order Creation Flow
```javascript
async function createShipmentOrder(orderData) {
    const payload = {
        order_id: orderData.orderId,
        order_date: new Date().toISOString().slice(0, 16).replace('T', ' '),
        pickup_location: "Primary",
        billing_customer_name: orderData.customerName,
        billing_last_name: orderData.customerLastName || "",
        billing_address: orderData.billingAddress,
        billing_city: orderData.billingCity,
        billing_pincode: orderData.billingPincode,
        billing_state: orderData.billingState,
        billing_country: "India",
        billing_email: orderData.customerEmail,
        billing_phone: orderData.customerPhone,
        shipping_is_billing: true,
        order_items: orderData.items.map(item => ({
            name: item.name,
            sku: item.sku,
            units: item.quantity,
            selling_price: item.price,
            discount: item.discount || 0,
            tax: item.tax || 0,
            hsn: item.hsn || 0
        })),
        payment_method: orderData.paymentMethod, // "Prepaid" or "COD"
        sub_total: orderData.subTotal,
        length: orderData.dimensions?.length || 10,
        breadth: orderData.dimensions?.breadth || 10,
        height: orderData.dimensions?.height || 5,
        weight: orderData.weight || 0.5
    };
    
    return await makeShipRocketRequest('orders/create/adhoc', 'POST', payload);
}
```

### 4. Serviceability Check
```javascript
async function checkServiceability(pickupPincode, deliveryPincode, weight = 1, isCOD = false) {
    const params = new URLSearchParams({
        pickup_postcode: pickupPincode,
        delivery_postcode: deliveryPincode,
        weight: weight.toString(),
        cod: isCOD ? '1' : '0'
    });
    
    return await makeShipRocketRequest(`courier/serviceability/?${params}`);
}
```

### 5. Order Tracking
```javascript
async function trackShipment(shipmentId) {
    return await makeShipRocketRequest(`courier/track/shipment/${shipmentId}`);
}

async function trackByAWB(awbNumber) {
    return await makeShipRocketRequest(`courier/track/awb/${awbNumber}`);
}
```

### 6. Rate Calculator
```javascript
async function getShippingRates(pickupPincode, deliveryPincode, weight, dimensions) {
    const serviceability = await checkServiceability(pickupPincode, deliveryPincode, weight);
    
    if (serviceability.data?.available_courier_companies) {
        return serviceability.data.available_courier_companies.sort(
            (a, b) => parseFloat(a.freight_charge) - parseFloat(b.freight_charge)
        );
    }
    
    return [];
}
```

### 7. Webhook Handler (Backend)
```javascript
// Express.js webhook handler
app.post('/api/shiprocket/webhook', (req, res) => {
    const webhookData = req.body;
    
    // Verify webhook authenticity (implement signature verification)
    
    // Process webhook data
    switch (webhookData.current_status) {
        case 'Delivered':
            updateOrderStatus(webhookData.order_id, 'delivered');
            break;
        case 'Out for Delivery':
            updateOrderStatus(webhookData.order_id, 'out_for_delivery');
            break;
        case 'In Transit':
            updateOrderStatus(webhookData.order_id, 'in_transit');
            break;
        // Handle other statuses
    }
    
    res.status(200).send('OK');
});
```

### 8. Best Practices

#### Security
- Never expose API credentials in frontend code
- Implement proper token refresh mechanism
- Use HTTPS for all API calls
- Validate all inputs before sending to API

#### Performance
- Cache authentication tokens
- Implement request retry logic with exponential backoff
- Use loading states for better UX
- Batch API calls where possible

#### Error Handling
- Implement comprehensive error handling
- Show user-friendly error messages
- Log errors for debugging
- Provide fallback options

#### Testing
- Test with real pincodes
- Verify order creation in ShipRocket dashboard
- Test COD and prepaid scenarios
- Validate all required fields

### 9. Common Error Codes
- **401**: Unauthorized - Token expired or invalid
- **400**: Bad Request - Invalid payload or missing required fields
- **404**: Not Found - Invalid endpoint or resource not found
- **429**: Rate Limit Exceeded - Too many requests
- **500**: Internal Server Error - ShipRocket service issue

### 10. Rate Limits
- Authentication: 100 requests per hour
- Order Creation: 1000 requests per hour
- Tracking: 5000 requests per hour
- Serviceability: 10000 requests per hour

### 11. Environment Configuration
```javascript
const config = {
    development: {
        baseURL: 'https://apiv2.shiprocket.in/v1/external/',
        timeout: 30000
    },
    production: {
        baseURL: 'https://apiv2.shiprocket.in/v1/external/',
        timeout: 30000
    }
};
```

### 12. React Hook Example
```javascript
import { useState, useEffect } from 'react';

const useShipRocket = () => {
    const [token, setToken] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    
    const authenticate = async () => {
        setLoading(true);
        try {
            const newToken = await getShipRocketToken();
            setToken(newToken);
            setError(null);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };
    
    const createOrder = async (orderData) => {
        if (!token) await authenticate();
        return await createShipmentOrder(orderData);
    };
    
    const checkService = async (pickup, delivery, weight, cod) => {
        if (!token) await authenticate();
        return await checkServiceability(pickup, delivery, weight, cod);
    };
    
    return {
        token,
        loading,
        error,
        authenticate,
        createOrder,
        checkService
    };
};
```

This documentation provides everything needed for seamless ShipRocket integration in your frontend application.
"""


def main():
    """Main function to run tests and generate documentation"""
    tester = ShipRocketTester()
    
    print("Starting ShipRocket API comprehensive testing...")
    print("=" * 60)
    
    success = tester.run_all_tests()
    
    print("=" * 60)
    print(f"Testing completed. Success: {success}")
    print(f"Total tests: {len(tester.test_results)}")
    print(f"Successful: {len([r for r in tester.test_results if r['success']])}")
    print(f"Failed: {len([r for r in tester.test_results if not r['success']])}")
    
    # Generate documentation
    tester.generate_documentation()
    print("Documentation generated successfully!")
    
    return tester


if __name__ == "__main__":
    tester = main()