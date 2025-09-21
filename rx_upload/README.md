# MedixMall RX Verifier System

## Complete Documentation & API Guide

### 📋 Table of Contents

1. [System Overview](#system-overview)
2. [RX Verifier Account Management](#rx-verifier-account-management)
3. [Authentication API](#authentication-api)
4. [Prescription Management API](#prescription-management-api)
5. [Verification Workflow API](#verification-workflow-api)
6. [Dashboard & Analytics API](#dashboard--analytics-api)
7. [Email Notification System](#email-notification-system)
8. [Permission System](#permission-system)
9. [Testing Guide](#testing-guide)
10. [Deployment Guide](#deployment-guide)

---

## System Overview

The MedixMall RX Verifier System is a comprehensive prescription verification platform that allows:

- **Customers** to upload prescription images for verification
- **RX Verifiers** to review, approve, reject, or request clarification for prescriptions
- **Admins** to manage verifiers and monitor system performance
- **Automated Email Notifications** for all stakeholders

### 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Customer      │    │   RX Verifier   │    │   Admin         │
│   - Upload RX   │    │   - Review RX   │    │   - Manage      │
│   - Track Status│    │   - Verify RX   │    │   - Monitor     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  RX Upload API  │
                    │  - Prescriptions│
                    │  - Verification │
                    │  - Notifications│
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ImageKit      │    │   Email System  │    │   Database      │
│   - Store Images│    │   - Credentials │    │   - User Data   │
│   - Process RX  │    │   - Notifications│    │   - RX Records  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 🔗 App Installation

Add `rx_upload` to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ... existing apps
    'rx_upload',
]
```

Add URL patterns to main `urls.py`:

```python
urlpatterns = [
    # ... existing patterns
    path('api/rx-upload/', include('rx_upload.urls')),
]
```

---

## RX Verifier Account Management

### 🔧 Creating RX Verifier Accounts

#### Using Django Management Command

```bash
# Create RX verifier with auto-generated password
python manage.py create_rx_verifier \
    --email="verifier@medixmall.com" \
    --full_name="Dr. John Smith" \
    --contact="9876543210" \
    --send-email

# Create RX verifier with custom password
python manage.py create_rx_verifier \
    --email="verifier2@medixmall.com" \
    --full_name="Dr. Jane Doe" \
    --contact="9876543211" \
    --password="CustomPass123!" \
    --send-email
```

#### Command Output

```
✅ RX verifier account created successfully
📧 Email: verifier@medixmall.com
👤 Name: Dr. John Smith
📱 Contact: 9876543210
🔑 Password: Xy9#mN2$kL8P
📧 Credentials sent to verifier@medixmall.com
📊 Workload tracking initialized for Dr. John Smith
```

#### Programmatic Account Creation

```python
from django.contrib.auth import get_user_model
from rx_upload.models import VerifierWorkload
import secrets
import string

User = get_user_model()

# Generate secure password
password = ''.join(secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*") for i in range(12))

# Create RX verifier
verifier = User.objects.create_user(
    email='verifier@medixmall.com',
    password=password,
    full_name='Dr. John Smith',
    contact='9876543210',
    role='rx_verifier',
    email_verified=True
)

# Send credentials via email
success, message = verifier.send_rx_verifier_credentials(password)

# Create workload tracking
VerifierWorkload.objects.create(
    verifier=verifier,
    is_available=True,
    max_daily_capacity=50
)
```

---

## Authentication API

### 🔐 RX Verifier Login

**Endpoint:** `POST /api/rx-upload/auth/login/`

**Description:** Authenticate RX verifier and get session data

**Request Body:**
```json
{
    "email": "verifier@medixmall.com",
    "password": "VerifierPass123!"
}
```

**Success Response (200):**
```json
{
    "success": true,
    "message": "Welcome back, Dr. John Smith!",
    "data": {
        "user": {
            "id": 123,
            "email": "verifier@medixmall.com",
            "full_name": "Dr. John Smith",
            "role": "rx_verifier",
            "last_login": "2024-09-21T10:30:00Z"
        },
        "workload": {
            "pending_count": 5,
            "in_review_count": 3,
            "total_verified": 150,
            "approval_rate": 89.5,
            "is_available": true,
            "can_accept_more": true
        }
    }
}
```

**Error Responses:**
```json
// Invalid credentials (401)
{
    "success": false,
    "message": "Invalid email or password"
}

// Not an RX verifier (403)
{
    "success": false,
    "message": "Access denied. RX Verifier privileges required."
}

// Account inactive (403)
{
    "success": false,
    "message": "Account is inactive. Please contact administrator."
}
```

### 🚪 RX Verifier Logout

**Endpoint:** `POST /api/rx-upload/auth/logout/`

**Description:** Logout RX verifier and clear session

**Headers:** `Authorization: Bearer <token>` or session authentication

**Success Response (200):**
```json
{
    "success": true,
    "message": "Logged out successfully"
}
```

### 👤 RX Verifier Profile

**Endpoint:** `GET /api/rx-upload/auth/profile/`

**Description:** Get RX verifier profile and workload information

**Headers:** `Authorization: Bearer <token>`

**Success Response (200):**
```json
{
    "success": true,
    "data": {
        "user": {
            "id": 123,
            "email": "verifier@medixmall.com",
            "full_name": "Dr. John Smith",
            "contact": "9876543210",
            "role": "rx_verifier",
            "date_joined": "2024-01-15T08:00:00Z",
            "last_login": "2024-09-21T10:30:00Z"
        },
        "workload": {
            "id": 1,
            "verifier_name": "Dr. John Smith",
            "pending_count": 5,
            "in_review_count": 3,
            "total_verified": 150,
            "total_approved": 134,
            "total_rejected": 16,
            "approval_rate": 89.33,
            "average_processing_time": 2.5,
            "is_available": true,
            "max_daily_capacity": 50,
            "current_daily_count": 8,
            "can_accept_more": true,
            "last_activity": "2024-09-21T10:30:00Z"
        }
    }
}
```

---

## Prescription Management API

### 📋 List Prescriptions

**Endpoint:** `GET /api/rx-upload/prescriptions/`

**Description:** List prescriptions (filtered by user role)

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)
- `verification_status`: Filter by status (`pending`, `in_review`, `approved`, `rejected`, `clarification_needed`)
- `is_urgent`: Filter by urgency (`true`, `false`)
- `priority_level`: Filter by priority (1-4)
- `verified_by`: Filter by verifier ID
- `assigned_to_me`: Show only assigned to current verifier (`true`)
- `search`: Search in prescription number, patient name, doctor name, hospital
- `ordering`: Sort by field (`uploaded_at`, `-uploaded_at`, `verification_date`, etc.)

**Headers:** `Authorization: Bearer <token>`

**Example Request:**
```
GET /api/rx-upload/prescriptions/?verification_status=pending&is_urgent=true&page=1&page_size=10
```

**Success Response (200):**
```json
{
    "count": 25,
    "next": "http://api.example.com/rx-upload/prescriptions/?page=2",
    "previous": null,
    "results": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "prescription_number": "RX2024092110301501AB2C",
            "customer": 456,
            "customer_name": "John Customer",
            "customer_email": "customer@example.com",
            "doctor_name": "Dr. Smith",
            "doctor_license": "DL123456",
            "hospital_clinic": "City Hospital",
            "patient_name": "John Customer",
            "patient_age": 35,
            "patient_gender": "male",
            "prescription_type": "image",
            "prescription_image": "https://ik.imagekit.io/prescriptions/customer456/2024/09/prescription.jpg",
            "original_filename": "prescription_scan.jpg",
            "file_size": 245760,
            "diagnosis": "Common cold and fever",
            "medications_prescribed": "Paracetamol 500mg, Cetirizine 10mg",
            "dosage_instructions": "Paracetamol: 1 tablet every 6 hours, Cetirizine: 1 tablet daily",
            "prescription_date": "2024-09-20",
            "prescription_valid_until": "2024-10-20",
            "verification_status": "pending",
            "verified_by": null,
            "verified_by_name": null,
            "verification_date": null,
            "verification_notes": null,
            "customer_notes": "Urgent - patient has high fever",
            "clarification_requested": null,
            "customer_response": null,
            "image_quality_score": null,
            "legibility_score": null,
            "completeness_score": null,
            "uploaded_at": "2024-09-21T10:30:15Z",
            "updated_at": "2024-09-21T10:30:15Z",
            "is_urgent": true,
            "priority_level": 4,
            "customer_phone": "9876543210",
            "alternative_contact": null,
            "medications": [],
            "processing_time": 0.25,
            "can_be_verified": true,
            "is_overdue": false
        }
    ]
}
```

### 📤 Upload Prescription

**Endpoint:** `POST /api/rx-upload/prescriptions/`

**Description:** Upload new prescription (customers only)

**Content-Type:** `multipart/form-data`

**Request Body:**
```json
{
    "patient_name": "John Customer",
    "patient_age": 35,
    "patient_gender": "male",
    "doctor_name": "Dr. Smith",
    "doctor_license": "DL123456",
    "hospital_clinic": "City Hospital",
    "diagnosis": "Common cold and fever",
    "medications_prescribed": "Paracetamol 500mg, Cetirizine 10mg",
    "dosage_instructions": "Take as prescribed",
    "prescription_date": "2024-09-20",
    "prescription_valid_until": "2024-10-20",
    "customer_notes": "Urgent - patient has high fever",
    "is_urgent": true,
    "priority_level": 4,
    "customer_phone": "9876543210",
    "prescription_file": "<binary_file_data>"
}
```

**Success Response (201):**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "prescription_number": "RX2024092110301501AB2C",
    "customer": 456,
    "customer_name": "John Customer",
    "verification_status": "pending",
    "prescription_image": "https://ik.imagekit.io/prescriptions/customer456/2024/09/prescription.jpg",
    "uploaded_at": "2024-09-21T10:30:15Z",
    "can_be_verified": true,
    "is_overdue": false
}
```

### 📄 Get Prescription Details

**Endpoint:** `GET /api/rx-upload/prescriptions/{id}/`

**Description:** Get detailed prescription information

**Headers:** `Authorization: Bearer <token>`

**Success Response (200):**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "prescription_number": "RX2024092110301501AB2C",
    "customer": 456,
    "customer_name": "John Customer",
    "customer_email": "customer@example.com",
    "doctor_name": "Dr. Smith",
    "hospital_clinic": "City Hospital",
    "patient_name": "John Customer",
    "verification_status": "approved",
    "verified_by": 123,
    "verified_by_name": "Dr. John Smith",
    "verification_date": "2024-09-21T11:45:30Z",
    "verification_notes": "Prescription is clear and valid. All medications approved.",
    "processing_time": 1.25,
    "medications": [
        {
            "id": 1,
            "medication_name": "Paracetamol 500mg",
            "dosage": "500mg",
            "frequency": "Every 6 hours",
            "duration": "5 days",
            "quantity": 20,
            "is_verified": true
        }
    ]
}
```

---

## Verification Workflow API

### 📌 Assign Prescription

**Endpoint:** `POST /api/rx-upload/prescriptions/{id}/assign/`

**Description:** Assign prescription to current verifier

**Headers:** `Authorization: Bearer <token>`

**Success Response (200):**
```json
{
    "success": true,
    "message": "Assigned to Dr. John Smith",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "verification_status": "in_review",
        "verified_by": 123,
        "verified_by_name": "Dr. John Smith"
    }
}
```

**Error Responses:**
```json
// Already assigned or not pending (400)
{
    "success": false,
    "message": "Prescription cannot be assigned in current status"
}

// Verifier at capacity (400)
{
    "success": false,
    "message": "You have reached maximum workload capacity"
}
```

### ✅ Approve Prescription

**Endpoint:** `POST /api/rx-upload/prescriptions/{id}/approve/`

**Description:** Approve prescription with optional notes

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
    "notes": "Prescription is clear and valid. All medications approved for dispensing."
}
```

**Success Response (200):**
```json
{
    "success": true,
    "message": "Prescription approved successfully",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "verification_status": "approved",
        "verified_by": 123,
        "verified_by_name": "Dr. John Smith",
        "verification_date": "2024-09-21T11:45:30Z",
        "verification_notes": "Prescription is clear and valid. All medications approved for dispensing."
    }
}
```

### ❌ Reject Prescription

**Endpoint:** `POST /api/rx-upload/prescriptions/{id}/reject/`

**Description:** Reject prescription with required reason

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
    "notes": "Prescription image is unclear and illegible. Doctor's signature is not visible. Please upload a clearer image."
}
```

**Success Response (200):**
```json
{
    "success": true,
    "message": "Prescription rejected",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "verification_status": "rejected",
        "verified_by": 123,
        "verified_by_name": "Dr. John Smith",
        "verification_date": "2024-09-21T11:45:30Z",
        "verification_notes": "Prescription image is unclear and illegible. Doctor's signature is not visible. Please upload a clearer image."
    }
}
```

**Error Response:**
```json
// Missing rejection reason (400)
{
    "success": false,
    "message": "Rejection reason is required"
}
```

### ❓ Request Clarification

**Endpoint:** `POST /api/rx-upload/prescriptions/{id}/clarification/`

**Description:** Request clarification from customer

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
    "message": "Could you please provide a clearer image of the prescription? The dosage section for Paracetamol is not clearly visible. Also, please confirm the patient's age as it appears to be cut off in the image."
}
```

**Success Response (200):**
```json
{
    "success": true,
    "message": "Clarification requested from customer",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "verification_status": "clarification_needed",
        "verified_by": 123,
        "verified_by_name": "Dr. John Smith",
        "verification_date": "2024-09-21T11:45:30Z",
        "clarification_requested": "Could you please provide a clearer image of the prescription? The dosage section for Paracetamol is not clearly visible. Also, please confirm the patient's age as it appears to be cut off in the image."
    }
}
```

---

## Dashboard & Analytics API

### 📊 Verification Dashboard

**Endpoint:** `GET /api/rx-upload/dashboard/`

**Description:** Get comprehensive dashboard data for verifiers/admins

**Headers:** `Authorization: Bearer <token>`

**Success Response (200):**
```json
{
    "success": true,
    "data": {
        "counts": {
            "pending": 25,
            "in_review": 8,
            "approved": 150,
            "rejected": 12,
            "clarification_needed": 5,
            "urgent": 3,
            "overdue": 2
        },
        "recent_activities": [
            {
                "id": 1,
                "prescription_number": "RX2024092110301501AB2C",
                "verifier_name": "Dr. John Smith",
                "action": "approved",
                "description": "Prescription approved by Dr. John Smith",
                "timestamp": "2024-09-21T11:45:30Z"
            }
        ],
        "performance": {
            "total_verified": 162,
            "total_approved": 150,
            "total_rejected": 12,
            "approval_rate": 92.59,
            "average_processing_time": 2.3,
            "current_workload": 13,
            "daily_capacity": 50,
            "current_daily_count": 8
        }
    }
}
```

### 📋 Pending Prescriptions

**Endpoint:** `GET /api/rx-upload/pending/`

**Description:** Get pending prescriptions for assignment (sorted by priority)

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `page`: Page number
- `page_size`: Items per page

**Success Response (200):**
```json
{
    "count": 25,
    "next": "http://api.example.com/rx-upload/pending/?page=2",
    "previous": null,
    "results": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "prescription_number": "RX2024092110301501AB2C",
            "patient_name": "Emergency Patient",
            "is_urgent": true,
            "priority_level": 4,
            "uploaded_at": "2024-09-21T09:15:00Z",
            "processing_time": 2.5,
            "customer_name": "John Customer"
        }
    ]
}
```

### 👥 Verifier Workloads (Admin Only)

**Endpoint:** `GET /api/rx-upload/workloads/`

**Description:** Get all verifier workloads and performance metrics

**Headers:** `Authorization: Bearer <token>` (Admin only)

**Success Response (200):**
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "verifier": 123,
            "verifier_name": "Dr. John Smith",
            "verifier_email": "verifier1@medixmall.com",
            "pending_count": 5,
            "in_review_count": 3,
            "total_verified": 162,
            "total_approved": 150,
            "total_rejected": 12,
            "approval_rate": 92.59,
            "average_processing_time": 2.3,
            "is_available": true,
            "max_daily_capacity": 50,
            "current_daily_count": 8,
            "can_accept_more": true,
            "last_activity": "2024-09-21T11:45:30Z"
        }
    ]
}
```

### 🔄 Update Availability

**Endpoint:** `POST /api/rx-upload/availability/`

**Description:** Update verifier availability status

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
    "is_available": false
}
```

**Success Response (200):**
```json
{
    "success": true,
    "message": "Availability updated to unavailable",
    "data": {
        "id": 1,
        "is_available": false,
        "can_accept_more": false
    }
}
```

---

## Email Notification System

### 📧 RX Verifier Credential Email

**Trigger:** When admin creates new RX verifier account

**Subject:** `🔐 MedixMall RX Verifier Account - Login Credentials`

**Content:**
- Welcome message for new RX verifier
- Login credentials (email and temporary password)
- Security notice to change password
- Responsibilities and access information
- Quick start guide
- Support contact information

**Example HTML Email:**
```html
<h1>🔐 RX Verifier Account</h1>
<h2>Hello Dr. John Smith! 👨‍⚕️</h2>
<p>Your RX Verifier account has been created successfully.</p>

<h3>🔑 Your Login Credentials</h3>
<div style="background: #f7fafc; padding: 20px;">
    <p><strong>Email:</strong> verifier@medixmall.com</p>
    <p><strong>Password:</strong> TempPass123!</p>
    <p><strong>Role:</strong> RX VERIFIER</p>
</div>

<h3>📋 Your Responsibilities:</h3>
<ul>
    <li>Review and verify prescription uploads</li>
    <li>Approve or reject prescription requests</li>
    <li>Add verification notes and comments</li>
    <li>Maintain timely response to pending verifications</li>
</ul>

<p><strong>Login URL:</strong> <a href="https://backend.okpuja.in/api/rx-upload/auth/login/">RX Verifier Portal</a></p>
```

### ✅ Prescription Approval Email

**Trigger:** When prescription is approved

**Subject:** `Prescription Verification Update - RX2024092110301501AB2C`

**Content:**
```
Dear John Customer,

Your prescription (#RX2024092110301501AB2C) has been approved by our medical team.

Status: ✅ APPROVED
Verified by: Dr. John Smith
Verification Date: September 21, 2024 at 11:45 AM

You can now proceed with your medication order.

Verifier Notes: Prescription is clear and valid. All medications approved for dispensing.

Thank you for choosing MedixMall!
```

### ❌ Prescription Rejection Email

**Trigger:** When prescription is rejected

**Subject:** `Prescription Verification Update - RX2024092110301501AB2C`

**Content:**
```
Dear John Customer,

Unfortunately, your prescription (#RX2024092110301501AB2C) could not be approved.

Status: ❌ REJECTED
Verified by: Dr. John Smith
Verification Date: September 21, 2024 at 11:45 AM

Reason: Prescription image is unclear and illegible. Doctor's signature is not visible. Please upload a clearer image.

You may upload a new, clearer prescription or contact our support team.

Support: rx-support@medixmall.com
Phone: +91 8002-8002-80
```

### ❓ Clarification Request Email

**Trigger:** When clarification is requested

**Subject:** `Clarification Needed - Prescription RX2024092110301501AB2C`

**Content:**
```
Dear John Customer,

Our medical team needs additional clarification for your prescription (#RX2024092110301501AB2C).

Status: ⏳ CLARIFICATION NEEDED
Reviewed by: Dr. John Smith

Request:
Could you please provide a clearer image of the prescription? The dosage section for Paracetamol is not clearly visible. Also, please confirm the patient's age as it appears to be cut off in the image.

Please provide the requested information by:
1. Replying to this email with details
2. Calling our support: +91 8002-8002-80
3. Uploading additional documents if needed

We'll review your response and update the verification status accordingly.
```

---

## Permission System

### 🔐 User Roles & Permissions

| Role | Description | Permissions |
|------|-------------|-------------|
| `user` | Regular customer | Upload prescriptions, view own prescriptions |
| `supplier` | Medicine supplier | Existing supplier permissions |
| `admin` | System administrator | Full access to all features |
| `rx_verifier` | Prescription verifier | Verify prescriptions, manage workload |

### 🛡️ Permission Classes

#### `IsRXVerifier`
- Only authenticated RX verifiers
- Used for verifier-specific endpoints

#### `IsRXVerifierOrAdmin`
- RX verifiers and admins
- Used for verification management

#### `IsOwnerOrRXVerifierOrAdmin`
- Object owner, RX verifiers, or admins
- Used for prescription access control

#### `CanVerifyPrescription`
- Only RX verifiers and admins can verify
- Used for verification actions

### 🔒 API Endpoint Permissions

| Endpoint | Method | Permission Required |
|----------|--------|-------------------|
| `/auth/login/` | POST | None (public) |
| `/auth/logout/` | POST | IsRXVerifier |
| `/auth/profile/` | GET | IsRXVerifier |
| `/prescriptions/` | GET | IsRXVerifierOrAdmin |
| `/prescriptions/` | POST | IsAuthenticated |
| `/prescriptions/{id}/` | GET/PUT/DELETE | IsOwnerOrRXVerifierOrAdmin |
| `/prescriptions/{id}/assign/` | POST | CanVerifyPrescription |
| `/prescriptions/{id}/approve/` | POST | CanVerifyPrescription |
| `/prescriptions/{id}/reject/` | POST | CanVerifyPrescription |
| `/prescriptions/{id}/clarification/` | POST | CanVerifyPrescription |
| `/dashboard/` | GET | IsRXVerifierOrAdmin |
| `/pending/` | GET | IsRXVerifierOrAdmin |
| `/workloads/` | GET | IsAdmin |
| `/availability/` | POST | IsRXVerifier |

---

## Testing Guide

### 🧪 Running Tests

```bash
# Run all RX upload tests
python manage.py test rx_upload

# Run specific test file
python manage.py test rx_upload.rx_verifier_system_test

# Run with coverage
coverage run --source='.' manage.py test rx_upload
coverage report
coverage html
```

### 📋 Test Scenarios Covered

1. **Account Management**
   - RX verifier account creation via command
   - Email credential sending
   - Workload initialization

2. **Authentication**
   - Valid login with correct credentials
   - Invalid login attempts
   - Non-verifier access denial
   - Logout functionality

3. **Prescription Upload**
   - Customer prescription upload
   - File handling and ImageKit integration
   - Automatic prescription number generation

4. **Verification Workflow**
   - Prescription assignment to verifier
   - Approval with notes
   - Rejection with reasons
   - Clarification requests

5. **Email Notifications**
   - Credential emails for new verifiers
   - Approval notifications to customers
   - Rejection notifications with reasons
   - Clarification request emails

6. **Dashboard & Analytics**
   - Verifier dashboard data
   - Pending prescription lists
   - Performance metrics calculation
   - Admin workload overview

7. **Permission System**
   - Role-based access control
   - API endpoint security
   - Object-level permissions

8. **Search & Filtering**
   - Prescription search by various fields
   - Status and priority filtering
   - Pagination handling

9. **Performance Tracking**
   - Processing time calculation
   - Approval rate metrics
   - Workload capacity management

10. **Error Handling**
    - Invalid requests handling
    - Edge case scenarios
    - Capacity limit enforcement

### 🔬 Sample Test Code

```python
def test_complete_verification_workflow(self):
    """Test end-to-end prescription verification"""
    # 1. Customer uploads prescription
    self.client.force_authenticate(user=self.customer)
    prescription_data = {
        'patient_name': 'Test Patient',
        'doctor_name': 'Dr. Test',
        'diagnosis': 'Test condition'
    }
    response = self.client.post('/api/rx-upload/prescriptions/', prescription_data)
    self.assertEqual(response.status_code, 201)
    
    prescription_id = response.json()['id']
    
    # 2. Verifier assigns prescription
    self.client.force_authenticate(user=self.rx_verifier)
    response = self.client.post(f'/api/rx-upload/prescriptions/{prescription_id}/assign/')
    self.assertEqual(response.status_code, 200)
    
    # 3. Verifier approves prescription
    approval_data = {'notes': 'Prescription approved'}
    response = self.client.post(f'/api/rx-upload/prescriptions/{prescription_id}/approve/', approval_data)
    self.assertEqual(response.status_code, 200)
    
    # 4. Verify email was sent
    self.assertEqual(len(mail.outbox), 1)
    self.assertIn('APPROVED', mail.outbox[0].body)
```

---

## Deployment Guide

### 🚀 Production Setup

#### 1. Add App to Settings

```python
# settings.py
INSTALLED_APPS = [
    # ... existing apps
    'rx_upload',
]

# Add URL include
ROOT_URLCONF = 'ecommerce.urls'
```

#### 2. Database Migration

```bash
# Create migrations
python manage.py makemigrations rx_upload

# Apply migrations
python manage.py migrate rx_upload

# Create admin superuser if needed
python manage.py createsuperuser
```

#### 3. Create Initial RX Verifiers

```bash
# Create first RX verifier
python manage.py create_rx_verifier \
    --email="head.verifier@medixmall.com" \
    --full_name="Dr. Head Verifier" \
    --contact="9999999999" \
    --send-email

# Create additional verifiers as needed
python manage.py create_rx_verifier \
    --email="verifier2@medixmall.com" \
    --full_name="Dr. Second Verifier" \
    --contact="9999999998" \
    --send-email
```

#### 4. Configure Email Settings

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # Or your SMTP server
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'MedixMall <noreply@medixmall.com>'
```

#### 5. ImageKit Configuration

```python
# settings.py (already configured in accounts/models.py)
IMAGEKIT_PRIVATE_KEY = 'your_imagekit_private_key'
IMAGEKIT_PUBLIC_KEY = 'your_imagekit_public_key'
IMAGEKIT_URL_ENDPOINT = 'https://ik.imagekit.io/your_endpoint'
```

#### 6. URL Configuration

```python
# ecommerce/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # ... existing patterns
    path('api/rx-upload/', include('rx_upload.urls')),
]
```

### 📊 Monitoring & Maintenance

#### Daily Tasks
```bash
# Check pending prescriptions
python manage.py shell -c "
from rx_upload.models import PrescriptionUpload
pending_count = PrescriptionUpload.objects.filter(verification_status='pending').count()
overdue_count = PrescriptionUpload.objects.filter(
    verification_status__in=['pending', 'in_review'],
    uploaded_at__lt=timezone.now() - timedelta(hours=24)
).count()
print(f'Pending: {pending_count}, Overdue: {overdue_count}')
"

# Update all verifier workloads
python manage.py shell -c "
from rx_upload.models import VerifierWorkload
for workload in VerifierWorkload.objects.all():
    workload.update_workload()
print('All workloads updated')
"
```

#### Weekly Reports
```python
# Generate weekly performance report
from rx_upload.models import VerifierWorkload, PrescriptionUpload
from django.utils import timezone
from datetime import timedelta

week_ago = timezone.now() - timedelta(days=7)

# Get weekly stats
weekly_uploads = PrescriptionUpload.objects.filter(uploaded_at__gte=week_ago).count()
weekly_approved = PrescriptionUpload.objects.filter(
    verification_date__gte=week_ago,
    verification_status='approved'
).count()
weekly_rejected = PrescriptionUpload.objects.filter(
    verification_date__gte=week_ago,
    verification_status='rejected'
).count()

print(f"Weekly Report:")
print(f"Uploads: {weekly_uploads}")
print(f"Approved: {weekly_approved}")
print(f"Rejected: {weekly_rejected}")
print(f"Approval Rate: {(weekly_approved/(weekly_approved+weekly_rejected)*100):.1f}%")
```

### 🔧 Environment Variables

```bash
# .env file additions
IMAGEKIT_PRIVATE_KEY=your_imagekit_private_key
IMAGEKIT_PUBLIC_KEY=your_imagekit_public_key  
IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/your_endpoint

EMAIL_HOST_USER=your-smtp-email@gmail.com
EMAIL_HOST_PASSWORD=your-smtp-password

# Optional: Twilio for SMS (if implementing)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890
```

---

## 📈 API Usage Examples

### Frontend Integration Examples

#### React/JavaScript
```javascript
// Login RX Verifier
const loginVerifier = async (email, password) => {
    const response = await fetch('/api/rx-upload/auth/login/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ email, password })
    });
    
    if (response.ok) {
        const data = await response.json();
        console.log('Login successful:', data.data.user);
        return data;
    } else {
        throw new Error('Login failed');
    }
};

// Upload Prescription
const uploadPrescription = async (formData) => {
    const response = await fetch('/api/rx-upload/prescriptions/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken()
        },
        body: formData  // FormData with file
    });
    
    return response.json();
};

// Get Dashboard Data
const getDashboard = async () => {
    const response = await fetch('/api/rx-upload/dashboard/', {
        headers: {
            'Authorization': `Bearer ${getAuthToken()}`
        }
    });
    
    return response.json();
};
```

#### Python Client
```python
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

class RXVerifierClient:
    def __init__(self, base_url, session_id=None):
        self.base_url = base_url
        self.session = requests.Session()
        if session_id:
            self.session.cookies.set('sessionid', session_id)
    
    def login(self, email, password):
        """Login as RX verifier"""
        response = self.session.post(f'{self.base_url}/auth/login/', {
            'email': email,
            'password': password
        })
        return response.json()
    
    def get_pending_prescriptions(self):
        """Get pending prescriptions"""
        response = self.session.get(f'{self.base_url}/pending/')
        return response.json()
    
    def approve_prescription(self, prescription_id, notes=""):
        """Approve prescription"""
        response = self.session.post(
            f'{self.base_url}/prescriptions/{prescription_id}/approve/',
            {'notes': notes}
        )
        return response.json()
    
    def upload_prescription(self, file_path, patient_name, doctor_name):
        """Upload prescription file"""
        with open(file_path, 'rb') as f:
            multipart_data = MultipartEncoder(
                fields={
                    'patient_name': patient_name,
                    'doctor_name': doctor_name,
                    'prescription_file': (file_path, f, 'image/jpeg')
                }
            )
            
            response = self.session.post(
                f'{self.base_url}/prescriptions/',
                data=multipart_data,
                headers={'Content-Type': multipart_data.content_type}
            )
        return response.json()

# Usage
client = RXVerifierClient('https://api.medixmall.com/api/rx-upload')
login_result = client.login('verifier@medixmall.com', 'password123')
pending = client.get_pending_prescriptions()
```

---

## 📞 Support & Contact

### Technical Support
- **Email:** rx-support@medixmall.com
- **Phone:** +91 8002-8002-80 (Ext: 101)
- **Internal Chat:** Available in verifier portal

### Documentation Updates
This documentation is maintained in the `rx_upload` app folder and should be updated with any API changes.

### API Versioning
Current API Version: `v1`
Base URL: `/api/rx-upload/`

---

**Last Updated:** September 21, 2024  
**Version:** 1.0.0  
**Author:** MedixMall Development Team