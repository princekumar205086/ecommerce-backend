#!/usr/bin/env python
"""
Comprehensive RX Upload API Test Script
Tests all customer and verifier endpoints with detailed reporting
"""
import os
import sys
import django
import requests
import json
from io import BytesIO
from PIL import Image
from decimal import Decimal
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from rx_upload.models import PrescriptionUpload, VerifierWorkload

User = get_user_model()


class RXUploadAPITester:
    """Comprehensive test suite for RX Upload API"""
    
    def __init__(self):
        self.client = Client()
        self.base_url = 'http://localhost:8000'
        self.test_results = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        self.customer_user = None
        self.verifier_user = None
        self.test_prescription_id = None
        self.test_address_id = None
        
    def print_header(self, text):
        """Print section header"""
        print(f"\n{Fore.CYAN}{'=' * 80}")
        print(f"{Fore.CYAN}{text.center(80)}")
        print(f"{Fore.CYAN}{'=' * 80}\n")
    
    def print_test(self, name):
        """Print test name"""
        print(f"{Fore.YELLOW}▶ Testing: {name}")
        self.test_results['total'] += 1
    
    def print_success(self, message):
        """Print success message"""
        print(f"{Fore.GREEN}  ✓ {message}")
        self.test_results['passed'] += 1
    
    def print_error(self, message, details=None):
        """Print error message"""
        print(f"{Fore.RED}  ✗ {message}")
        if details:
            print(f"{Fore.RED}    Details: {details}")
        self.test_results['failed'] += 1
        self.test_results['errors'].append({
            'message': message,
            'details': details
        })
    
    def print_info(self, message):
        """Print info message"""
        print(f"{Fore.BLUE}  ℹ {message}")
    
    def create_test_image(self):
        """Create a test prescription image"""
        img = Image.new('RGB', (800, 600), color='white')
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        return img_byte_arr
    
    def setup_test_data(self):
        """Setup test users and data"""
        self.print_header("SETTING UP TEST DATA")
        
        # Create or get customer user
        try:
            self.customer_user, created = User.objects.get_or_create(
                email='testcustomer@medixmall.com',
                defaults={
                    'full_name': 'Test Customer',
                    'contact': '9876543210',
                    'role': 'customer',
                    'is_active': True
                }
            )
            if created:
                self.customer_user.set_password('TestPass123')
                self.customer_user.save()
                self.print_success(f"Created customer user: {self.customer_user.email}")
            else:
                self.print_info(f"Using existing customer: {self.customer_user.email}")
        except Exception as e:
            self.print_error("Failed to create customer user", str(e))
            return False
        
        # Set test address ID (addresses are managed via API, not database model)
        self.test_address_id = 1  # Default address ID from get_user_addresses helper
        self.print_info(f"Using address ID: {self.test_address_id}")
        
        # Create or get verifier user
        try:
            self.verifier_user, created = User.objects.get_or_create(
                email='testverifier@medixmall.com',
                defaults={
                    'full_name': 'Test Verifier',
                    'contact': '9876543211',
                    'role': 'rx_verifier',
                    'is_active': True
                }
            )
            if created:
                self.verifier_user.set_password('VerifierPass123')
                self.verifier_user.save()
                
                # Create workload for verifier
                VerifierWorkload.objects.get_or_create(
                    verifier=self.verifier_user,
                    defaults={'is_available': True, 'max_daily_capacity': 50}
                )
                self.print_success(f"Created verifier user: {self.verifier_user.email}")
            else:
                self.print_info(f"Using existing verifier: {self.verifier_user.email}")
        except Exception as e:
            self.print_error("Failed to create verifier user", str(e))
            return False
        
        return True
    
    def login_as_customer(self):
        """Login as customer using force_login"""
        self.client.force_login(self.customer_user)
    
    def login_as_verifier(self):
        """Login as verifier using force_login"""
        self.client.force_login(self.verifier_user)
    
    def logout(self):
        """Logout current user"""
        self.client.logout()
    
    # ==================== CUSTOMER FLOW TESTS ====================
    
    def test_upload_prescription(self):
        """Test prescription file upload"""
        self.print_test("Upload Prescription - Valid File")
        self.login_as_customer()
        
        try:
            # Create test image
            test_image = self.create_test_image()
            
            # Upload prescription
            response = self.client.post(
                '/api/rx-upload/customer/upload/',
                {
                    'prescription_file': test_image
                },
                format='multipart'
            )
            
            if response.status_code == 201:
                data = response.json()
                if data.get('success') and 'prescription_id' in data.get('data', {}):
                    self.test_prescription_id = data['data']['prescription_id']
                    self.print_success(f"Upload successful - ID: {self.test_prescription_id}")
                    self.print_info(f"Prescription Number: {data['data']['prescription_number']}")
                    return True
                else:
                    self.print_error("Response missing expected data", data)
            else:
                self.print_error(f"Upload failed with status {response.status_code}", response.content.decode())
        except Exception as e:
            self.print_error("Exception during upload", str(e))
        
        return False
    
    def test_upload_without_file(self):
        """Test upload without file - should fail"""
        self.print_test("Upload Prescription - Missing File (Should Fail)")
        self.login_as_customer()
        
        try:
            response = self.client.post('/api/rx-upload/customer/upload/', {})
            
            if response.status_code == 400:
                data = response.json()
                if not data.get('success'):
                    self.print_success("Correctly rejected upload without file")
                    return True
                else:
                    self.print_error("Should have failed but returned success")
            else:
                self.print_error(f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.print_error("Exception during test", str(e))
        
        return False
    
    def test_add_patient_info(self):
        """Test adding patient information"""
        self.print_test("Add Patient Information - Valid Data")
        self.login_as_customer()
        
        if not self.test_prescription_id:
            self.print_error("No prescription ID available", "Run upload test first")
            return False
        
        try:
            patient_data = {
                'patient_name': 'John Doe',
                'customer_phone': '9876543210',
                'patient_age': 30,
                'patient_gender': 'male',
                'emergency_contact': '9123456789',
                'customer_notes': 'Test patient notes'
            }
            
            response = self.client.post(
                f'/api/rx-upload/customer/{self.test_prescription_id}/patient-info/',
                data=json.dumps(patient_data),
                content_type='application/json'
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.print_success("Patient information saved successfully")
                    self.print_info(f"Patient: {data['data']['patient_name']}")
                    return True
                else:
                    self.print_error("Response indicates failure", data)
            else:
                self.print_error(f"Failed with status {response.status_code}", response.content.decode())
        except Exception as e:
            self.print_error("Exception during test", str(e))
        
        return False
    
    def test_patient_info_validation(self):
        """Test patient info validation - missing required fields"""
        self.print_test("Add Patient Information - Missing Phone (Should Fail)")
        self.login_as_customer()
        
        if not self.test_prescription_id:
            self.print_error("No prescription ID available", "Run upload test first")
            return False
        
        try:
            patient_data = {
                'patient_name': 'John Doe'
                # Missing customer_phone
            }
            
            response = self.client.post(
                f'/api/rx-upload/customer/{self.test_prescription_id}/patient-info/',
                data=json.dumps(patient_data),
                content_type='application/json'
            )
            
            if response.status_code == 400:
                data = response.json()
                if not data.get('success'):
                    self.print_success("Correctly rejected invalid patient info")
                    return True
                else:
                    self.print_error("Should have failed but returned success")
            else:
                self.print_error(f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.print_error("Exception during test", str(e))
        
        return False
    
    def test_get_delivery_addresses(self):
        """Test getting delivery addresses"""
        self.print_test("Get Delivery Addresses")
        self.login_as_customer()
        
        try:
            response = self.client.get('/api/rx-upload/customer/addresses/')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    addresses = data.get('data', [])
                    self.print_success(f"Retrieved {len(addresses)} address(es)")
                    if addresses:
                        self.print_info(f"First address: {addresses[0]['formatted_address']}")
                    return True
                else:
                    self.print_error("Response indicates failure", data)
            else:
                self.print_error(f"Failed with status {response.status_code}", response.content.decode())
        except Exception as e:
            self.print_error("Exception during test", str(e))
        
        return False
    
    def test_get_delivery_options(self):
        """Test getting delivery options"""
        self.print_test("Get Delivery Options")
        self.login_as_customer()
        
        try:
            response = self.client.get('/api/rx-upload/customer/delivery-options/')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    options = data.get('data', {}).get('options', [])
                    self.print_success(f"Retrieved {len(options)} delivery option(s)")
                    for opt in options:
                        self.print_info(f"  - {opt['name']}: ₹{opt['price']} ({opt['estimated_delivery']})")
                    return True
                else:
                    self.print_error("Response indicates failure", data)
            else:
                self.print_error(f"Failed with status {response.status_code}", response.content.decode())
        except Exception as e:
            self.print_error("Exception during test", str(e))
        
        return False
    
    def test_submit_order(self):
        """Test submitting complete prescription order"""
        self.print_test("Submit Prescription Order - Complete Data")
        self.login_as_customer()
        
        if not self.test_prescription_id:
            self.print_error("No prescription ID available", "Run upload test first")
            return False
        
        if not self.test_address_id:
            self.print_error("No address ID available", "Run setup first")
            return False
        
        try:
            order_data = {
                'delivery_address_id': self.test_address_id,
                'delivery_option': 'express',
                'payment_method': 'cod',
                'customer_notes': 'Test order submission'
            }
            
            response = self.client.post(
                f'/api/rx-upload/customer/{self.test_prescription_id}/submit/',
                data=json.dumps(order_data),
                content_type='application/json'
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.print_success("Order submitted successfully")
                    self.print_info(f"Order ID: {data['data']['order_id']}")
                    self.print_info(f"Delivery Charge: ₹{data['data']['delivery_charge']}")
                    self.print_info(f"Status: {data['data']['status']}")
                    return True
                else:
                    self.print_error("Response indicates failure", data)
            else:
                self.print_error(f"Failed with status {response.status_code}", response.content.decode())
        except Exception as e:
            self.print_error("Exception during test", str(e))
        
        return False
    
    def test_submit_order_validation(self):
        """Test order submission validation - missing delivery address"""
        self.print_test("Submit Order - Missing Address (Should Fail)")
        self.login_as_customer()
        
        if not self.test_prescription_id:
            self.print_error("No prescription ID available", "Run upload test first")
            return False
        
        try:
            order_data = {
                'delivery_option': 'express',
                # Missing delivery_address_id
            }
            
            response = self.client.post(
                f'/api/rx-upload/customer/{self.test_prescription_id}/submit/',
                data=json.dumps(order_data),
                content_type='application/json'
            )
            
            if response.status_code == 400:
                data = response.json()
                if not data.get('success'):
                    self.print_success("Correctly rejected incomplete order")
                    return True
                else:
                    self.print_error("Should have failed but returned success")
            else:
                self.print_error(f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.print_error("Exception during test", str(e))
        
        return False
    
    def test_get_order_summary(self):
        """Test getting order summary"""
        self.print_test("Get Order Summary")
        self.login_as_customer()
        
        if not self.test_prescription_id:
            self.print_error("No prescription ID available", "Run upload test first")
            return False
        
        try:
            response = self.client.get(
                f'/api/rx-upload/customer/{self.test_prescription_id}/summary/'
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    summary = data.get('data', {})
                    self.print_success("Retrieved order summary")
                    self.print_info(f"Prescription Files: {summary.get('prescription_files')}")
                    self.print_info(f"Patient: {summary.get('patient')}")
                    self.print_info(f"Status: {summary.get('verification_status')}")
                    return True
                else:
                    self.print_error("Response indicates failure", data)
            else:
                self.print_error(f"Failed with status {response.status_code}", response.content.decode())
        except Exception as e:
            self.print_error("Exception during test", str(e))
        
        return False
    
    def test_get_my_prescriptions(self):
        """Test getting customer's prescription history"""
        self.print_test("Get My Prescriptions")
        self.login_as_customer()
        
        try:
            response = self.client.get('/api/rx-upload/customer/my-prescriptions/')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    prescriptions = data.get('data', [])
                    count = data.get('count', 0)
                    self.print_success(f"Retrieved {count} prescription(s)")
                    for rx in prescriptions[:3]:  # Show first 3
                        self.print_info(f"  - {rx['prescription_number']}: {rx['verification_status']}")
                    return True
                else:
                    self.print_error("Response indicates failure", data)
            else:
                self.print_error(f"Failed with status {response.status_code}", response.content.decode())
        except Exception as e:
            self.print_error("Exception during test", str(e))
        
        return False
    
    # ==================== VERIFIER FLOW TESTS ====================
    
    def test_verifier_login(self):
        """Test verifier login"""
        self.print_test("Verifier Login")
        self.logout()
        
        try:
            response = self.client.post(
                '/api/rx-upload/auth/login/',
                data=json.dumps({
                    'email': 'testverifier@medixmall.com',
                    'password': 'VerifierPass123'
                }),
                content_type='application/json'
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.print_success("Verifier login successful")
                    self.print_info(f"User: {data['data']['user']['full_name']}")
                    return True
                else:
                    self.print_error("Response indicates failure", data)
            else:
                self.print_error(f"Failed with status {response.status_code}", response.content.decode())
        except Exception as e:
            self.print_error("Exception during test", str(e))
        
        return False
    
    def test_list_prescriptions(self):
        """Test listing prescriptions"""
        self.print_test("List Prescriptions")
        self.login_as_verifier()
        
        try:
            response = self.client.get('/api/rx-upload/prescriptions/')
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                count = data.get('count', 0)
                self.print_success(f"Retrieved {len(results)} prescriptions (Total: {count})")
                return True
            else:
                self.print_error(f"Failed with status {response.status_code}", response.content.decode())
        except Exception as e:
            self.print_error("Exception during test", str(e))
        
        return False
    
    def test_assign_prescription(self):
        """Test assigning prescription to verifier"""
        self.print_test("Assign Prescription to Verifier")
        self.login_as_verifier()
        
        if not self.test_prescription_id:
            self.print_error("No prescription ID available", "Run upload test first")
            return False
        
        try:
            response = self.client.post(
                f'/api/rx-upload/prescriptions/{self.test_prescription_id}/assign/'
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.print_success("Prescription assigned successfully")
                    return True
                else:
                    self.print_error("Response indicates failure", data)
            else:
                self.print_error(f"Failed with status {response.status_code}", response.content.decode())
        except Exception as e:
            self.print_error("Exception during test", str(e))
        
        return False
    
    def test_approve_prescription(self):
        """Test approving prescription"""
        self.print_test("Approve Prescription")
        self.login_as_verifier()
        
        if not self.test_prescription_id:
            self.print_error("No prescription ID available", "Run upload test first")
            return False
        
        try:
            response = self.client.post(
                f'/api/rx-upload/prescriptions/{self.test_prescription_id}/approve/',
                data=json.dumps({
                    'notes': 'Test approval - All medications verified'
                }),
                content_type='application/json'
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.print_success("Prescription approved successfully")
                    return True
                else:
                    self.print_error("Response indicates failure", data)
            else:
                self.print_error(f"Failed with status {response.status_code}", response.content.decode())
        except Exception as e:
            self.print_error("Exception during test", str(e))
        
        return False
    
    def test_verification_dashboard(self):
        """Test verification dashboard"""
        self.print_test("Verification Dashboard")
        self.login_as_verifier()
        
        try:
            response = self.client.get('/api/rx-upload/dashboard/')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    counts = data['data'].get('counts', {})
                    self.print_success("Dashboard loaded successfully")
                    self.print_info(f"Pending: {counts.get('pending', 0)}")
                    self.print_info(f"In Review: {counts.get('in_review', 0)}")
                    self.print_info(f"Approved: {counts.get('approved', 0)}")
                    return True
                else:
                    self.print_error("Response indicates failure", data)
            else:
                self.print_error(f"Failed with status {response.status_code}", response.content.decode())
        except Exception as e:
            self.print_error("Exception during test", str(e))
        
        return False
    
    # ==================== MAIN TEST RUNNER ====================
    
    def run_all_tests(self):
        """Run all test suites"""
        print(f"\n{Fore.MAGENTA}{'*' * 80}")
        print(f"{Fore.MAGENTA}{'RX UPLOAD API COMPREHENSIVE TEST SUITE'.center(80)}")
        print(f"{Fore.MAGENTA}{'*' * 80}\n")
        
        # Setup
        if not self.setup_test_data():
            self.print_error("Failed to setup test data. Aborting tests.")
            return
        
        # Customer Flow Tests
        self.print_header("CUSTOMER FLOW TESTS")
        self.test_upload_prescription()
        self.test_upload_without_file()
        self.test_add_patient_info()
        self.test_patient_info_validation()
        self.test_get_delivery_addresses()
        self.test_get_delivery_options()
        self.test_submit_order()
        self.test_submit_order_validation()
        self.test_get_order_summary()
        self.test_get_my_prescriptions()
        
        # Verifier Flow Tests
        self.print_header("VERIFIER FLOW TESTS")
        self.test_verifier_login()
        self.test_list_prescriptions()
        self.test_assign_prescription()
        self.test_approve_prescription()
        self.test_verification_dashboard()
        
        # Print Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")
        
        total = self.test_results['total']
        passed = self.test_results['passed']
        failed = self.test_results['failed']
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"{Fore.CYAN}Total Tests: {total}")
        print(f"{Fore.GREEN}Passed: {passed}")
        print(f"{Fore.RED}Failed: {failed}")
        print(f"{Fore.YELLOW}Success Rate: {success_rate:.1f}%\n")
        
        if success_rate == 100:
            print(f"{Fore.GREEN}{'🎉 ALL TESTS PASSED! 🎉'.center(80)}\n")
        elif success_rate >= 80:
            print(f"{Fore.YELLOW}{'⚠ MOST TESTS PASSED - Some issues need attention'.center(80)}\n")
        else:
            print(f"{Fore.RED}{'❌ MANY TESTS FAILED - Significant issues detected'.center(80)}\n")
        
        if self.test_results['errors']:
            print(f"{Fore.RED}Failed Tests Details:")
            for i, error in enumerate(self.test_results['errors'], 1):
                print(f"{Fore.RED}  {i}. {error['message']}")
                if error['details']:
                    print(f"{Fore.RED}     {error['details']}")


if __name__ == '__main__':
    tester = RXUploadAPITester()
    tester.run_all_tests()
