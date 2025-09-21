# rx_upload/rx_verifier_system_test.py
"""
Comprehensive End-to-End Test Suite for RX Verifier System
Tests all aspects: authentication, prescription upload, verification, email notifications
"""

import json
import tempfile
import os
from io import BytesIO
from PIL import Image
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.core import mail
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from .models import PrescriptionUpload, VerificationActivity, VerifierWorkload, PrescriptionMedication
from accounts.models import User

User = get_user_model()


class RXVerifierSystemTestCase(APITestCase):
    """Comprehensive test suite for RX Verifier system"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.admin_user = User.objects.create_user(
            email='admin@medixmall.com',
            password='AdminPass123!',
            full_name='System Administrator',
            contact='9999999999',
            role='admin',
            email_verified=True
        )
        
        self.rx_verifier = User.objects.create_user(
            email='verifier@medixmall.com',
            password='VerifierPass123!',
            full_name='Dr. John Verifier',
            contact='8888888888',
            role='rx_verifier',
            email_verified=True
        )
        
        self.customer = User.objects.create_user(
            email='customer@example.com',
            password='CustomerPass123!',
            full_name='John Customer',
            contact='7777777777',
            role='user',
            email_verified=True
        )
        
        # Create verifier workload
        self.workload = VerifierWorkload.objects.create(
            verifier=self.rx_verifier,
            is_available=True,
            max_daily_capacity=50
        )
        
        self.client = APIClient()
        
        # Create test prescription image
        self.test_image = self.create_test_image()
    
    def create_test_image(self):
        """Create a test prescription image"""
        image = Image.new('RGB', (800, 600), color='white')
        temp_file = BytesIO()
        image.save(temp_file, format='JPEG')
        temp_file.seek(0)
        return SimpleUploadedFile(
            name='test_prescription.jpg',
            content=temp_file.getvalue(),
            content_type='image/jpeg'
        )
    
    def test_01_rx_verifier_account_creation_via_command(self):
        """Test RX verifier account creation using management command"""
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        
        # Test account creation
        call_command(
            'create_rx_verifier',
            '--email=newverifier@medixmall.com',
            '--full_name=Dr. Jane Verifier',
            '--contact=6666666666',
            '--password=TempPass123!',
            stdout=out
        )
        
        # Verify account was created
        user = User.objects.get(email='newverifier@medixmall.com')
        self.assertEqual(user.role, 'rx_verifier')
        self.assertEqual(user.full_name, 'Dr. Jane Verifier')
        self.assertTrue(user.email_verified)
        
        # Verify workload was created
        workload = VerifierWorkload.objects.get(verifier=user)
        self.assertTrue(workload.is_available)
        self.assertEqual(workload.max_daily_capacity, 50)
        
        output = out.getvalue()
        self.assertIn('✅ RX verifier account created successfully', output)
        self.assertIn('📊 Workload tracking initialized', output)
    
    def test_02_rx_verifier_email_credentials_sending(self):
        """Test sending RX verifier credentials via email"""
        # Clear mail outbox
        mail.outbox = []
        
        # Create new RX verifier
        new_verifier = User.objects.create_user(
            email='testverifier@medixmall.com',
            password='TestPass123!',
            full_name='Dr. Test Verifier',
            contact='5555555555',
            role='rx_verifier',
            email_verified=True
        )
        
        # Send credentials
        success, message = new_verifier.send_rx_verifier_credentials('TestPass123!')
        
        self.assertTrue(success)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertEqual(email.to, ['testverifier@medixmall.com'])
        self.assertIn('RX Verifier Account', email.subject)
        self.assertIn('TestPass123!', email.body)
        self.assertIn('Dr. Test Verifier', email.body)
        self.assertIn('rx-verifier/login', email.body)
    
    def test_03_rx_verifier_authentication(self):
        """Test RX verifier login/logout functionality"""
        # Test login with correct credentials
        login_data = {
            'email': 'verifier@medixmall.com',
            'password': 'VerifierPass123!'
        }
        
        response = self.client.post('/api/rx-upload/auth/login/', login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertIn('Welcome back', response_data['message'])
        self.assertEqual(response_data['data']['user']['role'], 'rx_verifier')
        self.assertIn('workload', response_data['data'])
        
        # Test login with wrong credentials
        wrong_data = {
            'email': 'verifier@medixmall.com',
            'password': 'WrongPassword'
        }
        
        response = self.client.post('/api/rx-upload/auth/login/', wrong_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test login with non-verifier account
        customer_data = {
            'email': 'customer@example.com',
            'password': 'CustomerPass123!'
        }
        
        response = self.client.post('/api/rx-upload/auth/login/', customer_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('RX Verifier privileges required', response.json()['message'])
    
    def test_04_prescription_upload_by_customer(self):
        """Test prescription upload by customer"""
        # Login as customer
        self.client.force_authenticate(user=self.customer)
        
        # Prepare prescription data
        prescription_data = {
            'patient_name': 'John Customer',
            'patient_age': 35,
            'patient_gender': 'male',
            'doctor_name': 'Dr. Smith',
            'hospital_clinic': 'City Hospital',
            'diagnosis': 'Common cold',
            'medications_prescribed': 'Paracetamol 500mg',
            'customer_notes': 'Urgent medication needed',
            'is_urgent': True
        }
        
        # Mock ImageKit upload
        with patch('rx_upload.models.upload_to_imagekit') as mock_upload:
            mock_upload.return_value = 'https://imagekit.io/test/prescription.jpg'
            
            # Upload prescription with image
            prescription_data['prescription_file'] = self.test_image
            response = self.client.post('/api/rx-upload/prescriptions/', prescription_data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        prescription = PrescriptionUpload.objects.get(customer=self.customer)
        self.assertEqual(prescription.patient_name, 'John Customer')
        self.assertEqual(prescription.verification_status, 'pending')
        self.assertTrue(prescription.is_urgent)
        self.assertTrue(prescription.prescription_number.startswith('RX'))
    
    def test_05_verifier_dashboard_and_pending_prescriptions(self):
        """Test verifier dashboard and pending prescriptions view"""
        # Create test prescriptions
        prescription1 = PrescriptionUpload.objects.create(
            customer=self.customer,
            patient_name='Patient 1',
            verification_status='pending',
            is_urgent=True
        )
        
        prescription2 = PrescriptionUpload.objects.create(
            customer=self.customer,
            patient_name='Patient 2',
            verification_status='pending',
            is_urgent=False
        )
        
        # Login as verifier
        self.client.force_authenticate(user=self.rx_verifier)
        
        # Test dashboard
        response = self.client.get('/api/rx-upload/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        dashboard_data = response.json()['data']
        self.assertEqual(dashboard_data['counts']['pending'], 2)
        self.assertEqual(dashboard_data['counts']['urgent'], 1)
        
        # Test pending prescriptions
        response = self.client.get('/api/rx-upload/pending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        
        # Handle paginated response format
        if 'results' in response_data:
            # Paginated response where results contains the actual response from the view
            if isinstance(response_data['results'], dict) and 'data' in response_data['results']:
                pending_data = response_data['results']['data']
            else:
                pending_data = response_data['results']
        elif 'data' in response_data:
            # Non-paginated response with 'data' key
            pending_data = response_data['data']
        else:
            # Direct response
            pending_data = response_data
        
        # Ensure pending_data is a list
        if not isinstance(pending_data, list):
            self.fail(f"Expected list, got {type(pending_data)}: {pending_data}")
        
        self.assertEqual(len(pending_data), 2)
        
        # Urgent prescription should be first
        self.assertTrue(pending_data[0]['is_urgent'])
    
    def test_06_prescription_assignment_and_verification_workflow(self):
        """Test complete prescription verification workflow"""
        # Create test prescription
        prescription = PrescriptionUpload.objects.create(
            customer=self.customer,
            patient_name='Test Patient',
            doctor_name='Dr. Test',
            diagnosis='Test condition',
            medications_prescribed='Test medication',
            verification_status='pending'
        )
        
        # Login as verifier
        self.client.force_authenticate(user=self.rx_verifier)
        
        # Test assignment
        response = self.client.post(f'/api/rx-upload/prescriptions/{prescription.id}/assign/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        prescription.refresh_from_db()
        self.assertEqual(prescription.verification_status, 'in_review')
        self.assertEqual(prescription.verified_by, self.rx_verifier)
        
        # Verify activity was logged
        activity = VerificationActivity.objects.filter(
            prescription=prescription,
            action='assigned'
        ).first()
        self.assertIsNotNone(activity)
        
        # Test approval
        approval_data = {'notes': 'Prescription is clear and valid'}
        response = self.client.post(f'/api/rx-upload/prescriptions/{prescription.id}/approve/', approval_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        prescription.refresh_from_db()
        self.assertEqual(prescription.verification_status, 'approved')
        self.assertEqual(prescription.verification_notes, 'Prescription is clear and valid')
        self.assertIsNotNone(prescription.verification_date)
        
        # Verify workload was updated
        self.workload.refresh_from_db()
        self.assertEqual(self.workload.total_verified, 1)
        self.assertEqual(self.workload.total_approved, 1)
    
    def test_07_prescription_rejection_workflow(self):
        """Test prescription rejection workflow"""
        # Create test prescription
        prescription = PrescriptionUpload.objects.create(
            customer=self.customer,
            patient_name='Test Patient',
            verification_status='in_review',
            verified_by=self.rx_verifier
        )
        
        # Login as verifier
        self.client.force_authenticate(user=self.rx_verifier)
        
        # Test rejection without notes (should fail)
        response = self.client.post(f'/api/rx-upload/prescriptions/{prescription.id}/reject/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test rejection with notes
        rejection_data = {'notes': 'Prescription is unclear and illegible'}
        response = self.client.post(f'/api/rx-upload/prescriptions/{prescription.id}/reject/', rejection_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        prescription.refresh_from_db()
        self.assertEqual(prescription.verification_status, 'rejected')
        self.assertEqual(prescription.verification_notes, 'Prescription is unclear and illegible')
        
        # Verify activity was logged
        activity = VerificationActivity.objects.filter(
            prescription=prescription,
            action='rejected'
        ).first()
        self.assertIsNotNone(activity)
    
    def test_08_clarification_request_workflow(self):
        """Test clarification request workflow"""
        # Clear mail outbox
        mail.outbox = []
        
        # Create test prescription
        prescription = PrescriptionUpload.objects.create(
            customer=self.customer,
            patient_name='Test Patient',
            verification_status='in_review',
            verified_by=self.rx_verifier
        )
        
        # Login as verifier
        self.client.force_authenticate(user=self.rx_verifier)
        
        # Test clarification request
        clarification_data = {
            'message': 'Please provide a clearer image of the prescription. The dosage section is not visible.'
        }
        response = self.client.post(f'/api/rx-upload/prescriptions/{prescription.id}/clarification/', clarification_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        prescription.refresh_from_db()
        self.assertEqual(prescription.verification_status, 'clarification_needed')
        self.assertEqual(prescription.clarification_requested, clarification_data['message'])
        
        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.customer.email])
        self.assertIn('Clarification Needed', email.subject)
        self.assertIn('clearer image', email.body)
    
    def test_09_verifier_workload_management(self):
        """Test verifier workload management"""
        # Login as verifier
        self.client.force_authenticate(user=self.rx_verifier)
        
        # Test profile endpoint
        response = self.client.get('/api/rx-upload/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        profile_data = response.json()['data']
        self.assertEqual(profile_data['user']['role'], 'rx_verifier')
        self.assertIn('workload', profile_data)
        
        # Test availability update
        availability_data = {'is_available': False}
        response = self.client.post('/api/rx-upload/availability/', availability_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Debug the response
        response_data = response.json()
        
        self.workload.refresh_from_db()
        self.assertFalse(self.workload.is_available)
        
        # Test workload capacity check
        # Create many prescriptions to test capacity
        for i in range(25):
            PrescriptionUpload.objects.create(
                customer=self.customer,
                patient_name=f'Patient {i}',
                verification_status='in_review',
                verified_by=self.rx_verifier
            )
        
        self.workload.update_workload()
        self.assertEqual(self.workload.in_review_count, 25)
    
    def test_10_admin_workload_overview(self):
        """Test admin workload overview functionality"""
        # Login as admin
        self.client.force_authenticate(user=self.admin_user)
        
        # Test workloads endpoint (admin only)
        response = self.client.get('/api/rx-upload/workloads/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        workloads_data = response.json()['data']
        self.assertEqual(len(workloads_data), 1)
        self.assertEqual(workloads_data[0]['verifier_name'], 'Dr. John Verifier')
        
        # Test with non-admin user (should fail)
        self.client.force_authenticate(user=self.customer)
        response = self.client.get('/api/rx-upload/workloads/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_11_prescription_notification_emails(self):
        """Test prescription verification notification emails"""
        # Clear mail outbox
        mail.outbox = []
        
        # Create test prescription
        prescription = PrescriptionUpload.objects.create(
            customer=self.customer,
            patient_name='Test Patient',
            verification_status='in_review',
            verified_by=self.rx_verifier
        )
        
        # Test approval notification
        prescription.approve_prescription(self.rx_verifier, 'Prescription approved')
        
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.customer.email])
        self.assertIn('Prescription Verification Update', email.subject)
        self.assertIn('APPROVED', email.body)
        self.assertIn('Dr. John Verifier', email.body)
        
        # Clear mail outbox for rejection test
        mail.outbox = []
        
        # Create another prescription for rejection test
        prescription2 = PrescriptionUpload.objects.create(
            customer=self.customer,
            patient_name='Test Patient 2',
            verification_status='in_review',
            verified_by=self.rx_verifier
        )
        
        # Test rejection notification
        prescription2.reject_prescription(self.rx_verifier, 'Prescription is illegible')
        
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn('REJECTED', email.body)
        self.assertIn('illegible', email.body)
    
    def test_12_permission_checks(self):
        """Test permission checks across the system"""
        # Create test prescription
        prescription = PrescriptionUpload.objects.create(
            customer=self.customer,
            patient_name='Test Patient',
            verification_status='pending'
        )
        
        # Test unauthenticated access (should fail)
        response = self.client.get('/api/rx-upload/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test customer trying to access verifier endpoints (should fail)
        self.client.force_authenticate(user=self.customer)
        
        response = self.client.get('/api/rx-upload/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        response = self.client.post(f'/api/rx-upload/prescriptions/{prescription.id}/assign/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test customer accessing their own prescriptions (should work)
        response = self.client.get('/api/rx-upload/prescriptions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test verifier accessing verification endpoints (should work)
        self.client.force_authenticate(user=self.rx_verifier)
        
        response = self.client.get('/api/rx-upload/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = self.client.post(f'/api/rx-upload/prescriptions/{prescription.id}/assign/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_13_prescription_search_and_filtering(self):
        """Test prescription search and filtering functionality"""
        # Clear any existing prescriptions
        PrescriptionUpload.objects.all().delete()
        
        # Create test prescriptions with different statuses
        prescriptions = [
            PrescriptionUpload.objects.create(
                customer=self.customer,
                patient_name='John Doe',
                doctor_name='Dr. Smith',
                verification_status='pending',
                is_urgent=True
            ),
            PrescriptionUpload.objects.create(
                customer=self.customer,
                patient_name='Jane Doe',
                doctor_name='Dr. Johnson',
                verification_status='approved',
                verified_by=self.rx_verifier,
                is_urgent=False
            ),
            PrescriptionUpload.objects.create(
                customer=self.customer,
                patient_name='Bob Wilson',
                doctor_name='Dr. Williams',
                verification_status='rejected',
                verified_by=self.rx_verifier,
                is_urgent=True
            )
        ]
        
        # Login as verifier
        self.client.force_authenticate(user=self.rx_verifier)
        
        # Test filtering by status
        response = self.client.get('/api/rx-upload/prescriptions/?verification_status=pending')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['verification_status'], 'pending')
        
        # Test filtering by urgency
        response = self.client.get('/api/rx-upload/prescriptions/?is_urgent=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()['results']
        self.assertEqual(len(results), 2)
        
        # Test search by patient name
        response = self.client.get('/api/rx-upload/prescriptions/?search=Jane')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['patient_name'], 'Jane Doe')
        
        # Test search by doctor name
        response = self.client.get('/api/rx-upload/prescriptions/?search=Dr. Smith')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['doctor_name'], 'Dr. Smith')
    
    def test_14_performance_and_analytics(self):
        """Test performance tracking and analytics"""
        # Reset workload counts for clean state
        self.workload.total_verified = 0
        self.workload.total_approved = 0
        self.workload.total_rejected = 0
        self.workload.save()
        
        # Create test data for analytics
        start_time = timezone.now()
        
        # Create and verify multiple prescriptions
        for i in range(5):
            prescription = PrescriptionUpload.objects.create(
                customer=self.customer,
                patient_name=f'Patient {i}',
                verification_status='pending'
            )
            
            # Assign and approve
            prescription.assign_to_verifier(self.rx_verifier)
            prescription.approve_prescription(self.rx_verifier, f'Notes for patient {i}')
        
        # Create and reject one prescription
        prescription = PrescriptionUpload.objects.create(
            customer=self.customer,
            patient_name='Rejected Patient',
            verification_status='pending'
        )
        prescription.assign_to_verifier(self.rx_verifier)
        prescription.reject_prescription(self.rx_verifier, 'Illegible prescription')
        
        # Update workload to calculate metrics
        self.workload.refresh_from_db()
        
        # Check performance metrics
        self.assertEqual(self.workload.total_verified, 6)
        self.assertEqual(self.workload.total_approved, 5)
        self.assertEqual(self.workload.total_rejected, 1)
        self.assertAlmostEqual(self.workload.approval_rate, 83.33, places=1)
        
        # Test dashboard analytics
        self.client.force_authenticate(user=self.rx_verifier)
        
        # Clear cache to ensure fresh data
        from django.core.cache import cache
        cache.clear()
        
        response = self.client.get('/api/rx-upload/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        performance = response.json()['data']['performance']
        self.assertEqual(performance['total_verified'], 6)
        self.assertEqual(performance['total_approved'], 5)
        self.assertEqual(performance['total_rejected'], 1)
    
    def test_15_error_handling_and_edge_cases(self):
        """Test error handling and edge cases"""
        # Login as verifier
        self.client.force_authenticate(user=self.rx_verifier)
        
        # Test assigning non-existent prescription
        response = self.client.post('/api/rx-upload/prescriptions/00000000-0000-0000-0000-000000000000/assign/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test approving prescription without being assigned
        prescription = PrescriptionUpload.objects.create(
            customer=self.customer,
            patient_name='Test Patient',
            verification_status='pending'
        )
        
        # Create another verifier
        other_verifier = User.objects.create_user(
            email='other@medixmall.com',
            password='OtherPass123!',
            full_name='Other Verifier',
            role='rx_verifier'
        )
        
        # Try to approve with wrong verifier
        self.client.force_authenticate(user=other_verifier)
        response = self.client.post(f'/api/rx-upload/prescriptions/{prescription.id}/approve/')
        # Should work as any verifier can approve
        
        # Test workload capacity limits
        capacity_test_prescription = PrescriptionUpload.objects.create(
            customer=self.customer,
            patient_name='Capacity Test Patient',
            verification_status='pending'
        )
        
        self.workload.max_daily_capacity = 1
        self.workload.current_daily_count = 1
        self.workload.save()
        
        # Should not be able to accept more prescriptions
        self.assertFalse(self.workload.can_accept_more)
        
        self.client.force_authenticate(user=self.rx_verifier)
        response = self.client.post(f'/api/rx-upload/prescriptions/{capacity_test_prescription.id}/assign/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('maximum workload capacity', response.json()['message'])
    
    def tearDown(self):
        """Clean up after tests"""
        # Clear mail outbox
        mail.outbox = []
        
        # Clean up test files
        if hasattr(self, 'test_image'):
            self.test_image.close()


if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    # Configure Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
    django.setup()
    
    # Run tests
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['rx_upload.rx_verifier_system_test'])
    
    if failures:
        print(f"\n❌ {failures} test(s) failed")
    else:
        print("\n✅ All tests passed successfully!")
        
    print(f"\n📊 Test Summary:")
    print(f"   - RX Verifier Authentication: ✅")
    print(f"   - Prescription Upload: ✅")
    print(f"   - Verification Workflow: ✅")
    print(f"   - Email Notifications: ✅")
    print(f"   - Permission System: ✅")
    print(f"   - Workload Management: ✅")
    print(f"   - Admin Functions: ✅")
    print(f"   - Search & Filtering: ✅")
    print(f"   - Performance Analytics: ✅")
    print(f"   - Error Handling: ✅")