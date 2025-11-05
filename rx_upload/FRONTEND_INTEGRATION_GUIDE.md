# 🚀 RX Upload - Frontend Quick Start Guide

## Base URL
```
Development: http://localhost:8000/api/rx-upload
Production: https://your-domain.com/api/rx-upload
```

## Authentication
Include in all requests:
```javascript
headers: {
  'Authorization': 'Bearer YOUR_JWT_TOKEN',
  // or use session authentication
}
```

---

## 📸 Frontend Flow (From Screenshots)

### Screen 1: Upload Prescription

**Endpoint**: `POST /customer/upload/`

```javascript
const formData = new FormData();
formData.append('prescription_file', selectedFile);

const response = await fetch('/api/rx-upload/customer/upload/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
  },
  body: formData
});

const data = await response.json();
// Save: data.data.prescription_id for next steps
```

**Response**:
```json
{
  "success": true,
  "data": {
    "prescription_id": "uuid-here",
    "prescription_number": "RX202501051430...",
    "prescription_image": "https://imagekit.io/...",
    "uploaded_at": "2025-01-05T14:30:45Z"
  }
}
```

---

### Screen 2: Patient Information

**Endpoint**: `POST /customer/{prescription_id}/patient-info/`

```javascript
const patientData = {
  patient_name: "John Doe",           // Required
  customer_phone: "9876543210",       // Required, 10 digits
  patient_age: 30,                    // Optional
  patient_gender: "male",             // Optional: male/female/other
  emergency_contact: "9123456789"     // Optional
};

const response = await fetch(`/api/rx-upload/customer/${prescriptionId}/patient-info/`, {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(patientData)
});
```

**Validation**:
- ✅ `patient_name`: Required
- ✅ `customer_phone`: Required, exactly 10 digits
- ✅ Show error if phone invalid

---

### Screen 3: Delivery & Address

#### Get Addresses
```javascript
const response = await fetch('/api/rx-upload/customer/addresses/', {
  headers: {
    'Authorization': 'Bearer ' + token,
  }
});

const data = await response.json();
// data.data contains array of addresses
```

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "type": "home",
      "full_name": "Admin User",
      "phone": "1234567890",
      "formatted_address": "Rohini, Sector 5, Purnia, Bihar - 854301",
      "is_default": true
    }
  ]
}
```

#### Get Delivery Options
```javascript
const response = await fetch('/api/rx-upload/customer/delivery-options/', {
  headers: {
    'Authorization': 'Bearer ' + token,
  }
});
```

**Response**:
```json
{
  "success": true,
  "data": {
    "options": [
      {
        "id": "express",
        "name": "Express Delivery",
        "description": "Get your medicines within 2-4 hours",
        "price": 99.00,
        "estimated_delivery": "2-4 hours"
      },
      {
        "id": "standard",
        "name": "Standard Delivery",
        "price": 49.00,
        "estimated_delivery": "24 hours"
      },
      {
        "id": "free",
        "name": "Free Delivery",
        "price": 0.00,
        "estimated_delivery": "2-3 days"
      }
    ]
  }
}
```

---

### Screen 4: Order Summary & Submit

#### Get Summary
```javascript
const response = await fetch(`/api/rx-upload/customer/${prescriptionId}/summary/`, {
  headers: {
    'Authorization': 'Bearer ' + token,
  }
});
```

**Response**:
```json
{
  "success": true,
  "data": {
    "prescription_files": 1,
    "patient": "John Doe",
    "delivery_address": "home address",
    "can_submit": true,
    "missing_fields": []
  }
}
```

#### Submit Order
```javascript
const orderData = {
  delivery_address_id: selectedAddressId,  // Required
  delivery_option: "express",              // Required: express/standard/free
  payment_method: "cod",                   // Optional, default: cod
  customer_notes: "Please deliver ASAP"    // Optional
};

const response = await fetch(`/api/rx-upload/customer/${prescriptionId}/submit/`, {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(orderData)
});
```

**Success Response**:
```json
{
  "success": true,
  "message": "Prescription order submitted successfully",
  "data": {
    "order_id": "RX202501051430...",
    "delivery_charge": 99.00,
    "estimated_delivery": "2-4 hours",
    "status": "pending_verification",
    "message": "Your prescription is being verified by our pharmacist..."
  }
}
```

---

## 🎨 UI Components Guide

### Upload Section
```jsx
<div className="upload-box">
  <input 
    type="file" 
    accept=".jpg,.jpeg,.png,.pdf" 
    onChange={handleFileSelect}
    max-size="10MB"
  />
  <p>Drag and drop your prescription images or PDFs here, or click to browse</p>
  <p className="hint">Supported formats: JPEG, PNG, PDF. Max size: 10MB.</p>
</div>

{/* Preview */}
{uploadedFile && (
  <div className="preview">
    <img src={prescriptionImageUrl} alt="Prescription" />
    <button onClick={handleRemove}>✕</button>
  </div>
)}
```

### Patient Information Form
```jsx
<form onSubmit={handlePatientInfo}>
  <input 
    type="text" 
    placeholder="Enter patient's full name" 
    required 
  />
  <input 
    type="tel" 
    placeholder="Enter 10-digit mobile number"
    pattern="[0-9]{10}"
    maxLength="10"
    required
  />
  <input 
    type="number" 
    placeholder="Age (Optional)"
  />
  <select name="gender">
    <option value="">Select Gender (Optional)</option>
    <option value="male">Male</option>
    <option value="female">Female</option>
    <option value="other">Other</option>
  </select>
</form>
```

### Address Cards
```jsx
{addresses.map(addr => (
  <div 
    key={addr.id} 
    className={`address-card ${addr.is_default ? 'default' : ''}`}
    onClick={() => selectAddress(addr.id)}
  >
    <span className="type">{addr.type}</span>
    {addr.is_default && <span className="badge">Default</span>}
    <h4>{addr.full_name}</h4>
    <p>{addr.formatted_address}</p>
    <p>{addr.phone}</p>
  </div>
))}
```

### Delivery Options
```jsx
{deliveryOptions.map(option => (
  <div 
    key={option.id}
    className={`delivery-option ${selected === option.id ? 'selected' : ''}`}
    onClick={() => selectDelivery(option.id)}
  >
    <div className="icon">{option.icon}</div>
    <div className="info">
      <h4>{option.name}</h4>
      <p>{option.description}</p>
      <p className="time">{option.estimated_delivery}</p>
    </div>
    <div className="price">₹{option.price}</div>
  </div>
))}
```

### Order Summary
```jsx
<div className="order-summary">
  <h3>Order Summary</h3>
  <div className="row">
    <span>Prescription Files</span>
    <span>{summary.prescription_files} file</span>
  </div>
  <div className="row">
    <span>Patient</span>
    <span>{summary.patient || 'Not specified'}</span>
  </div>
  <div className="row">
    <span>Delivery Address</span>
    <span>{summary.delivery_address || 'Not selected'}</span>
  </div>
  <div className="row">
    <span>Delivery</span>
    <span>{summary.delivery_option || 'Not selected'}</span>
  </div>
  
  <button 
    disabled={!summary.can_submit}
    onClick={handleSubmit}
  >
    Submit Prescription Order
  </button>
  
  {summary.missing_fields.length > 0 && (
    <p className="warning">
      Please complete: {summary.missing_fields.join(', ')}
    </p>
  )}
</div>
```

---

## ⚠️ Error Handling

```javascript
async function handleApiCall() {
  try {
    const response = await fetch(endpoint, options);
    const data = await response.json();
    
    if (!data.success) {
      // Show error message
      showError(data.message);
      
      // Show field errors
      if (data.errors) {
        Object.keys(data.errors).forEach(field => {
          showFieldError(field, data.errors[field][0]);
        });
      }
      return;
    }
    
    // Success handling
    handleSuccess(data);
    
  } catch (error) {
    showError('Network error. Please check your connection.');
  }
}
```

### Common Error Responses

**400 - Validation Error**:
```json
{
  "success": false,
  "message": "Phone number is required",
  "errors": {
    "customer_phone": ["This field is required."]
  }
}
```

**401 - Authentication Required**:
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**404 - Not Found**:
```json
{
  "success": false,
  "message": "Prescription not found"
}
```

---

## 🔄 Complete Flow Example

```javascript
class PrescriptionOrderFlow {
  constructor() {
    this.prescriptionId = null;
    this.token = localStorage.getItem('authToken');
  }
  
  // Step 1
  async uploadPrescription(file) {
    const formData = new FormData();
    formData.append('prescription_file', file);
    
    const response = await this.apiCall('POST', '/customer/upload/', formData);
    this.prescriptionId = response.data.prescription_id;
    return response;
  }
  
  // Step 2
  async addPatientInfo(data) {
    return await this.apiCall(
      'POST', 
      `/customer/${this.prescriptionId}/patient-info/`,
      JSON.stringify(data)
    );
  }
  
  // Step 3
  async getAddresses() {
    return await this.apiCall('GET', '/customer/addresses/');
  }
  
  async getDeliveryOptions() {
    return await this.apiCall('GET', '/customer/delivery-options/');
  }
  
  // Step 4
  async getSummary() {
    return await this.apiCall('GET', `/customer/${this.prescriptionId}/summary/`);
  }
  
  async submitOrder(orderData) {
    return await this.apiCall(
      'POST',
      `/customer/${this.prescriptionId}/submit/`,
      JSON.stringify(orderData)
    );
  }
  
  // Helper
  async apiCall(method, endpoint, body = null) {
    const options = {
      method,
      headers: {
        'Authorization': `Bearer ${this.token}`,
      }
    };
    
    if (body && typeof body === 'string') {
      options.headers['Content-Type'] = 'application/json';
      options.body = body;
    } else if (body instanceof FormData) {
      options.body = body;
    }
    
    const response = await fetch(`/api/rx-upload${endpoint}`, options);
    return await response.json();
  }
}

// Usage
const flow = new PrescriptionOrderFlow();

// Upload
await flow.uploadPrescription(file);

// Patient info
await flow.addPatientInfo({
  patient_name: "John Doe",
  customer_phone: "9876543210"
});

// Get options
const addresses = await flow.getAddresses();
const deliveryOptions = await flow.getDeliveryOptions();

// Submit
await flow.submitOrder({
  delivery_address_id: 1,
  delivery_option: "express",
  payment_method: "cod"
});
```

---

## ✅ Testing Checklist

- [ ] File upload with valid image
- [ ] File upload with PDF
- [ ] File upload with > 10MB (should fail)
- [ ] Patient info with required fields only
- [ ] Patient info with all fields
- [ ] Invalid phone number (should fail)
- [ ] Get addresses
- [ ] Get delivery options
- [ ] Submit with all data
- [ ] Submit without address (should fail)
- [ ] View order summary
- [ ] View prescription history

---

## 📞 Support

Need help? Check:
1. **API_DOCUMENTATION.md** - Complete API reference
2. **IMPLEMENTATION_SUMMARY.md** - Technical overview
3. **simple_model_test.py** - Example usage

---

**Status**: ✅ Ready for Integration
**Last Updated**: November 5, 2025
