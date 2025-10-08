# Email Check API Endpoint

## Overview
This endpoint allows frontend applications to check if an email address is already registered in the system before allowing users to proceed with registration.

## Endpoint Details

### URL
```
POST /api/accounts/check-email/
```

### Authentication
- **Required**: No (Open endpoint)
- **Permission**: `AllowAny`

### Request

#### Headers
```
Content-Type: application/json
```

#### Body Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email` | string (email) | Yes | The email address to check |

#### Example Request
```json
{
    "email": "user@example.com"
}
```

### Response

#### Success Response (200 OK)
```json
{
    "email": "user@example.com",
    "is_registered": true,
    "message": "Email is already registered"
}
```

or

```json
{
    "email": "newuser@example.com",
    "is_registered": false,
    "message": "Email is available"
}
```

#### Response Fields
| Field | Type | Description |
|-------|------|-------------|
| `email` | string | The email address that was checked |
| `is_registered` | boolean | `true` if email exists in system, `false` if available |
| `message` | string | Human-readable message describing the result |

#### Error Responses

##### 400 Bad Request - Invalid Email Format
```json
{
    "email": ["Enter a valid email address."]
}
```

##### 400 Bad Request - Missing Email Field
```json
{
    "email": ["This field is required."]
}
```

##### 405 Method Not Allowed
```json
{
    "detail": "Method \"GET\" not allowed."
}
```

## Usage Examples

### Using JavaScript (Fetch API)
```javascript
async function checkEmail(email) {
    try {
        const response = await fetch('/api/accounts/check-email/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email: email })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            return data.is_registered;
        } else {
            console.error('Email validation error:', data);
            return null;
        }
    } catch (error) {
        console.error('Network error:', error);
        return null;
    }
}

// Usage
const isRegistered = await checkEmail('user@example.com');
if (isRegistered === true) {
    alert('This email is already registered. Please login instead.');
} else if (isRegistered === false) {
    // Proceed with registration
    console.log('Email is available for registration');
}
```

### Using cURL
```bash
# Check existing email
curl -X POST http://localhost:8000/api/accounts/check-email/ \
  -H "Content-Type: application/json" \
  -d '{"email": "existing@example.com"}'

# Check new email
curl -X POST http://localhost:8000/api/accounts/check-email/ \
  -H "Content-Type: application/json" \
  -d '{"email": "new@example.com"}'
```

### Using PowerShell
```powershell
# Check email availability
Invoke-RestMethod -Uri "http://localhost:8000/api/accounts/check-email/" `
  -Method POST `
  -Headers @{"Content-Type" = "application/json"} `
  -Body '{"email": "test@example.com"}'
```

## Implementation Notes

### Case Sensitivity
- The email check is **case insensitive**
- `USER@EXAMPLE.COM` and `user@example.com` are treated as the same email
- This is implemented using Django's `__iexact` lookup

### Validation
- Email format validation is handled by Django's `EmailField`
- Invalid email formats will return a 400 error with validation message
- Empty or missing email field will return appropriate error messages

### Performance
- Simple database query using indexed email field
- Fast response times suitable for real-time validation

## Integration with Registration Flow

This endpoint is designed to be used in the following registration flow:

1. **User enters email** in registration form
2. **Frontend calls check-email endpoint** (optionally with debouncing)
3. **If email exists**: Show message "Email already registered" with login link
4. **If email available**: Allow user to continue with registration form
5. **User completes registration** using the main registration endpoint

## Testing

The endpoint includes comprehensive test coverage:
- Testing with existing emails
- Testing with new emails  
- Email format validation
- Missing field validation
- Case insensitive checking
- HTTP method restrictions

Run tests with:
```bash
python manage.py test accounts.tests.test_email_check
```

## Related Endpoints

- `POST /api/accounts/register/` - User registration
- `POST /api/accounts/login/` - User login
- `POST /api/accounts/login/choice/` - Login with email/password or OTP

## Security Considerations

- This endpoint is intentionally public to support registration flows
- No sensitive user information is exposed
- Only returns boolean existence and email format validation
- Rate limiting should be considered for production deployment