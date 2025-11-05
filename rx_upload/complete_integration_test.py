#!/usr/bin/env python
"""
Complete Integration Test for RX Upload System
Tests all customer endpoints with proper Django authentication
Run server first: python manage.py runserver
"""
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from colorama import init, Fore, Style
from PIL import Image
from io import BytesIO
import json

# Initialize colorama
init(autoreset=True)

User = get_user_model()

class IntegrationTester:
    def __init__(self):
        self.client = Client()
        self.test_results = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        self.prescription_id = None
        self.customer = None
        
    def print_header(self, text):
        print(f"\n{Fore.CYAN}{'=' * 80}")
        print(f"{Fore.CYAN}{text.center(80)}")
        print(f"{Fore.CYAN}{'=' * 80}\n")
    
    def print_test(self, name):
        print(f"{Fore.YELLOW}▶ Testing: {name}")
        self.test_results['total'] += 1
    
    def print_success(self, message):
        print(f"{Fore.GREEN}  ✓ {message}")
        self.test_results['passed'] += 1
    
    def print_error(self, message, details=None):
        print(f"{Fore.RED}  ✗ {message}")
        if details:
            print(f"{Fore.RED}    Details: {details}")
        self.test_results['failed'] += 1
        self.test_results['errors'].append({
            'message': message,
            'details': details
        })
    
    def print_info(self, message):
        print(f"{Fore.BLUE}  ℹ {message}")
    
    def create_test_image(self):
        """Create a test prescription image"""
        img = Image.new('RGB', (800, 600), color='white')
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        img_byte_arr.name = 'test_prescription.jpg'
        return img_byte_arr
    
    def setup_test_user(self):
        """Create or get test customer"""
        self.print_test("Setup Test User")
        
        try:
            # Get or create test customer
            self.customer, created = User.objects.get_or_create(
                email='testcustomer@example.com',
                defaults={
                    'full_name': 'Test Customer',
                    'contact': '9876543210',
                    'role': 'user',
                    'is_active': True,
                    'email_verified': True
                }
            )
            
            if created:
                self.customer.set_password('TestPass123!')
                self.customer.save()
                self.print_success("Created new test customer")
            else:
                self.print_success("Using existing test customer")
            
            # Login the client
            self.client.force_login(self.customer)
            self.print_info(f"Authenticated as: {self.customer.email}")
            return True
            
        except Exception as e:
            self.print_error(f"Failed to setup user: {str(e)}")
            return False
    
    def test_upload_prescription(self):
        """Test prescription upload"""
        self.print_test("Upload Prescription")
        
        try:
            # Create test image file
            image_content = self.create_test_image().read()
            uploaded_file = SimpleUploadedFile(
                "test_prescription.jpg",
                image_content,
                content_type="image/jpeg"
            )
            
            response = self.client.post(
                '/api/rx-upload/customer/upload/',
                {'prescription_file': uploaded_file},
                format='multipart'
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                if data.get('success'):
                    self.prescription_id = data['data']['prescription_id']
                    self.print_success(f"Uploaded successfully")
                    self.print_info(f"Prescription ID: {self.prescription_id}")
                    self.print_info(f"Prescription #: {data['data']['prescription_number']}")
                    return True
                else:
                    self.print_error("Upload failed", json.dumps(data, indent=2))
            else:
                self.print_error(f"Status {response.status_code}", response.content.decode()[:200])
        except Exception as e:
            self.print_error(f"Exception: {str(e)}")
        
        return False
    
    def test_add_patient_info(self):
        """Test adding patient information"""
        self.print_test("Add Patient Information")
        
        if not self.prescription_id:
            self.print_error("No prescription ID available")
            return False
        
        try:
            patient_data = {
                'patient_name': 'John Doe Integration Test',
                'customer_phone': '9876543210',
                'patient_age': 30,
                'patient_gender': 'male',
                'emergency_contact': '9123456789',
                'customer_notes': 'Integration test patient'
            }
            
            response = self.client.post(
                f'/api/rx-upload/customer/{self.prescription_id}/patient-info/',
                data=json.dumps(patient_data),
                content_type='application/json'
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.print_success("Patient info saved")
                    self.print_info(f"Patient: {data['data']['patient_name']}")
                    return True
                else:
                    self.print_error("Save failed", json.dumps(data, indent=2))
            else:
                self.print_error(f"Status {response.status_code}", response.content.decode()[:200])
        except Exception as e:
            self.print_error(f"Exception: {str(e)}")
        
        return False
    
    def test_get_addresses(self):
        """Test getting delivery addresses"""
        self.print_test("Get Delivery Addresses")
        
        try:
            response = self.client.get('/api/rx-upload/customer/addresses/')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    addresses = data.get('data', [])
                    self.print_success(f"Retrieved {len(addresses)} address(es)")
                    return True
                else:
                    self.print_error("Request failed", json.dumps(data, indent=2))
            else:
                self.print_error(f"Status {response.status_code}", response.content.decode()[:200])
        except Exception as e:
            self.print_error(f"Exception: {str(e)}")
        
        return False
    
    def test_get_delivery_options(self):
        """Test getting delivery options"""
        self.print_test("Get Delivery Options")
        
        try:
            response = self.client.get('/api/rx-upload/customer/delivery-options/')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    options = data['data']['options']
                    self.print_success(f"Retrieved {len(options)} delivery option(s)")
                    for opt in options:
                        self.print_info(f"  - {opt['name']}: ₹{opt['price']}")
                    return True
                else:
                    self.print_error("Request failed", json.dumps(data, indent=2))
            else:
                self.print_error(f"Status {response.status_code}", response.content.decode()[:200])
        except Exception as e:
            self.print_error(f"Exception: {str(e)}")
        
        return False
    
    def test_submit_order(self):
        """Test submitting prescription order"""
        self.print_test("Submit Prescription Order")
        
        if not self.prescription_id:
            self.print_error("No prescription ID available")
            return False
        
        try:
            order_data = {
                'delivery_address_id': 1,
                'delivery_option': 'express',
                'payment_method': 'cod',
                'customer_notes': 'Integration test order - please deliver ASAP'
            }
            
            response = self.client.post(
                f'/api/rx-upload/customer/{self.prescription_id}/submit/',
                data=json.dumps(order_data),
                content_type='application/json'
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.print_success("Order submitted successfully")
                    self.print_info(f"Order ID: {data['data']['order_id']}")
                    self.print_info(f"Status: {data['data']['status']}")
                    self.print_info(f"Delivery: ₹{data['data']['delivery_charge']} - {data['data']['estimated_delivery']}")
                    return True
                else:
                    self.print_error("Submit failed", json.dumps(data, indent=2))
            else:
                self.print_error(f"Status {response.status_code}", response.content.decode()[:200])
        except Exception as e:
            self.print_error(f"Exception: {str(e)}")
        
        return False
    
    def test_get_summary(self):
        """Test getting order summary"""
        self.print_test("Get Order Summary")
        
        if not self.prescription_id:
            self.print_error("No prescription ID available")
            return False
        
        try:
            response = self.client.get(
                f'/api/rx-upload/customer/{self.prescription_id}/summary/'
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    summary = data['data']
                    self.print_success("Retrieved order summary")
                    self.print_info(f"Prescription #: {summary['prescription_number']}")
                    self.print_info(f"Patient: {summary['patient']}")
                    self.print_info(f"Status: {summary['verification_status']}")
                    return True
                else:
                    self.print_error("Request failed", json.dumps(data, indent=2))
            else:
                self.print_error(f"Status {response.status_code}", response.content.decode()[:200])
        except Exception as e:
            self.print_error(f"Exception: {str(e)}")
        
        return False
    
    def test_get_my_prescriptions(self):
        """Test getting customer's prescriptions"""
        self.print_test("Get My Prescriptions")
        
        try:
            response = self.client.get('/api/rx-upload/customer/my-prescriptions/')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    prescriptions = data.get('data', [])
                    count = data.get('count', 0)
                    self.print_success(f"Retrieved {count} prescription(s)")
                    for rx in prescriptions[:3]:  # Show first 3
                        self.print_info(f"  - {rx['prescription_number']}: {rx['verification_status_display']}")
                    return True
                else:
                    self.print_error("Request failed", json.dumps(data, indent=2))
            else:
                self.print_error(f"Status {response.status_code}", response.content.decode()[:200])
        except Exception as e:
            self.print_error(f"Exception: {str(e)}")
        
        return False
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")
        
        total = self.test_results['total']
        passed = self.test_results['passed']
        failed = self.test_results['failed']
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"{Fore.WHITE}Total Tests: {total}")
        print(f"{Fore.GREEN}Passed: {passed}")
        print(f"{Fore.RED}Failed: {failed}")
        print(f"{Fore.CYAN}Success Rate: {success_rate:.1f}%\n")
        
        if success_rate == 100:
            print(f"{Fore.GREEN}{'🎉 ALL TESTS PASSED! 🎉'.center(80)}")
            print(f"{Fore.GREEN}{'✓ RX Upload System Ready for Production'.center(80)}\n")
        elif success_rate >= 80:
            print(f"{Fore.YELLOW}{'⚠ MOST TESTS PASSED'.center(80)}")
            print(f"{Fore.YELLOW}{'Review failed tests before deployment'.center(80)}\n")
        else:
            print(f"{Fore.RED}{'✗ MULTIPLE TEST FAILURES'.center(80)}")
            print(f"{Fore.RED}{'Fix critical issues before deployment'.center(80)}\n")
        
        if failed > 0:
            print(f"{Fore.RED}Failed Tests:")
            for i, error in enumerate(self.test_results['errors'], 1):
                print(f"{Fore.RED}  {i}. {error['message']}")
                if error['details']:
                    details = str(error['details'])[:100]
                    print(f"{Fore.RED}     {details}...")
    
    def run_all_tests(self):
        """Run complete integration test suite"""
        self.print_header("RX UPLOAD SYSTEM - COMPLETE INTEGRATION TEST")
        
        print(f"{Fore.CYAN}Testing all customer endpoints with Django Test Client")
        print(f"{Fore.CYAN}This test validates the complete prescription ordering workflow\n")
        
        # Setup
        if not self.setup_test_user():
            print(f"\n{Fore.RED}✗ Cannot proceed without test user setup")
            return
        
        # Run tests in sequence
        tests = [
            self.test_upload_prescription,
            self.test_add_patient_info,
            self.test_get_addresses,
            self.test_get_delivery_options,
            self.test_submit_order,
            self.test_get_summary,
            self.test_get_my_prescriptions
        ]
        
        for test_func in tests:
            try:
                test_func()
            except Exception as e:
                self.print_error(f"Test crashed: {test_func.__name__}", str(e))
        
        # Print summary
        self.print_summary()
        
        return self.test_results['passed'] == self.test_results['total']


if __name__ == '__main__':
    print(f"{Fore.CYAN}Starting Complete Integration Test...")
    print(f"{Fore.CYAN}Using Django Test Client with force_login authentication\n")
    
    tester = IntegrationTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
