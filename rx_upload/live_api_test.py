#!/usr/bin/env python
"""
Live API Test for RX Upload System
Tests all endpoints with real HTTP requests
Requires Django server to be running: python manage.py runserver
"""
import requests
import json
import os
from io import BytesIO
from PIL import Image
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

BASE_URL = 'http://localhost:8000'
API_BASE = f'{BASE_URL}/api/rx-upload'

class LiveAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        self.prescription_id = None
        self.auth_token = None
        
        # Test credentials
        self.customer_email = 'user@example.com'
        self.customer_password = 'User@123'
        self.verifier_email = 'admin@example.com'  # Using admin as verifier
        self.verifier_password = 'Admin@123'
    
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
        return img_byte_arr
    
    def get_csrf_token(self):
        """Get CSRF token from Django"""
        try:
            response = self.session.get(f'{BASE_URL}/admin/login/')
            return self.session.cookies.get('csrftoken', '')
        except:
            return ''
    
    def login_customer(self):
        """Login as customer"""
        self.print_test("Customer Login")
        csrf_token = self.get_csrf_token()
        
        try:
            response = self.session.post(
                f'{BASE_URL}/api/accounts/login/',
                json={
                    'email': self.customer_email,
                    'password': self.customer_password
                },
                headers={
                    'X-CSRFToken': csrf_token,
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code in [200, 201]:
                self.print_success(f"Customer logged in: {self.customer_email}")
                return True
            else:
                self.print_error(f"Login failed: Status {response.status_code}", response.text[:200])
                return False
        except Exception as e:
            self.print_error(f"Login exception: {str(e)}")
            return False
    
    def test_upload_prescription(self):
        """Test prescription upload"""
        self.print_test("Upload Prescription - Valid File")
        
        try:
            # Create test image
            test_image = self.create_test_image()
            
            # Prepare multipart data
            files = {
                'prescription_file': ('test_prescription.jpg', test_image, 'image/jpeg')
            }
            
            csrf_token = self.session.cookies.get('csrftoken', '')
            
            response = self.session.post(
                f'{API_BASE}/customer/upload/',
                files=files,
                headers={'X-CSRFToken': csrf_token}
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                if data.get('success'):
                    self.prescription_id = data['data']['prescription_id']
                    self.print_success(f"Upload successful - ID: {self.prescription_id}")
                    self.print_info(f"Prescription #: {data['data']['prescription_number']}")
                    return True
                else:
                    self.print_error("Response indicates failure", json.dumps(data, indent=2))
            else:
                self.print_error(f"Upload failed: Status {response.status_code}", response.text[:200])
        except Exception as e:
            self.print_error(f"Upload exception: {str(e)}")
        
        return False
    
    def test_add_patient_info(self):
        """Test adding patient information"""
        self.print_test("Add Patient Information")
        
        if not self.prescription_id:
            self.print_error("No prescription ID available")
            return False
        
        try:
            patient_data = {
                'patient_name': 'John Doe Test',
                'customer_phone': '9876543210',
                'patient_age': 30,
                'patient_gender': 'male',
                'emergency_contact': '9123456789'
            }
            
            csrf_token = self.session.cookies.get('csrftoken', '')
            
            response = self.session.post(
                f'{API_BASE}/customer/{self.prescription_id}/patient-info/',
                json=patient_data,
                headers={
                    'X-CSRFToken': csrf_token,
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.print_success("Patient information saved")
                    self.print_info(f"Patient: {data['data']['patient_name']}")
                    return True
                else:
                    self.print_error("Failed to save patient info", json.dumps(data, indent=2))
            else:
                self.print_error(f"Failed: Status {response.status_code}", response.text[:200])
        except Exception as e:
            self.print_error(f"Exception: {str(e)}")
        
        return False
    
    def test_get_addresses(self):
        """Test getting delivery addresses"""
        self.print_test("Get Delivery Addresses")
        
        try:
            response = self.session.get(f'{API_BASE}/customer/addresses/')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    addresses = data.get('data', [])
                    self.print_success(f"Retrieved {len(addresses)} address(es)")
                    if addresses:
                        self.print_info(f"First: {addresses[0]['formatted_address']}")
                    return True
                else:
                    self.print_error("Failed to get addresses", json.dumps(data, indent=2))
            else:
                self.print_error(f"Failed: Status {response.status_code}", response.text[:200])
        except Exception as e:
            self.print_error(f"Exception: {str(e)}")
        
        return False
    
    def test_get_delivery_options(self):
        """Test getting delivery options"""
        self.print_test("Get Delivery Options")
        
        try:
            response = self.session.get(f'{API_BASE}/customer/delivery-options/')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    options = data['data']['options']
                    self.print_success(f"Retrieved {len(options)} option(s)")
                    for opt in options:
                        self.print_info(f"  {opt['name']}: ₹{opt['price']}")
                    return True
                else:
                    self.print_error("Failed to get options", json.dumps(data, indent=2))
            else:
                self.print_error(f"Failed: Status {response.status_code}", response.text[:200])
        except Exception as e:
            self.print_error(f"Exception: {str(e)}")
        
        return False
    
    def test_submit_order(self):
        """Test submitting order"""
        self.print_test("Submit Prescription Order")
        
        if not self.prescription_id:
            self.print_error("No prescription ID available")
            return False
        
        try:
            order_data = {
                'delivery_address_id': 1,
                'delivery_option': 'express',
                'payment_method': 'cod'
            }
            
            csrf_token = self.session.cookies.get('csrftoken', '')
            
            response = self.session.post(
                f'{API_BASE}/customer/{self.prescription_id}/submit/',
                json=order_data,
                headers={
                    'X-CSRFToken': csrf_token,
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.print_success("Order submitted successfully")
                    self.print_info(f"Order ID: {data['data']['order_id']}")
                    self.print_info(f"Delivery: {data['data']['estimated_delivery']}")
                    return True
                else:
                    self.print_error("Failed to submit", json.dumps(data, indent=2))
            else:
                self.print_error(f"Failed: Status {response.status_code}", response.text[:200])
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
            response = self.session.get(f'{API_BASE}/customer/{self.prescription_id}/summary/')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    summary = data['data']
                    self.print_success("Summary retrieved")
                    self.print_info(f"Files: {summary['prescription_files']}")
                    self.print_info(f"Patient: {summary['patient']}")
                    self.print_info(f"Status: {summary['verification_status']}")
                    return True
                else:
                    self.print_error("Failed to get summary", json.dumps(data, indent=2))
            else:
                self.print_error(f"Failed: Status {response.status_code}", response.text[:200])
        except Exception as e:
            self.print_error(f"Exception: {str(e)}")
        
        return False
    
    def test_get_my_prescriptions(self):
        """Test getting prescription history"""
        self.print_test("Get My Prescriptions")
        
        try:
            response = self.session.get(f'{API_BASE}/customer/my-prescriptions/')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    count = data.get('count', 0)
                    self.print_success(f"Retrieved {count} prescription(s)")
                    return True
                else:
                    self.print_error("Failed to get prescriptions", json.dumps(data, indent=2))
            else:
                self.print_error(f"Failed: Status {response.status_code}", response.text[:200])
        except Exception as e:
            self.print_error(f"Exception: {str(e)}")
        
        return False
    
    def run_all_tests(self):
        """Run all tests"""
        print(f"\n{Fore.MAGENTA}{'*' * 80}")
        print(f"{Fore.MAGENTA}{'RX UPLOAD - LIVE API TEST SUITE'.center(80)}")
        print(f"{Fore.MAGENTA}{'*' * 80}\n")
        
        print(f"{Fore.CYAN}Testing API at: {API_BASE}")
        print(f"{Fore.CYAN}Using credentials: {self.customer_email}\n")
        
        # Customer flow
        self.print_header("CUSTOMER FLOW TESTS")
        
        if not self.login_customer():
            print(f"\n{Fore.RED}❌ Cannot continue without successful login")
            print(f"{Fore.YELLOW}Make sure:")
            print(f"{Fore.YELLOW}  1. Django server is running: python manage.py runserver")
            print(f"{Fore.YELLOW}  2. User exists: {self.customer_email}")
            print(f"{Fore.YELLOW}  3. Password is correct: {self.customer_password}")
            return
        
        self.test_upload_prescription()
        self.test_add_patient_info()
        self.test_get_addresses()
        self.test_get_delivery_options()
        self.test_submit_order()
        self.test_get_summary()
        self.test_get_my_prescriptions()
        
        # Print summary
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
            print(f"{Fore.YELLOW}{'⚠ MOST TESTS PASSED'.center(80)}\n")
        else:
            print(f"{Fore.RED}{'❌ MANY TESTS FAILED'.center(80)}\n")
        
        if self.test_results['errors']:
            print(f"{Fore.RED}Failed Tests:")
            for i, error in enumerate(self.test_results['errors'], 1):
                print(f"{Fore.RED}  {i}. {error['message']}")


if __name__ == '__main__':
    print(f"\n{Fore.YELLOW}⚠ IMPORTANT: Make sure Django server is running!")
    print(f"{Fore.YELLOW}Run in another terminal: python manage.py runserver\n")
    
    import time
    time.sleep(2)
    
    tester = LiveAPITester()
    tester.run_all_tests()
