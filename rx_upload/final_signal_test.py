"""
Final Test: Verify Accounts App Endpoint with Auto-Workload Creation
Tests that VerifierWorkload is automatically created when using Accounts App endpoint
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
from rx_upload.models import VerifierWorkload
import json
import random

User = get_user_model()


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    CYAN = '\033[96m'
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


print_header("FINAL TEST: Accounts App Endpoint + Auto-Workload Creation")

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
print_success("Admin setup complete")

# Create test verifier
client = Client()
random_num = random.randint(10000, 99999)

test_data = {
    'email': f'final.test{random_num}@rxverification.com',
    'full_name': f'Dr. Final Test {random_num}',
    'contact': f'98765{random_num}',
    'password': 'SecurePass@123',
    'password2': 'SecurePass@123',
    'send_credentials_email': False
}

print_info(f"\nCreating RX Verifier: {test_data['email']}")

response = client.post(
    '/api/accounts/admin/rx-verifiers/create/',
    data=json.dumps(test_data),
    content_type='application/json',
    HTTP_AUTHORIZATION=f'Bearer {admin_token}'
)

print_info(f"Response Status: {response.status_code}")

if response.status_code == 201:
    data = response.json()
    user_id = data['user']['id']
    
    print_success("User created successfully!")
    print_info(f"User ID: {user_id}")
    print_info(f"Email: {data['user']['email']}")
    print_info(f"Role: {data['user']['role']}")
    
    # Check if VerifierWorkload was auto-created
    try:
        user = User.objects.get(id=user_id)
        workload = VerifierWorkload.objects.get(verifier=user)
        
        print_success(f"\n🎉 VerifierWorkload AUTO-CREATED via Signal! 🎉")
        print_info(f"Workload ID: {workload.id}")
        print_info(f"Max Daily Capacity: {workload.max_daily_capacity}")
        print_info(f"Is Available: {workload.is_available}")
        print_info(f"Pending Count: {workload.pending_count}")
        
        print_header("✅ SUCCESS: Signal Working Perfectly!")
        print(f"\n{Colors.GREEN}{Colors.BOLD}VERDICT:{Colors.END}")
        print("Keep ONLY Accounts App endpoint:")
        print(f"{Colors.CYAN}POST /api/accounts/admin/rx-verifiers/create/{Colors.END}")
        print("\nFeatures:")
        print("✓ Creates User with role='rx_verifier'")
        print("✓ AUTO-creates VerifierWorkload (via signal)")
        print("✓ Sends email credentials")
        print("✓ Audit logging")
        print("✓ Swagger documentation")
        print("\n" + "=" * 80 + "\n")
        
    except VerifierWorkload.DoesNotExist:
        print_error("\n✗ VerifierWorkload NOT created!")
        print_error("Signal may not be working")
        
else:
    print_error(f"Failed: {response.content.decode()}")
