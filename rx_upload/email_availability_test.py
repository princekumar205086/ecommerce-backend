"""
Test Email Availability Check Endpoint
Tests the new endpoint for checking if an email is available before creating RX verifier
"""
import os
import django
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
import json

User = get_user_model()


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_info(message):
    print(f"{Colors.CYAN}ℹ {message}{Colors.END}")


def print_header(message):
    print(f"\n{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{message.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 80}{Colors.END}\n")


print_header("EMAIL AVAILABILITY CHECK - COMPREHENSIVE TEST")

# Setup admin
admin_user, _ = User.objects.get_or_create(
    email='admin@example.com',
    defaults={
        'full_name': 'Admin',
        'role': 'admin',
        'is_staff': True,
        'is_superuser': True
    }
)
admin_token = str(AccessToken.for_user(admin_user))
client = Client()

print_success("Admin setup complete\n")

# Test 1: Check available email
print_info("Test 1: Check Available Email")
response = client.get(
    '/api/accounts/admin/rx-verifiers/check-email/?email=newverifier@example.com',
    HTTP_AUTHORIZATION=f'Bearer {admin_token}'
)
print_info(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print_info(f"Response: {json.dumps(data, indent=2)}")
    if data['available']:
        print_success("✓ Email is available")
    else:
        print_error("✗ Email is not available")
else:
    print_error(f"Failed: {response.content.decode()}")

# Test 2: Check existing email
print_info("\nTest 2: Check Existing Email")
response = client.get(
    '/api/accounts/admin/rx-verifiers/check-email/?email=admin@example.com',
    HTTP_AUTHORIZATION=f'Bearer {admin_token}'
)
print_info(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print_info(f"Response: {json.dumps(data, indent=2)}")
    if not data['available']:
        print_success("✓ Correctly identified existing email")
        if 'existing_user' in data:
            print_info(f"   Existing user: {data['existing_user']['full_name']} ({data['existing_user']['role']})")
    else:
        print_error("✗ Should have identified email as taken")
else:
    print_error(f"Failed: {response.content.decode()}")

# Test 3: Invalid email format
print_info("\nTest 3: Invalid Email Format")
response = client.get(
    '/api/accounts/admin/rx-verifiers/check-email/?email=invalid-email',
    HTTP_AUTHORIZATION=f'Bearer {admin_token}'
)
print_info(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print_info(f"Response: {json.dumps(data, indent=2)}")
    if not data['available'] and 'Invalid' in data['message']:
        print_success("✓ Correctly identified invalid email format")
    else:
        print_error("✗ Should have identified invalid format")
else:
    print_error(f"Failed: {response.content.decode()}")

# Test 4: Missing email parameter
print_info("\nTest 4: Missing Email Parameter")
response = client.get(
    '/api/accounts/admin/rx-verifiers/check-email/',
    HTTP_AUTHORIZATION=f'Bearer {admin_token}'
)
print_info(f"Status: {response.status_code}")
if response.status_code == 400:
    data = response.json()
    print_success("✓ Correctly returned 400 for missing parameter")
    print_info(f"   Error: {data.get('error')}")
else:
    print_error(f"Expected 400, got {response.status_code}")

# Test 5: Case-insensitive check
print_info("\nTest 5: Case-Insensitive Email Check")
response = client.get(
    '/api/accounts/admin/rx-verifiers/check-email/?email=ADMIN@EXAMPLE.COM',
    HTTP_AUTHORIZATION=f'Bearer {admin_token}'
)
print_info(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    if not data['available']:
        print_success("✓ Case-insensitive check working correctly")
    else:
        print_error("✗ Should have matched admin@example.com")
else:
    print_error(f"Failed: {response.content.decode()}")

print_header("✅ ALL TESTS COMPLETED")

# Print usage example
print(f"\n{Colors.BOLD}Usage Example (Frontend):{Colors.END}\n")
print("""
// JavaScript/Axios
const checkEmailAvailability = async (email) => {
    try {
        const response = await axios.get(
            `/api/accounts/admin/rx-verifiers/check-email/?email=${email}`,
            {
                headers: {
                    'Authorization': `Bearer ${adminToken}`
                }
            }
        );
        
        if (response.data.available) {
            console.log('✓ Email is available');
            return true;
        } else {
            console.log('✗ Email already exists');
            if (response.data.existing_user) {
                console.log(`Found: ${response.data.existing_user.full_name}`);
            }
            return false;
        }
    } catch (error) {
        console.error('Error checking email:', error);
        return false;
    }
};

// React Component Example
const EmailInput = () => {
    const [email, setEmail] = useState('');
    const [isAvailable, setIsAvailable] = useState(null);
    const [isChecking, setIsChecking] = useState(false);
    
    const handleEmailCheck = async () => {
        setIsChecking(true);
        const available = await checkEmailAvailability(email);
        setIsAvailable(available);
        setIsChecking(false);
    };
    
    return (
        <div>
            <input 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onBlur={handleEmailCheck}
            />
            {isChecking && <span>Checking...</span>}
            {isAvailable === true && <span style={{color: 'green'}}>✓ Available</span>}
            {isAvailable === false && <span style={{color: 'red'}}>✗ Already exists</span>}
        </div>
    );
};
""")

print(f"\n{Colors.BOLD}API Documentation:{Colors.END}")
print("""
GET /api/accounts/admin/rx-verifiers/check-email/

Query Parameters:
  email (required): Email address to check

Response (200 OK):
  {
      "available": true|false,
      "email": "test@example.com",
      "message": "Email is available for registration" | "Email already exists",
      "existing_user": {  // Only if email exists
          "id": 123,
          "email": "test@example.com",
          "full_name": "Dr. Test",
          "role": "rx_verifier",
          "is_active": true,
          "date_joined": "2024-11-07T..."
      }
  }
""")
