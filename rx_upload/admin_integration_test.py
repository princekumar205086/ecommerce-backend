"""
Comprehensive Admin Integration Tests for RX Upload
Tests all admin endpoints with JWT authentication
Target: 100% Success Rate
"""
import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from rx_upload.models import PrescriptionUpload, VerifierWorkload, VerificationActivity
import uuid

User = get_user_model()


class AdminIntegrationTest(TestCase):
    """Comprehensive tests for admin prescription management"""
    
    def setUp(self):
        """Setup test data with admin, verifiers, and prescriptions"""
        self.client = APIClient()
        
        # Create admin user with is_staff=True (required for IsAdminUser permission)
        self.admin_user = User.objects.create_user(
            email='admin@medixmall.com',
            password='Admin@12345',
            full_name='System Admin',
            role='admin',
            is_active=True,
            contact='9999999999',
            is_staff=True  # Required for IsAdminUser permission
        )
        self.admin_user.email_verified = True
        self.admin_user.save()
        
        # Create verifiers
        self.verifier1 = User.objects.create_user(
            email='verifier1@medixmall.com',
            password='Verifier@123',
            full_name='Dr. John Doe',
            role='rx_verifier',
            is_active=True,
            contact='9876543210'
        )
        self.verifier1.email_verified = True
        self.verifier1.save()
        
        self.verifier2 = User.objects.create_user(
            email='verifier2@medixmall.com',
            password='Verifier@123',
            full_name='Dr. Jane Smith',
            role='rx_verifier',
            is_active=True,
            contact='9876543211'
        )
        self.verifier2.email_verified = True
        self.verifier2.save()
        
        # Create customer
        self.customer = User.objects.create_user(
            email='customer@example.com',
            password='Customer@123',
            full_name='Test Customer',
            role='customer',
            is_active=True,
            contact='9876543212'
        )
        self.customer.email_verified = True
        self.customer.save()
        
        # Create workloads for verifiers
        self.workload1 = VerifierWorkload.objects.create(
            verifier=self.verifier1,
            is_available=True,
            max_daily_capacity=50
        )
        
        self.workload2 = VerifierWorkload.objects.create(
            verifier=self.verifier2,
            is_available=True,
            max_daily_capacity=50
        )
        
        # Create test prescriptions
        self.prescription1 = PrescriptionUpload.objects.create(
            customer=self.customer,
            prescription_number=f'RX{uuid.uuid4().hex[:8].upper()}',
            verification_status='pending',
            is_urgent=False
        )
        
        self.prescription2 = PrescriptionUpload.objects.create(
            customer=self.customer,
            prescription_number=f'RX{uuid.uuid4().hex[:8].upper()}',
            verification_status='pending',
            is_urgent=True
        )
        
        self.prescription3 = PrescriptionUpload.objects.create(
            customer=self.customer,
            prescription_number=f'RX{uuid.uuid4().hex[:8].upper()}',
            verification_status='in_review',
            verified_by=self.verifier1,
            is_urgent=False
        )
        
        # Get admin JWT token (generate directly instead of via login API)
        refresh = RefreshToken.for_user(self.admin_user)
        self.admin_token = str(refresh.access_token)
    
    def obtain_jwt_token(self, user):
        """Helper to get JWT token directly for a user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def set_admin_auth(self):
        """Set admin authentication header"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
    
    def test_01_admin_dashboard(self):
        """Test admin dashboard endpoint"""
        print("\n=== Test 01: Admin Dashboard ===")
        self.set_admin_auth()
        
        response = self.client.get('/api/rx-upload/admin/dashboard/')
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('overview', response.data['data'])
        self.assertIn('verifiers', response.data['data'])
        self.assertIn('performance', response.data['data'])
        
        # Verify statistics
        overview = response.data['data']['overview']
        self.assertEqual(overview['total_prescriptions'], 3)
        self.assertEqual(overview['pending'], 2)
        self.assertEqual(overview['in_review'], 1)
        
        print("✅ Admin Dashboard Test Passed!")
    
    def test_02_admin_list_prescriptions(self):
        """Test listing all prescriptions with filters"""
        print("\n=== Test 02: Admin List Prescriptions ===")
        self.set_admin_auth()
        
        # Test basic listing
        response = self.client.get('/api/rx-upload/admin/prescriptions/')
        
        print(f"Status Code: {response.status_code}")
        print(f"Total Prescriptions: {response.data['data']['pagination']['total_count']}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['pagination']['total_count'], 3)
        
        # Test filtering by status
        response = self.client.get('/api/rx-upload/admin/prescriptions/?status=pending')
        self.assertEqual(response.data['data']['pagination']['total_count'], 2)
        
        # Test urgent filter
        response = self.client.get('/api/rx-upload/admin/prescriptions/?urgent=true')
        self.assertEqual(response.data['data']['pagination']['total_count'], 1)
        
        print("✅ Admin List Prescriptions Test Passed!")
    
    def test_03_admin_assign_prescription(self):
        """Test assigning prescription to verifier"""
        print("\n=== Test 03: Admin Assign Prescription ===")
        self.set_admin_auth()
        
        response = self.client.post(
            f'/api/rx-upload/admin/prescriptions/{self.prescription1.id}/assign/',
            {
                'verifier_id': self.verifier1.id,
                'is_urgent': False,
                'priority_level': 2
            },
            format='json'
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify assignment
        self.prescription1.refresh_from_db()
        self.assertEqual(self.prescription1.verified_by_id, self.verifier1.id)
        self.assertEqual(self.prescription1.verification_status, 'in_review')
        
        # Verify activity log created
        activity_exists = VerificationActivity.objects.filter(
            prescription=self.prescription1,
            action='assigned'
        ).exists()
        self.assertTrue(activity_exists)
        
        print("✅ Admin Assign Prescription Test Passed!")
    
    def test_04_admin_reassign_prescription(self):
        """Test reassigning prescription to different verifier"""
        print("\n=== Test 04: Admin Reassign Prescription ===")
        self.set_admin_auth()
        
        response = self.client.post(
            f'/api/rx-upload/admin/prescriptions/{self.prescription3.id}/reassign/',
            {
                'verifier_id': self.verifier2.id,
                'reason': 'Workload balancing test'
            },
            format='json'
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify reassignment
        self.prescription3.refresh_from_db()
        self.assertEqual(self.prescription3.verified_by_id, self.verifier2.id)
        
        print("✅ Admin Reassign Prescription Test Passed!")
    
    def test_05_admin_bulk_assign(self):
        """Test bulk assignment with balanced strategy"""
        print("\n=== Test 05: Admin Bulk Assign ===")
        self.set_admin_auth()
        
        # Create additional pending prescriptions
        prescription4 = PrescriptionUpload.objects.create(
            customer=self.customer,
            prescription_number=f'RX{uuid.uuid4().hex[:8].upper()}',
            verification_status='pending'
        )
        
        prescription5 = PrescriptionUpload.objects.create(
            customer=self.customer,
            prescription_number=f'RX{uuid.uuid4().hex[:8].upper()}',
            verification_status='pending'
        )
        
        response = self.client.post(
            '/api/rx-upload/admin/prescriptions/bulk-assign/',
            {
                'prescription_ids': [
                    str(self.prescription2.id),
                    str(prescription4.id),
                    str(prescription5.id)
                ],
                'strategy': 'balanced'
            },
            format='json'
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['assigned_count'], 3)
        
        # Verify all assigned
        self.prescription2.refresh_from_db()
        prescription4.refresh_from_db()
        prescription5.refresh_from_db()
        
        self.assertIsNotNone(self.prescription2.verified_by)
        self.assertIsNotNone(prescription4.verified_by)
        self.assertIsNotNone(prescription5.verified_by)
        
        print("✅ Admin Bulk Assign Test Passed!")
    
    def test_06_admin_list_verifiers(self):
        """Test listing all verifiers with workload"""
        print("\n=== Test 06: Admin List Verifiers ===")
        self.set_admin_auth()
        
        response = self.client.get('/api/rx-upload/admin/verifiers/list/')
        
        print(f"Status Code: {response.status_code}")
        print(f"Total Verifiers: {len(response.data['data'])}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']), 2)
        
        # Verify workload data included
        verifier_data = response.data['data'][0]
        self.assertIn('workload', verifier_data)
        self.assertIn('in_review_count', verifier_data['workload'])
        
        print("✅ Admin List Verifiers Test Passed!")
    
    def test_07_admin_update_verifier_status(self):
        """Test updating verifier availability and capacity"""
        print("\n=== Test 07: Admin Update Verifier Status ===")
        self.set_admin_auth()
        
        response = self.client.post(
            f'/api/rx-upload/admin/verifiers/{self.verifier1.id}/update-status/',
            {
                'is_active': True,
                'is_available': False,
                'max_daily_capacity': 100
            },
            format='json'
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify updates
        self.workload1.refresh_from_db()
        self.assertEqual(self.workload1.is_available, False)
        self.assertEqual(self.workload1.max_daily_capacity, 100)
        
        print("✅ Admin Update Verifier Status Test Passed!")
    
    def test_08_admin_performance_report(self):
        """Test generating performance report"""
        print("\n=== Test 08: Admin Performance Report ===")
        self.set_admin_auth()
        
        # Create some completed prescriptions for report
        completed_rx = PrescriptionUpload.objects.create(
            customer=self.customer,
            prescription_number=f'RX{uuid.uuid4().hex[:8].upper()}',
            verification_status='approved',
            verified_by=self.verifier1,
            verification_date=timezone.now()
        )
        
        response = self.client.get('/api/rx-upload/admin/reports/performance/')
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('overall', response.data['data'])
        self.assertIn('verifier_breakdown', response.data['data'])
        
        # Verify overall stats
        overall = response.data['data']['overall']
        self.assertGreater(overall['total_prescriptions'], 0)
        self.assertGreaterEqual(overall['approved'], 1)
        
        print("✅ Admin Performance Report Test Passed!")
    
    def test_09_admin_unauthorized_access(self):
        """Test that non-admin users cannot access admin endpoints"""
        print("\n=== Test 09: Admin Unauthorized Access ===")
        
        # Get customer token (generate directly)
        customer_token = self.obtain_jwt_token(self.customer)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {customer_token}')
        
        # Try to access admin dashboard
        response = self.client.get('/api/rx-upload/admin/dashboard/')
        
        print(f"Status Code: {response.status_code}")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        print("✅ Admin Unauthorized Access Test Passed!")
    
    def test_10_admin_assign_invalid_verifier(self):
        """Test error handling when assigning to invalid verifier"""
        print("\n=== Test 10: Admin Assign Invalid Verifier ===")
        self.set_admin_auth()
        
        response = self.client.post(
            f'/api/rx-upload/admin/prescriptions/{self.prescription1.id}/assign/',
            {
                'verifier_id': 99999  # Non-existent verifier
            },
            format='json'
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        
        print("✅ Admin Assign Invalid Verifier Test Passed!")


def run_tests():
    """Run all admin integration tests"""
    import unittest
    
    print("="*70)
    print("ADMIN INTEGRATION TESTS - COMPREHENSIVE TEST SUITE")
    print("Testing all admin endpoints for RX Upload System")
    print("="*70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(AdminIntegrationTest)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL ADMIN TESTS PASSED - 100% SUCCESS RATE! 🎉")
        success_rate = 100.0
    else:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
        print(f"\n⚠️  Success Rate: {success_rate:.1f}%")
    
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
