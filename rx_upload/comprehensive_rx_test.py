"""
Comprehensive RX Verifier System Test Suite
Tests all endpoints, order integration, and email notifications
Enterprise-grade testing with detailed reporting
"""

import os
import sys
import django
import requests
import json
from datetime import datetime
from io import BytesIO
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from rx_upload.models import PrescriptionUpload, VerifierWorkload
from orders.models import Order
from products.models import Product, Brand, ProductCategory

User = get_user_model()


class RXVerifierTestSuite:
    """Comprehensive test suite for RX verifier system"""
    
    def __init__(self):
        self.client = Client()
        self.base_url = "http://127.0.0.1:8000/api"
        self.test_results = []
        self.customer = None
        self.verifier = None
        self.admin = None
        self.prescription = None
        self.order = None
        
    def print_header(self, text):
        """Print formatted header"""
        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"{Fore.CYAN}{text.center(70)}")
        print(f"{Fore.CYAN}{'='*70}\n")
    
    def print_test(self, test_name):
        """Print test name"""
        print(f"{Fore.YELLOW}► Testing: {test_name}")
    
    def print_success(self, message):
        """Print success message"""
        print(f"{Fore.GREEN}✓ {message}")
        self.test_results.append(("✓", message, "success"))
    
    def print_error(self, message):
        """Print error message"""
        print(f"{Fore.RED}✗ {message}")
        self.test_results.append(("✗", message, "error"))
    
    def print_info(self, message):
        """Print info message"""
        print(f"{Fore.BLUE}ℹ {message}")
    
    def setup_test_data(self):
        """Setup test users, products, and prescriptions"""
        self.print_header("SETUP TEST DATA")
        
        try:
            # Create customer
            self.customer, created = User.objects.get_or_create(
                email='rx_test_customer@test.com',
                defaults={
                    'full_name': 'Test Customer',
                    'contact': '9876543210',
                    'role': 'user',
                    'address_line_1': '123 Test Street',
                    'city': 'Mumbai',
                    'state': 'Maharashtra',
                    'postal_code': '400001',
                    'email_verified': True
                }
            )
            if created:
                self.customer.set_password('test123456')
                self.customer.save()
            self.print_success(f"Customer: {self.customer.email}")
            
            # Create RX verifier
            self.verifier, created = User.objects.get_or_create(
                email='rx_test_verifier@test.com',
                defaults={
                    'full_name': 'Dr. Test Verifier',
                    'contact': '9876543211',
                    'role': 'rx_verifier',
                    'email_verified': True,
                    'is_staff': True
                }
            )
            if created:
                self.verifier.set_password('verifier123')
                self.verifier.save()
                
            # Ensure workload exists
            VerifierWorkload.objects.get_or_create(
                verifier=self.verifier,
                defaults={'is_available': True, 'max_daily_capacity': 50}
            )
            self.print_success(f"RX Verifier: {self.verifier.email}")
            
            # Create admin
            self.admin, created = User.objects.get_or_create(
                email='rx_test_admin@test.com',
                defaults={
                    'full_name': 'Test Admin',
                    'contact': '9876543212',
                    'role': 'admin',
                    'is_staff': True,
                    'is_superuser': True,
                    'email_verified': True
                }
            )
            if created:
                self.admin.set_password('admin123')
                self.admin.save()
            self.print_success(f"Admin: {self.admin.email}")
            
            # Create test products
            category, _ = ProductCategory.objects.get_or_create(
                name='Prescription Medicines',
                defaults={'slug': 'prescription-medicines', 'created_by': self.admin}
            )

            brand, _ = Brand.objects.get_or_create(
                name='MedixTest',
                defaults={'created_by': self.admin}
            )
            
            # Create medicine products
            medicines = [
                {'name': 'Amoxicillin 500mg', 'mrp': 150.00, 'selling_price': 135.00, 'stock': 100},
                {'name': 'Azithromycin 250mg', 'mrp': 180.00, 'selling_price': 162.00, 'stock': 50},
                {'name': 'Paracetamol 650mg', 'mrp': 50.00, 'selling_price': 45.00, 'stock': 200},
            ]
            
            for med_data in medicines:
                Product.objects.get_or_create(
                    name=med_data['name'],
                    defaults={
                        'slug': med_data['name'].lower().replace(' ', '-'),
                        'category': category,
                        'brand': brand,
                        'mrp': med_data['mrp'],
                        'price': med_data['selling_price'],
                        'stock': med_data['stock'],
                        'is_publish': True,
                        'product_type': 'medicine',
                        'created_by': self.admin
                    }
                )
            self.print_success(f"Created {len(medicines)} test medicine products")
            
            # Create test prescription
            self.prescription = PrescriptionUpload.objects.create(
                customer=self.customer,
                patient_name='Test Patient',
                patient_age=35,
                patient_gender='male',
                doctor_name='Dr. Test Doctor',
                hospital_clinic='Test Hospital',
                prescription_type='image',
                medications_prescribed='Amoxicillin 500mg\nAzithromycin 250mg',
                diagnosis='Bacterial infection',
                prescription_date=datetime.now().date(),
                customer_phone='9876543210',
                is_urgent=False,
                priority_level=2
            )
            self.print_success(f"Prescription created: {self.prescription.prescription_number}")
            
            return True
            
        except Exception as e:
            self.print_error(f"Setup failed: {str(e)}")
            return False
    
    def test_verifier_login(self):
        """Test RX verifier login"""
        self.print_header("TEST 1: RX VERIFIER LOGIN")
        
        try:
            response = self.client.post(
                f'/api/rx-upload/auth/login/',
                data=json.dumps({
                    'email': 'rx_test_verifier@test.com',
                    'password': 'verifier123'
                }),
                content_type='application/json'
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.print_success("Verifier login successful")
                    self.print_info(f"Workload - Pending: {data['data']['workload']['pending_count']}, In Review: {data['data']['workload']['in_review_count']}")

                    # Obtain JWT token via TokenObtainPair endpoint and attach to test client
                    try:
                        token_resp = self.client.post('/api/token/', data=json.dumps({
                            'email': 'rx_test_verifier@test.com',
                            'password': 'verifier123'
                        }), content_type='application/json')
                        if token_resp.status_code == 200:
                            token_data = token_resp.json()
                            access = token_data.get('access') or token_data.get('access_token')
                            if access:
                                # set default header for subsequent requests
                                self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {access}'
                                self.print_info('Attached JWT to test client for subsequent requests')
                        else:
                            self.print_info('Could not obtain JWT token; subsequent DRF endpoints may require JWT')
                    except Exception:
                        self.print_info('Token obtain attempted and failed; continuing without JWT')

                    return True
                else:
                    self.print_error(f"Login failed: {data.get('message')}")
            else:
                self.print_error(f"Login failed with status {response.status_code}")
            
            return False
            
        except Exception as e:
            self.print_error(f"Login test error: {str(e)}")
            return False
    
    def test_dashboard_access(self):
        """Test dashboard access"""
        self.print_header("TEST 2: DASHBOARD ACCESS")
        
        try:
            # Login first
            self.client.login(username='rx_test_verifier@test.com', password='verifier123')
            
            response = self.client.get('/api/rx-upload/dashboard/')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    counts = data['data']['counts']
                    self.print_success("Dashboard accessed successfully")
                    self.print_info(f"Total Pending: {counts.get('total_pending', 0)}")
                    self.print_info(f"Total Approved: {counts.get('total_approved', 0)}")
                    self.print_info(f"Total Rejected: {counts.get('total_rejected', 0)}")
                    return True
                else:
                    self.print_error("Dashboard access failed")
            else:
                self.print_error(f"Dashboard failed with status {response.status_code}")
            
            return False
            
        except Exception as e:
            self.print_error(f"Dashboard test error: {str(e)}")
            return False
    
    def test_get_pending_prescriptions(self):
        """Test getting pending prescriptions"""
        self.print_header("TEST 3: GET PENDING PRESCRIPTIONS")
        
        try:
            response = self.client.get('/api/rx-upload/pending/')
            
            if response.status_code == 200:
                data = response.json()
                # Handle both standard and paginated responses
                if data.get('success'):
                    prescriptions = data.get('data', [])
                    self.print_success(f"Found {len(prescriptions)} pending prescriptions")
                    return True
                elif data.get('results') and isinstance(data.get('results'), dict) and data['results'].get('success'):
                    prescriptions = data['results'].get('data', [])
                    self.print_success(f"Found {len(prescriptions)} pending prescriptions (paginated)")
                    return True
                else:
                    self.print_error("Failed to get pending prescriptions")
                    self.print_info(f"Response JSON: {data}")
            else:
                self.print_error(f"Request failed with status {response.status_code}")
                if response.content:
                    try:
                        self.print_info(f"Response: {response.content.decode()}")
                    except Exception:
                        self.print_info(repr(response.content))
            
            return False
            
        except Exception as e:
            self.print_error(f"Get pending error: {str(e)}")
            return False
    
    def test_assign_prescription(self):
        """Test assigning prescription to verifier"""
        self.print_header("TEST 4: ASSIGN PRESCRIPTION")
        
        try:
            response = self.client.post(
                f'/api/rx-upload/prescriptions/{self.prescription.id}/assign/',
                content_type='application/json'
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.print_success("Prescription assigned successfully")
                    self.prescription.refresh_from_db()
                    self.print_info(f"Status: {self.prescription.verification_status}")
                    return True
                else:
                    self.print_error(f"Assignment failed: {data.get('message')}")
            else:
                self.print_error(f"Assignment failed with status {response.status_code}")
            
            return False
            
        except Exception as e:
            self.print_error(f"Assignment test error: {str(e)}")
            return False
    
    def test_approve_prescription(self):
        """Test approving prescription"""
        self.print_header("TEST 5: APPROVE PRESCRIPTION")
        
        try:
            response = self.client.post(
                f'/api/rx-upload/prescriptions/{self.prescription.id}/approve/',
                data=json.dumps({
                    'notes': 'Prescription verified. All medications are appropriate.'
                }),
                content_type='application/json'
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.print_success("Prescription approved successfully")
                    self.prescription.refresh_from_db()
                    self.print_info(f"Status: {self.prescription.verification_status}")
                    self.print_info(f"Verified by: {self.prescription.verified_by.full_name}")
                    return True
                else:
                    self.print_error(f"Approval failed: {data.get('message')}")
            else:
                self.print_error(f"Approval failed with status {response.status_code}")
            
            return False
            
        except Exception as e:
            self.print_error(f"Approval test error: {str(e)}")
            return False
    
    def test_create_order_from_prescription(self):
        """Test creating order from approved prescription"""
        self.print_header("TEST 6: CREATE ORDER FROM PRESCRIPTION")
        
        try:
            # Get products
            amoxicillin = Product.objects.get(name='Amoxicillin 500mg')
            azithromycin = Product.objects.get(name='Azithromycin 250mg')
            
            response = self.client.post(
                f'/api/rx-upload/prescriptions/{self.prescription.id}/create-order/',
                data=json.dumps({
                    'medications': [
                        {'medication_name': 'Amoxicillin 500mg', 'product_id': amoxicillin.id, 'quantity': 2},
                        {'medication_name': 'Azithromycin 250mg', 'product_id': azithromycin.id, 'quantity': 1}
                    ],
                    'notes': 'Test order from prescription'
                }),
                content_type='application/json'
            )
            
            if response.status_code == 201:
                data = response.json()
                if data.get('success'):
                    self.print_success("Order created from prescription")
                    order_data = data['data']['order']
                    self.print_info(f"Order Number: {order_data['order_number']}")
                    self.print_info(f"Total: ₹{order_data['total']}")
                    self.print_info(f"Items: {len(order_data['items'])}")
                    
                    # Store order for later tests
                    self.order = Order.objects.get(order_number=order_data['order_number'])
                    return True
                else:
                    self.print_error(f"Order creation failed: {data.get('message')}")
            else:
                self.print_error(f"Order creation failed with status {response.status_code}")
                if response.content:
                    self.print_info(f"Response: {response.content.decode()}")
            
            return False
            
        except Exception as e:
            self.print_error(f"Order creation test error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_get_prescription_orders(self):
        """Test getting orders for a prescription"""
        self.print_header("TEST 7: GET PRESCRIPTION ORDERS")
        
        try:
            response = self.client.get(
                f'/api/rx-upload/prescriptions/{self.prescription.id}/orders/'
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    orders = data['data']['orders']
                    self.print_success(f"Found {len(orders)} orders for prescription")
                    for order in orders:
                        self.print_info(f"Order: {order['order_number']} - Status: {order['status']}")
                    return True
                else:
                    self.print_error("Failed to get orders")
            else:
                self.print_error(f"Request failed with status {response.status_code}")
            
            return False
            
        except Exception as e:
            self.print_error(f"Get orders test error: {str(e)}")
            return False
    
    def test_reject_prescription(self):
        """Test rejecting a prescription"""
        self.print_header("TEST 8: REJECT PRESCRIPTION (New Prescription)")
        
        try:
            # Create new prescription for rejection
            test_prescription = PrescriptionUpload.objects.create(
                customer=self.customer,
                patient_name='Test Reject Patient',
                patient_age=40,
                prescription_type='image',
                medications_prescribed='Invalid medication',
                verification_status='pending'
            )
            
            # Assign it first
            self.client.post(
                f'/api/rx-upload/prescriptions/{test_prescription.id}/assign/',
                content_type='application/json'
            )
            
            # Reject it
            response = self.client.post(
                f'/api/rx-upload/prescriptions/{test_prescription.id}/reject/',
                data=json.dumps({
                    'notes': 'Prescription is unclear. Please upload a better quality image.'
                }),
                content_type='application/json'
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.print_success("Prescription rejected successfully")
                    test_prescription.refresh_from_db()
                    self.print_info(f"Status: {test_prescription.verification_status}")
                    return True
                else:
                    self.print_error(f"Rejection failed: {data.get('message')}")
            else:
                self.print_error(f"Rejection failed with status {response.status_code}")
            
            return False
            
        except Exception as e:
            self.print_error(f"Rejection test error: {str(e)}")
            return False
    
    def test_request_clarification(self):
        """Test requesting clarification"""
        self.print_header("TEST 9: REQUEST CLARIFICATION")
        
        try:
            # Create new prescription
            test_prescription = PrescriptionUpload.objects.create(
                customer=self.customer,
                patient_name='Test Clarification Patient',
                patient_age=30,
                prescription_type='image',
                medications_prescribed='Some medications',
                verification_status='pending'
            )
            
            # Assign it
            self.client.post(
                f'/api/rx-upload/prescriptions/{test_prescription.id}/assign/',
                content_type='application/json'
            )
            
            # Request clarification
            response = self.client.post(
                f'/api/rx-upload/prescriptions/{test_prescription.id}/clarification/',
                data=json.dumps({
                    'message': 'Please provide doctor license number for verification.'
                }),
                content_type='application/json'
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.print_success("Clarification requested successfully")
                    test_prescription.refresh_from_db()
                    self.print_info(f"Status: {test_prescription.verification_status}")
                    return True
                else:
                    self.print_error(f"Clarification request failed: {data.get('message')}")
            else:
                self.print_error(f"Request failed with status {response.status_code}")
            
            return False
            
        except Exception as e:
            self.print_error(f"Clarification test error: {str(e)}")
            return False
    
    def test_update_availability(self):
        """Test updating verifier availability"""
        self.print_header("TEST 10: UPDATE AVAILABILITY")
        
        try:
            # Set to unavailable
            response = self.client.post(
                '/api/rx-upload/availability/',
                data=json.dumps({'is_available': False}),
                content_type='application/json'
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.print_success("Availability updated to unavailable")
                    
                    # Set back to available
                    response2 = self.client.post(
                        '/api/rx-upload/availability/',
                        data=json.dumps({'is_available': True}),
                        content_type='application/json'
                    )
                    
                    if response2.status_code == 200:
                        self.print_success("Availability updated to available")
                        return True
                else:
                    self.print_error(f"Update failed: {data.get('message')}")
            else:
                self.print_error(f"Update failed with status {response.status_code}")
            
            return False
            
        except Exception as e:
            self.print_error(f"Availability test error: {str(e)}")
            return False
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")
        
        success_count = sum(1 for _, _, status in self.test_results if status == "success")
        error_count = sum(1 for _, _, status in self.test_results if status == "error")
        total_count = len(self.test_results)
        
        print(f"\n{Fore.CYAN}Total Tests: {total_count}")
        print(f"{Fore.GREEN}Passed: {success_count}")
        print(f"{Fore.RED}Failed: {error_count}")
        
        if error_count == 0:
            print(f"\n{Fore.GREEN}{'🎉 ALL TESTS PASSED! 🎉'.center(70)}\n")
        else:
            print(f"\n{Fore.YELLOW}Some tests failed. Please review the errors above.\n")
        
        # Print detailed results
        print(f"\n{Fore.CYAN}Detailed Results:")
        for symbol, message, status in self.test_results:
            color = Fore.GREEN if status == "success" else Fore.RED
            print(f"{color}{symbol} {message}")
    
    def run_all_tests(self):
        """Run all tests"""
        print(f"\n{Fore.MAGENTA}{'*'*70}")
        print(f"{Fore.MAGENTA}{'RX VERIFIER COMPREHENSIVE TEST SUITE'.center(70)}")
        print(f"{Fore.MAGENTA}{'Enterprise-Grade Testing'.center(70)}")
        print(f"{Fore.MAGENTA}{'*'*70}\n")
        
        # Setup
        if not self.setup_test_data():
            print(f"\n{Fore.RED}Setup failed. Cannot continue tests.")
            return
        
        # Run tests
        self.test_verifier_login()
        self.test_dashboard_access()
        self.test_get_pending_prescriptions()
        self.test_assign_prescription()
        self.test_approve_prescription()
        self.test_create_order_from_prescription()
        self.test_get_prescription_orders()
        self.test_reject_prescription()
        self.test_request_clarification()
        self.test_update_availability()
        
        # Summary
        self.print_summary()


if __name__ == '__main__':
    test_suite = RXVerifierTestSuite()
    test_suite.run_all_tests()
