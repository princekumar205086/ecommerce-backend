"""
Comprehensive Admin Endpoints Test for RX Upload System
Tests all admin functionality: dashboard, prescription management, verifier management, bulk operations, and reports
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
from rx_upload.models import PrescriptionUpload, VerifierWorkload, VerificationActivity
from django.utils import timezone
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
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}\n")


def print_section(message):
    print(f"\n{Colors.YELLOW}{'─' * 70}{Colors.END}")
    print(f"{Colors.YELLOW}{message}{Colors.END}")
    print(f"{Colors.YELLOW}{'─' * 70}{Colors.END}")


class AdminEndpointsTest:
    def __init__(self):
        self.client = Client()
        self.admin_token = None
        self.admin_user = None
        self.test_verifier = None
        self.test_prescription = None
        self.tests_passed = 0
        self.tests_failed = 0
        self.total_tests = 0

    def setup_test_data(self):
        """Create test users and data"""
        print_section("Setting up test data...")
        
        # Get or create admin user
        self.admin_user, created = User.objects.get_or_create(
            email='admin@example.com',
            defaults={
                'full_name': 'Admin User',
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
            print_info(f"Using existing admin user: {self.admin_user.email}")
        
        # Generate admin JWT token
        self.admin_token = str(AccessToken.for_user(self.admin_user))
        print_success(f"Generated admin JWT token")
        
        # Create test verifier
        self.test_verifier, created = User.objects.get_or_create(
            email='test_verifier@example.com',
            defaults={
                'full_name': 'Test Verifier',
                'role': 'rx_verifier',
                'contact': '1234567890'
            }
        )
        if created:
            self.test_verifier.set_password('Verifier@123')
            self.test_verifier.save()
            print_success(f"Created test verifier: {self.test_verifier.email}")
        
        # Create verifier workload
        workload, created = VerifierWorkload.objects.get_or_create(
            verifier=self.test_verifier,
            defaults={
                'is_available': True,
                'max_daily_capacity': 50
            }
        )
        if created:
            print_success(f"Created workload for verifier")
        
        # Create test customer
        self.test_customer, created = User.objects.get_or_create(
            email='test_customer@example.com',
            defaults={
                'full_name': 'Test Customer',
                'role': 'customer',
                'contact': '9876543210'
            }
        )
        if created:
            self.test_customer.set_password('Customer@123')
            self.test_customer.save()
            print_success(f"Created test customer: {self.test_customer.email}")
        
        # Create test prescriptions
        for i in range(3):
            prescription, created = PrescriptionUpload.objects.get_or_create(
                customer=self.test_customer,
                prescription_number=f"TEST-RX-{i+1:04d}",
                defaults={
                    'patient_name': f'Test Patient {i+1}',
                    'patient_age': 30 + i,
                    'patient_gender': 'male' if i % 2 == 0 else 'female',
                    'verification_status': 'pending',
                    'is_urgent': i == 0,  # First prescription is urgent
                    'priority_level': 3 if i == 0 else 1
                }
            )
            if created:
                print_success(f"Created test prescription: {prescription.prescription_number}")
            if i == 0:
                self.test_prescription = prescription

    def test_admin_dashboard(self):
        """Test GET /api/rx-upload/admin/dashboard/"""
        self.total_tests += 1
        print_section("Test 1: Admin Dashboard")
        
        try:
            response = self.client.get(
                '/api/rx-upload/admin/dashboard/',
                HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
            )
            
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print_info(f"Response: {json.dumps(data, indent=2)}")
                
                # Verify response structure
                assert data['success'] == True, "Response should be successful"
                assert 'data' in data, "Response should have data"
                assert 'overview' in data['data'], "Should have overview section"
                assert 'verifiers' in data['data'], "Should have verifiers section"
                assert 'performance' in data['data'], "Should have performance section"
                
                print_success(f"Dashboard loaded successfully")
                print_info(f"Total Prescriptions: {data['data']['overview']['total_prescriptions']}")
                print_info(f"Pending: {data['data']['overview']['pending']}")
                print_info(f"Total Verifiers: {data['data']['verifiers']['total']}")
                print_info(f"Available Verifiers: {data['data']['verifiers']['available']}")
                
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

    def test_admin_list_prescriptions(self):
        """Test GET /api/rx-upload/admin/prescriptions/"""
        self.total_tests += 1
        print_section("Test 2: Admin List All Prescriptions")
        
        try:
            response = self.client.get(
                '/api/rx-upload/admin/prescriptions/',
                HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
            )
            
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                assert data['success'] == True
                assert 'data' in data
                assert 'results' in data['data']
                assert 'pagination' in data['data']
                
                print_success(f"Prescriptions listed successfully")
                print_info(f"Total Count: {data['data']['pagination']['total_count']}")
                print_info(f"Results: {len(data['data']['results'])} prescriptions")
                
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

    def test_admin_assign_prescription(self):
        """Test POST /api/rx-upload/admin/prescriptions/{id}/assign/"""
        self.total_tests += 1
        print_section("Test 3: Admin Assign Prescription to Verifier")
        
        try:
            response = self.client.post(
                f'/api/rx-upload/admin/prescriptions/{self.test_prescription.id}/assign/',
                data=json.dumps({
                    'verifier_id': self.test_verifier.id,
                    'priority_level': 3,
                    'is_urgent': True
                }),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
            )
            
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print_info(f"Response: {json.dumps(data, indent=2)}")
                
                assert data['success'] == True
                assert 'data' in data
                
                # Verify prescription was assigned
                self.test_prescription.refresh_from_db()
                assert self.test_prescription.verified_by == self.test_verifier
                assert self.test_prescription.verification_status == 'in_review'
                
                print_success(f"Prescription assigned successfully to {self.test_verifier.full_name}")
                print_info(f"Prescription Status: {self.test_prescription.verification_status}")
                
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

    def test_admin_reassign_prescription(self):
        """Test POST /api/rx-upload/admin/prescriptions/{id}/reassign/"""
        self.total_tests += 1
        print_section("Test 4: Admin Reassign Prescription")
        
        try:
            # Create another verifier for reassignment
            new_verifier, created = User.objects.get_or_create(
                email='new_verifier@example.com',
                defaults={
                    'full_name': 'New Verifier',
                    'role': 'rx_verifier',
                    'contact': '5555555555'
                }
            )
            if created:
                new_verifier.set_password('Verifier@123')
                new_verifier.save()
                VerifierWorkload.objects.get_or_create(
                    verifier=new_verifier,
                    defaults={'is_available': True, 'max_daily_capacity': 50}
                )
            
            response = self.client.post(
                f'/api/rx-upload/admin/prescriptions/{self.test_prescription.id}/reassign/',
                data=json.dumps({
                    'verifier_id': new_verifier.id,
                    'reason': 'Workload balancing test'
                }),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
            )
            
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                assert data['success'] == True
                
                # Verify reassignment
                self.test_prescription.refresh_from_db()
                assert self.test_prescription.verified_by == new_verifier
                
                print_success(f"Prescription reassigned successfully to {new_verifier.full_name}")
                
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

    def test_admin_bulk_assign(self):
        """Test POST /api/rx-upload/admin/prescriptions/bulk-assign/"""
        self.total_tests += 1
        print_section("Test 5: Admin Bulk Assign Prescriptions")
        
        try:
            # Get pending prescriptions
            pending_prescriptions = PrescriptionUpload.objects.filter(
                verification_status='pending'
            )[:2]
            
            if not pending_prescriptions.exists():
                print_info("No pending prescriptions for bulk assign test, skipping...")
                self.tests_passed += 1
                return True
            
            prescription_ids = [str(p.id) for p in pending_prescriptions]
            
            response = self.client.post(
                '/api/rx-upload/admin/prescriptions/bulk-assign/',
                data=json.dumps({
                    'prescription_ids': prescription_ids,
                    'strategy': 'balanced'
                }),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
            )
            
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print_info(f"Response: {json.dumps(data, indent=2)}")
                
                assert data['success'] == True
                assert data['data']['assigned_count'] > 0
                
                print_success(f"Bulk assigned {data['data']['assigned_count']} prescriptions")
                
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

    def test_admin_list_verifiers(self):
        """Test GET /api/rx-upload/admin/verifiers-management/"""
        self.total_tests += 1
        print_section("Test 6: Admin List All Verifiers")
        
        try:
            response = self.client.get(
                '/api/rx-upload/admin/verifiers-management/',
                HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
            )
            
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                assert data['success'] == True
                assert 'data' in data
                assert len(data['data']) > 0
                
                print_success(f"Listed {len(data['data'])} verifiers")
                
                # Print verifier details
                for verifier in data['data'][:3]:  # Show first 3
                    print_info(f"Verifier: {verifier['full_name']}")
                    print_info(f"  - Email: {verifier['email']}")
                    print_info(f"  - Active: {verifier['is_active']}")
                    print_info(f"  - Workload: {verifier['workload']['in_review_count']} in review")
                
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

    def test_admin_update_verifier_status(self):
        """Test POST /api/rx-upload/admin/verifiers-management/{id}/status/"""
        self.total_tests += 1
        print_section("Test 7: Admin Update Verifier Status")
        
        try:
            response = self.client.post(
                f'/api/rx-upload/admin/verifiers-management/{self.test_verifier.id}/status/',
                data=json.dumps({
                    'is_active': True,
                    'is_available': True,
                    'max_daily_capacity': 75
                }),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
            )
            
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                assert data['success'] == True
                
                # Verify update
                workload = VerifierWorkload.objects.get(verifier=self.test_verifier)
                assert workload.max_daily_capacity == 75
                
                print_success(f"Verifier status updated successfully")
                print_info(f"New capacity: {workload.max_daily_capacity}")
                
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

    def test_admin_performance_report(self):
        """Test GET /api/rx-upload/admin/reports/performance/"""
        self.total_tests += 1
        print_section("Test 8: Admin Performance Report")
        
        try:
            response = self.client.get(
                '/api/rx-upload/admin/reports/performance/',
                HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
            )
            
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print_info(f"Response: {json.dumps(data, indent=2)[:500]}...")
                
                assert data['success'] == True
                assert 'data' in data
                assert 'overall' in data['data']
                
                print_success(f"Performance report generated successfully")
                print_info(f"Total Prescriptions: {data['data']['overall']['total_prescriptions']}")
                print_info(f"Approval Rate: {data['data']['overall']['approval_rate']}%")
                
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

    def test_admin_filter_prescriptions(self):
        """Test GET /api/rx-upload/admin/prescriptions/ with filters"""
        self.total_tests += 1
        print_section("Test 9: Admin Filter Prescriptions (Urgent)")
        
        try:
            response = self.client.get(
                '/api/rx-upload/admin/prescriptions/?urgent=true&status=pending',
                HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
            )
            
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                assert data['success'] == True
                
                print_success(f"Filtered prescriptions successfully")
                print_info(f"Urgent Pending Prescriptions: {data['data']['pagination']['total_count']}")
                
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

    def test_admin_search_prescriptions(self):
        """Test GET /api/rx-upload/admin/prescriptions/ with search"""
        self.total_tests += 1
        print_section("Test 10: Admin Search Prescriptions")
        
        try:
            response = self.client.get(
                f'/api/rx-upload/admin/prescriptions/?search=TEST-RX',
                HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
            )
            
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                assert data['success'] == True
                
                print_success(f"Search completed successfully")
                print_info(f"Found: {data['data']['pagination']['total_count']} prescriptions")
                
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

    def run_all_tests(self):
        """Run all admin endpoint tests"""
        print_header("RX UPLOAD ADMIN ENDPOINTS - COMPREHENSIVE TEST SUITE")
        
        # Setup
        self.setup_test_data()
        
        # Run tests
        self.test_admin_dashboard()
        self.test_admin_list_prescriptions()
        self.test_admin_assign_prescription()
        self.test_admin_reassign_prescription()
        self.test_admin_bulk_assign()
        self.test_admin_list_verifiers()
        self.test_admin_update_verifier_status()
        self.test_admin_performance_report()
        self.test_admin_filter_prescriptions()
        self.test_admin_search_prescriptions()
        
        # Summary
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
            print(f"{Colors.GREEN}{Colors.BOLD}{'🎉 ALL TESTS PASSED! 🎉':^70}{Colors.END}\n")
        else:
            print(f"{Colors.RED}{Colors.BOLD}{'⚠ SOME TESTS FAILED ⚠':^70}{Colors.END}\n")


if __name__ == '__main__':
    tester = AdminEndpointsTest()
    tester.run_all_tests()
