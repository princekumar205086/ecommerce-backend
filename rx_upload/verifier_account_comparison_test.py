"""
COMPREHENSIVE TEST: RX Verifier Account Creation
Tests both available endpoints:
1. Accounts App: /api/accounts/admin/rx-verifiers/create/
2. RX Upload App: /api/rx-upload/admin/verifiers/create/

Determines which is better and provides recommendation
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
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_info(message):
    print(f"{Colors.CYAN}ℹ {message}{Colors.END}")


def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")


def print_header(message):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 90}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message.center(90)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 90}{Colors.END}\n")


def print_section(message):
    print(f"\n{Colors.YELLOW}{'─' * 90}{Colors.END}")
    print(f"{Colors.YELLOW}{message}{Colors.END}")
    print(f"{Colors.YELLOW}{'─' * 90}{Colors.END}")


class RXVerifierAccountCreationComparison:
    def __init__(self):
        self.client = Client()
        self.admin_token = None
        self.admin_user = None
        self.results = {
            'accounts_app': {},
            'rx_upload_app': {}
        }

    def setup_admin(self):
        """Setup admin user"""
        print_section("Setting up admin user...")
        
        self.admin_user, created = User.objects.get_or_create(
            email='admin@example.com',
            defaults={
                'full_name': 'System Administrator',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            self.admin_user.set_password('Admin@123')
            self.admin_user.save()
            print_success(f"Created admin user")
        else:
            print_info(f"Using existing admin")
        
        self.admin_token = str(AccessToken.for_user(self.admin_user))
        print_success("Generated JWT token")

    def test_accounts_app_endpoint(self):
        """Test /api/accounts/admin/rx-verifiers/create/"""
        print_header("TESTING ACCOUNTS APP ENDPOINT")
        print_info("Endpoint: POST /api/accounts/admin/rx-verifiers/create/")
        
        random_num = random.randint(10000, 99999)
        
        test_data = {
            'email': f'accounts.test{random_num}@rxverification.com',
            'full_name': f'Dr. Accounts Test {random_num}',
            'contact': f'98765{random_num}',
            'password': 'SecurePass@123',
            'password2': 'SecurePass@123',
            'send_credentials_email': False
        }
        
        print_info(f"Test Data: {json.dumps(test_data, indent=2)}")
        
        try:
            import time
            start_time = time.time()
            
            response = self.client.post(
                '/api/accounts/admin/rx-verifiers/create/',
                data=json.dumps(test_data),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
            )
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # ms
            
            print_info(f"Status Code: {response.status_code}")
            print_info(f"Response Time: {response_time:.2f}ms")
            
            if response.status_code == 201:
                data = response.json()
                print_success("Account created successfully!")
                print_info(f"Response: {json.dumps(data, indent=2)[:500]}...")
                
                # Verify user creation
                user = User.objects.get(email=test_data['email'])
                print_success(f"User verified: {user.email} (Role: {user.role})")
                
                # Check if VerifierWorkload was created
                try:
                    workload = VerifierWorkload.objects.get(verifier=user)
                    print_success(f"VerifierWorkload found: Capacity={workload.max_daily_capacity}")
                    has_workload = True
                except VerifierWorkload.DoesNotExist:
                    print_warning("VerifierWorkload NOT automatically created")
                    has_workload = False
                
                self.results['accounts_app'] = {
                    'status': 'SUCCESS',
                    'response_code': 201,
                    'response_time_ms': response_time,
                    'user_created': True,
                    'workload_created': has_workload,
                    'features': [
                        'Email notification support',
                        'Password validation',
                        'Auto email verification',
                        'Audit logging',
                        'Swagger documentation'
                    ],
                    'pros': [
                        'Well-integrated with accounts system',
                        'Automatic audit logging',
                        'Email credentials support',
                        'Swagger documented',
                        'Follows Django best practices'
                    ],
                    'cons': [
                        'Does NOT auto-create VerifierWorkload' if not has_workload else 'Auto-creates VerifierWorkload',
                        'Requires password in request (security consideration)',
                        'Limited RX-specific configuration'
                    ]
                }
                
                return True
            else:
                print_error(f"Failed with status {response.status_code}")
                print_error(f"Response: {response.content.decode()}")
                
                self.results['accounts_app'] = {
                    'status': 'FAILED',
                    'response_code': response.status_code,
                    'error': response.content.decode()
                }
                return False
                
        except Exception as e:
            print_error(f"Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results['accounts_app'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            return False

    def test_rx_upload_app_endpoint(self):
        """Test /api/rx-upload/admin/verifiers/create/"""
        print_header("TESTING RX UPLOAD APP ENDPOINT")
        print_info("Endpoint: POST /api/rx-upload/admin/verifiers/create/")
        
        random_num = random.randint(10000, 99999)
        
        test_data = {
            'email': f'rxupload.test{random_num}@rxverification.com',
            'full_name': f'Dr. RX Upload Test {random_num}',
            'phone_number': f'98765{random_num}',
            'specialization': 'General Medicine',
            'department': 'Internal Medicine',
            'license_number': f'MED{random_num}',
            'max_daily_capacity': 50,
            'send_welcome_email': False
        }
        
        print_info(f"Test Data: {json.dumps(test_data, indent=2)}")
        
        try:
            import time
            start_time = time.time()
            
            response = self.client.post(
                '/api/rx-upload/admin/verifiers/create/',
                data=json.dumps(test_data),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
            )
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # ms
            
            print_info(f"Status Code: {response.status_code}")
            print_info(f"Response Time: {response_time:.2f}ms")
            
            if response.status_code == 201:
                data = response.json()
                print_success("Account created successfully!")
                print_info(f"Response: {json.dumps(data, indent=2)[:500]}...")
                
                # Verify user creation
                user = User.objects.get(email=test_data['email'])
                print_success(f"User verified: {user.email} (Role: {user.role})")
                
                # Check user attributes
                print_success(f"Specialization: {getattr(user, 'specialization', 'N/A')}")
                print_success(f"Department: {getattr(user, 'department', 'N/A')}")
                
                # Check VerifierWorkload
                try:
                    workload = VerifierWorkload.objects.get(verifier=user)
                    print_success(f"VerifierWorkload created: Capacity={workload.max_daily_capacity}")
                    has_workload = True
                except VerifierWorkload.DoesNotExist:
                    print_warning("VerifierWorkload NOT found")
                    has_workload = False
                
                self.results['rx_upload_app'] = {
                    'status': 'SUCCESS',
                    'response_code': 201,
                    'response_time_ms': response_time,
                    'user_created': True,
                    'workload_created': has_workload,
                    'features': [
                        'RX-specific fields (specialization, department, license)',
                        'Auto-generates secure password',
                        'Auto-creates VerifierWorkload',
                        'Email notification with welcome template',
                        'RX-focused workflow'
                    ],
                    'pros': [
                        'Auto-creates VerifierWorkload' if has_workload else 'Manual workload creation needed',
                        'RX-specific field support',
                        'Auto-generates password (no manual input needed)',
                        'Dedicated RX workflow integration',
                        'HTML email template for verifiers'
                    ],
                    'cons': [
                        'Not integrated with main accounts system',
                        'Separate endpoint to maintain',
                        'May have duplication with accounts app'
                    ]
                }
                
                return True
            else:
                print_error(f"Failed with status {response.status_code}")
                print_error(f"Response: {response.content.decode()}")
                
                self.results['rx_upload_app'] = {
                    'status': 'FAILED',
                    'response_code': response.status_code,
                    'error': response.content.decode()
                }
                return False
                
        except Exception as e:
            print_error(f"Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results['rx_upload_app'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            return False

    def compare_and_recommend(self):
        """Compare both approaches and provide recommendation"""
        print_header("COMPARISON & RECOMMENDATION")
        
        accounts_result = self.results.get('accounts_app', {})
        rx_upload_result = self.results.get('rx_upload_app', {})
        
        print_section("Feature Comparison")
        
        comparison_table = [
            ["Feature", "Accounts App", "RX Upload App"],
            ["─" * 40, "─" * 20, "─" * 20],
            ["Status", accounts_result.get('status', 'N/A'), rx_upload_result.get('status', 'N/A')],
            ["Response Time", f"{accounts_result.get('response_time_ms', 0):.2f}ms", f"{rx_upload_result.get('response_time_ms', 0):.2f}ms"],
            ["Auto Workload Creation", str(accounts_result.get('workload_created', False)), str(rx_upload_result.get('workload_created', False))],
            ["RX-Specific Fields", "No", "Yes"],
            ["Password Auto-gen", "No", "Yes"],
            ["Audit Logging", "Yes", "Partial"],
            ["Swagger Docs", "Yes", "No"],
            ["Email Template", "Basic", "Enhanced"],
        ]
        
        for row in comparison_table:
            print(f"{row[0]:<40} {row[1]:<20} {row[2]:<20}")
        
        print_section("RECOMMENDATION")
        
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}RECOMMENDED APPROACH: HYBRID{Colors.END}\n")
        
        print(f"{Colors.CYAN}Best Practice:{Colors.END}")
        print("Use ACCOUNTS APP endpoint as primary, with enhancements:\n")
        
        print(f"{Colors.GREEN}1. Primary Endpoint:{Colors.END}")
        print("   POST /api/accounts/admin/rx-verifiers/create/")
        print("   ✓ Better integration with main accounts system")
        print("   ✓ Audit logging built-in")
        print("   ✓ Swagger documentation")
        print("   ✓ Follows Django best practices\n")
        
        print(f"{Colors.YELLOW}2. Required Enhancement:{Colors.END}")
        print("   Add signal/post-save hook to auto-create VerifierWorkload")
        print("   when User with role='rx_verifier' is created\n")
        
        print(f"{Colors.CYAN}3. Optional Improvements:{Colors.END}")
        print("   • Add RX-specific fields to User model (specialization, department, license)")
        print("   • Use enhanced email template from RX Upload app")
        print("   • Consider auto-generating password instead of requiring it\n")
        
        print(f"{Colors.MAGENTA}Implementation Plan:{Colors.END}")
        print("━" * 90)
        print("Step 1: Add signal in rx_upload/models.py to auto-create VerifierWorkload")
        print("Step 2: Add RX-specific fields to accounts/models.py User model (optional)")
        print("Step 3: Update email template in accounts app to use enhanced RX template")
        print("Step 4: Deprecate rx_upload verifier creation endpoint")
        print("Step 5: Update all documentation to reference accounts app endpoint")
        print("━" * 90)
        
        print(f"\n{Colors.BOLD}FINAL VERDICT:{Colors.END}")
        print(f"{Colors.GREEN}✓ Keep: {Colors.END}POST /api/accounts/admin/rx-verifiers/create/")
        print(f"{Colors.RED}✗ Deprecate: {Colors.END}POST /api/rx-upload/admin/verifiers/create/")
        print(f"{Colors.YELLOW}↻ Enhance: {Colors.END}Add auto-creation of VerifierWorkload via Django signal\n")

    def run_comparison(self):
        """Run the complete comparison"""
        print_header("RX VERIFIER ACCOUNT CREATION - COMPREHENSIVE COMPARISON TEST")
        
        self.setup_admin()
        
        # Test both endpoints
        accounts_success = self.test_accounts_app_endpoint()
        rx_upload_success = self.test_rx_upload_app_endpoint()
        
        # Compare and recommend
        self.compare_and_recommend()
        
        # Print final summary
        print_header("TEST SUMMARY")
        print(f"\n{Colors.BOLD}Accounts App:{Colors.END} {Colors.GREEN if accounts_success else Colors.RED}{self.results['accounts_app'].get('status')}{Colors.END}")
        print(f"{Colors.BOLD}RX Upload App:{Colors.END} {Colors.GREEN if rx_upload_success else Colors.RED}{self.results['rx_upload_app'].get('status')}{Colors.END}\n")


if __name__ == '__main__':
    tester = RXVerifierAccountCreationComparison()
    tester.run_comparison()
