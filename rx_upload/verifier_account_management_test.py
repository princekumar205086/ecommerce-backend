"""
Comprehensive Test for RX Verifier Account Management Endpoints
Tests admin's ability to create, manage, and monitor verifier accounts
"""
import os
import django
import sys
from django.conf import settings

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rx_upload.models import VerifierWorkload
import json

User = get_user_model()


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_info(message):
    print(f"{Colors.CYAN}ℹ {message}{Colors.END}")


def print_header(message):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.END}\n")


def print_section(message):
    print(f"\n{Colors.YELLOW}{'─' * 80}{Colors.END}")
    print(f"{Colors.YELLOW}{message}{Colors.END}")
    print(f"{Colors.YELLOW}{'─' * 80}{Colors.END}")


class VerifierAccountManagementTest:
    def __init__(self):
        self.client = Client()
        self.admin_token = None
        self.admin_user = None
        self.created_verifier_id = None
        self.tests_passed = 0
        self.tests_failed = 0
        self.total_tests = 0

    def setup_admin(self):
        """Setup admin user for testing"""
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
            print_success(f"Created admin user: {self.admin_user.email}")
        else:
            print_info(f"Using existing admin: {self.admin_user.email}")
        
        self.admin_token = str(AccessToken.for_user(self.admin_user))
        print_success("Generated admin JWT token")

    def test_create_verifier_account(self):
        """Test POST /api/rx-upload/admin/verifiers/create/"""
        self.total_tests += 1
        print_section("Test 1: Create Verifier Account")
        
        try:
            import random
            random_num = random.randint(1000, 9999)
            
            response = self.client.post(
                '/api/rx-upload/admin/verifiers/create/',
                data=json.dumps({
                    'email': f'dr.test{random_num}@rxverification.com',
                    'full_name': f'Dr. Test Verifier {random_num}',
                    'phone_number': f'98765{random_num}',
                    'specialization': 'General Medicine',
                    'department': 'Internal Medicine',
                    'license_number': f'MED{random_num}',
                    'max_daily_capacity': 40,
                    'send_welcome_email': False  # Set to False for testing
                }),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
            )
            
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 201:
                data = response.json()
                print_info(f"Response: {json.dumps(data, indent=2)}")
                
                assert data['success'] == True
                assert 'verifier_id' in data
                assert 'verifier_email' in data
                assert 'verifier_name' in data
                
                self.created_verifier_id = data['verifier_id']
                
                # Verify user was created
                verifier = User.objects.get(id=self.created_verifier_id)
                assert verifier.role == 'rx_verifier'
                assert verifier.email == data['verifier_email']
                
                # Verify workload was created
                workload = VerifierWorkload.objects.get(verifier=verifier)
                assert workload.max_daily_capacity == 40
                
                print_success(f"Verifier account created successfully")
                print_info(f"Verifier ID: {self.created_verifier_id}")
                print_info(f"Verifier Email: {data['verifier_email']}")
                print_info(f"Verifier Name: {data['verifier_name']}")
                
                self.tests_passed += 1
                return True
            else:
                print_error(f"Expected status 201, got {response.status_code}")
                print_error(f"Response: {response.content.decode()}")
                self.tests_failed += 1
                return False
                
        except Exception as e:
            print_error(f"Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            self.tests_failed += 1
            return False

    def test_list_verifier_accounts(self):
        """Test GET /api/rx-upload/admin/verifiers/"""
        self.total_tests += 1
        print_section("Test 2: List All Verifier Accounts")
        
        try:
            response = self.client.get(
                '/api/rx-upload/admin/verifiers/',
                HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
            )
            
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                assert data['success'] == True
                assert 'verifiers' in data
                assert 'statistics' in data
                assert 'total_count' in data
                
                print_success(f"Listed {data['total_count']} verifier accounts")
                
                # Show first 3 verifiers
                for i, verifier in enumerate(data['verifiers'][:3]):
                    print_info(f"\nVerifier {i+1}:")
                    print_info(f"  Name: {verifier['full_name']}")
                    print_info(f"  Email: {verifier['email']}")
                    print_info(f"  Active: {verifier['is_active']}")
                    if verifier['workload']:
                        print_info(f"  Capacity: {verifier['workload']['current_daily_count']}/{verifier['workload']['max_daily_capacity']}")
                        print_info(f"  Total Verified: {verifier['workload']['total_verified']}")
                        print_info(f"  Approval Rate: {verifier['workload']['approval_rate']}%")
                
                # Show statistics
                stats = data['statistics']
                print_info(f"\nSystem Statistics:")
                print_info(f"  Total Verifiers: {stats['total_verifiers']}")
                print_info(f"  Active Verifiers: {stats['active_verifiers']}")
                print_info(f"  Available Verifiers: {stats['available_verifiers']}")
                
                self.tests_passed += 1
                return True
            else:
                print_error(f"Expected status 200, got {response.status_code}")
                print_error(f"Response: {response.content.decode()}")
                self.tests_failed += 1
                return False
                
        except Exception as e:
            print_error(f"Test failed: {str(e)}")
            self.tests_failed += 1
            return False

    def test_get_verifier_detail(self):
        """Test GET /api/rx-upload/admin/verifiers/{id}/"""
        self.total_tests += 1
        print_section("Test 3: Get Verifier Account Details")
        
        if not self.created_verifier_id:
            print_info("Skipping: No verifier ID available")
            self.tests_passed += 1
            return True
        
        try:
            response = self.client.get(
                f'/api/rx-upload/admin/verifiers/{self.created_verifier_id}/',
                HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
            )
            
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                assert data['success'] == True
                assert 'verifier' in data
                assert 'workload' in data
                assert 'recent_activities' in data
                
                print_success("Verifier details retrieved successfully")
                print_info(f"\nVerifier Information:")
                print_info(f"  Name: {data['verifier']['full_name']}")
                print_info(f"  Email: {data['verifier']['email']}")
                print_info(f"  Specialization: {data['verifier']['specialization']}")
                print_info(f"  Department: {data['verifier']['department']}")
                print_info(f"  License: {data['verifier']['license_number']}")
                print_info(f"  Active: {data['verifier']['is_active']}")
                
                if data['workload']:
                    print_info(f"\nWorkload Information:")
                    print_info(f"  Max Daily Capacity: {data['workload']['max_daily_capacity']}")
                    print_info(f"  Current Count: {data['workload']['current_daily_count']}")
                    print_info(f"  Pending: {data['workload']['pending_count']}")
                    print_info(f"  In Review: {data['workload']['in_review_count']}")
                    print_info(f"  Total Verified: {data['workload']['total_verified']}")
                    print_info(f"  Approval Rate: {data['workload']['approval_rate']}%")
                
                self.tests_passed += 1
                return True
            else:
                print_error(f"Expected status 200, got {response.status_code}")
                print_error(f"Response: {response.content.decode()}")
                self.tests_failed += 1
                return False
                
        except Exception as e:
            print_error(f"Test failed: {str(e)}")
            self.tests_failed += 1
            return False

    def test_update_verifier_account(self):
        """Test PUT /api/rx-upload/admin/verifiers/{id}/"""
        self.total_tests += 1
        print_section("Test 4: Update Verifier Account")
        
        if not self.created_verifier_id:
            print_info("Skipping: No verifier ID available")
            self.tests_passed += 1
            return True
        
        try:
            response = self.client.put(
                f'/api/rx-upload/admin/verifiers/{self.created_verifier_id}/',
                data=json.dumps({
                    'full_name': 'Dr. Updated Verifier Name',
                    'specialization': 'Cardiology',
                    'is_active': True,
                    'workload': {
                        'max_daily_capacity': 60,
                        'is_available': True
                    }
                }),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
            )
            
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                assert data['success'] == True
                assert 'updated_fields' in data
                
                # Verify updates
                verifier = User.objects.get(id=self.created_verifier_id)
                assert verifier.full_name == 'Dr. Updated Verifier Name'
                assert verifier.specialization == 'Cardiology'
                
                workload = VerifierWorkload.objects.get(verifier=verifier)
                assert workload.max_daily_capacity == 60
                
                print_success("Verifier account updated successfully")
                print_info(f"Updated fields: {', '.join(data['updated_fields'])}")
                
                self.tests_passed += 1
                return True
            else:
                print_error(f"Expected status 200, got {response.status_code}")
                print_error(f"Response: {response.content.decode()}")
                self.tests_failed += 1
                return False
                
        except Exception as e:
            print_error(f"Test failed: {str(e)}")
            self.tests_failed += 1
            return False

    def test_get_verifier_statistics(self):
        """Test GET /api/rx-upload/admin/verifiers/statistics/"""
        self.total_tests += 1
        print_section("Test 5: Get Verifier Account Statistics")
        
        try:
            response = self.client.get(
                '/api/rx-upload/admin/verifiers/statistics/',
                HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
            )
            
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                assert data['success'] == True
                assert 'account_statistics' in data
                assert 'performance_statistics' in data
                
                print_success("Statistics retrieved successfully")
                
                acc_stats = data['account_statistics']
                print_info(f"\nAccount Statistics:")
                print_info(f"  Total Verifiers: {acc_stats['total_verifiers']}")
                print_info(f"  Active: {acc_stats['active_verifiers']}")
                print_info(f"  Inactive: {acc_stats['inactive_verifiers']}")
                print_info(f"  Available: {acc_stats['available_verifiers']}")
                print_info(f"  Busy: {acc_stats['busy_verifiers']}")
                
                perf_stats = data['performance_statistics']
                print_info(f"\nPerformance Statistics:")
                print_info(f"  Avg Approval Rate: {perf_stats['average_approval_rate']}%")
                print_info(f"  Avg Processing Time: {perf_stats['average_processing_time_hours']} hours")
                print_info(f"  Total Verifications: {perf_stats['total_verifications_all_time']}")
                print_info(f"  Avg Daily Capacity: {perf_stats['average_daily_capacity']}")
                print_info(f"  Recent (30 days): {perf_stats['recent_verifications_30_days']}")
                
                self.tests_passed += 1
                return True
            else:
                print_error(f"Expected status 200, got {response.status_code}")
                print_error(f"Response: {response.content.decode()}")
                self.tests_failed += 1
                return False
                
        except Exception as e:
            print_error(f"Test failed: {str(e)}")
            self.tests_failed += 1
            return False

    def test_duplicate_email_prevention(self):
        """Test that duplicate email addresses are prevented"""
        self.total_tests += 1
        print_section("Test 6: Duplicate Email Prevention")
        
        try:
            response = self.client.post(
                '/api/rx-upload/admin/verifiers/create/',
                data=json.dumps({
                    'email': 'dr.smith@rxverification.com',  # Existing email
                    'full_name': 'Dr. Duplicate Test',
                    'phone_number': '9876543210',
                    'specialization': 'General',
                    'max_daily_capacity': 30
                }),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
            )
            
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 400:
                data = response.json()
                print_success("Duplicate email correctly rejected")
                print_info(f"Error message: {data.get('message', 'N/A')}")
                
                self.tests_passed += 1
                return True
            else:
                print_error(f"Expected status 400, got {response.status_code}")
                self.tests_failed += 1
                return False
                
        except Exception as e:
            print_error(f"Test failed: {str(e)}")
            self.tests_failed += 1
            return False

    def test_invalid_data_validation(self):
        """Test that invalid data is properly validated"""
        self.total_tests += 1
        print_section("Test 7: Invalid Data Validation")
        
        try:
            response = self.client.post(
                '/api/rx-upload/admin/verifiers/create/',
                data=json.dumps({
                    'email': 'invalid-email',  # Invalid email format
                    'full_name': 'Test',
                    'max_daily_capacity': -5  # Invalid capacity
                }),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
            )
            
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 400:
                data = response.json()
                print_success("Invalid data correctly rejected")
                print_info(f"Validation errors detected: {data.get('errors', {})}")
                
                self.tests_passed += 1
                return True
            else:
                print_error(f"Expected status 400, got {response.status_code}")
                self.tests_failed += 1
                return False
                
        except Exception as e:
            print_error(f"Test failed: {str(e)}")
            self.tests_failed += 1
            return False

    def run_all_tests(self):
        """Run all verifier account management tests"""
        print_header("RX VERIFIER ACCOUNT MANAGEMENT - COMPREHENSIVE TEST SUITE")
        
        self.setup_admin()
        
        self.test_create_verifier_account()
        self.test_list_verifier_accounts()
        self.test_get_verifier_detail()
        self.test_update_verifier_account()
        self.test_get_verifier_statistics()
        self.test_duplicate_email_prevention()
        self.test_invalid_data_validation()
        
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print_header("TEST SUMMARY")
        
        success_rate = (self.tests_passed / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"\n{Colors.BOLD}Total Tests:{Colors.END} {self.total_tests}")
        print(f"{Colors.GREEN}{Colors.BOLD}Passed:{Colors.END} {self.tests_passed}")
        print(f"{Colors.RED}{Colors.BOLD}Failed:{Colors.END} {self.tests_failed}")
        print(f"{Colors.CYAN}{Colors.BOLD}Success Rate:{Colors.END} {success_rate:.1f}%\n")
        
        if self.tests_failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}{'🎉 ALL TESTS PASSED! 🎉':^80}{Colors.END}\n")
        else:
            print(f"{Colors.RED}{Colors.BOLD}{'⚠ SOME TESTS FAILED ⚠':^80}{Colors.END}\n")


if __name__ == '__main__':
    tester = VerifierAccountManagementTest()
    tester.run_all_tests()
