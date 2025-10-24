"""
Comprehensive tests for admin user management system
Enterprise-level testing for all admin operations
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from django.utils import timezone
import json

User = get_user_model()


class AdminUserManagementTestCase(APITestCase):
    """Test admin user management endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create admin user
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            full_name='Admin User',
            contact='9876543210',
            password='admin123',
            role='admin'
        )
        self.admin_user.is_staff = True
        self.admin_user.is_superuser = True
        self.admin_user.email_verified = True
        self.admin_user.save()
        
        # Create regular users
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            full_name='User One',
            contact='9876543211',
            password='user123',
            role='user'
        )
        self.user1.email_verified = True
        self.user1.save()
        
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            full_name='User Two',
            contact='9876543212',
            password='user123',
            role='user'
        )
        
        # Create supplier
        self.supplier = User.objects.create_user(
            email='supplier@test.com',
            full_name='Supplier User',
            contact='9876543213',
            password='supplier123',
            role='supplier'
        )
        
        # Get admin token
        self.admin_token = str(RefreshToken.for_user(self.admin_user).access_token)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
    
    def test_admin_list_users(self):
        """Test listing all users"""
        print("\n🧪 Test: Admin List Users")
        
        response = self.client.get('/api/accounts/admin/users/')
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Users Count: {response.data.get('count', 0)}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 4)  # At least 4 users
        print("   ✅ Admin can list all users")
    
    def test_admin_filter_users_by_role(self):
        """Test filtering users by role"""
        print("\n🧪 Test: Filter Users by Role")
        
        response = self.client.get('/api/accounts/admin/users/?role=supplier')
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Suppliers Count: {response.data.get('count', 0)}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        print("   ✅ Role filtering works correctly")
    
    def test_admin_filter_users_by_status(self):
        """Test filtering users by active status"""
        print("\n🧪 Test: Filter Users by Active Status")
        
        response = self.client.get('/api/accounts/admin/users/?is_active=true')
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Active Users: {response.data.get('count', 0)}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("   ✅ Status filtering works correctly")
    
    def test_admin_search_users(self):
        """Test searching users"""
        print("\n🧪 Test: Search Users")
        
        response = self.client.get('/api/accounts/admin/users/?search=user1')
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Search Results: {response.data.get('count', 0)}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)
        print("   ✅ User search works correctly")
    
    def test_admin_get_user_detail(self):
        """Test getting detailed user information"""
        print("\n🧪 Test: Get User Detail")
        
        response = self.client.get(f'/api/accounts/admin/users/{self.user1.id}/')
        
        print(f"   Status Code: {response.status_code}")
        print(f"   User Email: {response.data.get('email', 'N/A')}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user1.email)
        self.assertIn('account_stats', response.data)
        print("   ✅ User detail retrieval works correctly")
    
    def test_admin_create_user(self):
        """Test creating a new user"""
        print("\n🧪 Test: Create User")
        
        user_data = {
            'email': 'newuser@test.com',
            'full_name': 'New User',
            'contact': '9876543220',
            'role': 'user',
            'password': 'newuser123',
            'password2': 'newuser123',
            'is_active': True,
            'email_verified': True,
            'send_credentials_email': False
        }
        
        response = self.client.post('/api/accounts/admin/users/create/', user_data)
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 201:
            print(f"   Created User: {response.data.get('user', {}).get('email', 'N/A')}")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['email'], 'newuser@test.com')
        
        # Verify user exists
        self.assertTrue(User.objects.filter(email='newuser@test.com').exists())
        print("   ✅ User creation works correctly")
    
    def test_admin_update_user(self):
        """Test updating user information"""
        print("\n🧪 Test: Update User")
        
        update_data = {
            'full_name': 'Updated User Name',
            'is_active': True
        }
        
        response = self.client.patch(
            f'/api/accounts/admin/users/{self.user1.id}/update/',
            update_data
        )
        
        print(f"   Status Code: {response.status_code}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify update
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.full_name, 'Updated User Name')
        print("   ✅ User update works correctly")
    
    def test_admin_change_user_role(self):
        """Test changing user role"""
        print("\n🧪 Test: Change User Role")
        
        role_data = {
            'role': 'supplier',
            'reason': 'User requested supplier access'
        }
        
        response = self.client.post(
            f'/api/accounts/admin/users/{self.user1.id}/change-role/',
            role_data
        )
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"   New Role: {response.data.get('user', {}).get('role', 'N/A')}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify role change
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.role, 'supplier')
        print("   ✅ Role change works correctly")
    
    def test_admin_change_user_status(self):
        """Test activating/deactivating user"""
        print("\n🧪 Test: Change User Status")
        
        status_data = {
            'is_active': False,
            'reason': 'Suspicious activity'
        }
        
        response = self.client.post(
            f'/api/accounts/admin/users/{self.user2.id}/change-status/',
            status_data
        )
        
        print(f"   Status Code: {response.status_code}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify status change
        self.user2.refresh_from_db()
        self.assertFalse(self.user2.is_active)
        print("   ✅ Status change works correctly")
    
    def test_admin_bulk_activate_users(self):
        """Test bulk activating users"""
        print("\n🧪 Test: Bulk Activate Users")
        
        bulk_data = {
            'user_ids': [self.user1.id, self.user2.id],
            'action': 'activate',
            'reason': 'Bulk activation test'
        }
        
        response = self.client.post(
            '/api/accounts/admin/users/bulk-action/',
            bulk_data,
            format='json'
        )
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"   Affected: {response.data.get('affected_count', 0)}/{response.data.get('total_count', 0)}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['affected_count'], 2)
        print("   ✅ Bulk activation works correctly")
    
    def test_admin_bulk_verify_emails(self):
        """Test bulk email verification"""
        print("\n🧪 Test: Bulk Verify Emails")
        
        bulk_data = {
            'user_ids': [self.user2.id],
            'action': 'verify_email'
        }
        
        response = self.client.post(
            '/api/accounts/admin/users/bulk-action/',
            bulk_data,
            format='json'
        )
        
        print(f"   Status Code: {response.status_code}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify email verified
        self.user2.refresh_from_db()
        self.assertTrue(self.user2.email_verified)
        print("   ✅ Bulk email verification works correctly")
    
    def test_admin_delete_user(self):
        """Test deleting (deactivating) user"""
        print("\n🧪 Test: Delete User")
        
        # Create a user to delete
        temp_user = User.objects.create_user(
            email='temp@test.com',
            full_name='Temp User',
            contact='9876543299',
            password='temp123'
        )
        
        response = self.client.delete(f'/api/accounts/admin/users/{temp_user.id}/delete/')
        
        print(f"   Status Code: {response.status_code}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify user is deactivated
        temp_user.refresh_from_db()
        self.assertFalse(temp_user.is_active)
        print("   ✅ User deletion (soft delete) works correctly")
    
    def test_admin_cannot_delete_self(self):
        """Test admin cannot delete own account"""
        print("\n🧪 Test: Cannot Delete Self")
        
        response = self.client.delete(f'/api/accounts/admin/users/{self.admin_user.id}/delete/')
        
        print(f"   Status Code: {response.status_code}")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        print("   ✅ Self-deletion prevention works correctly")
    
    def test_admin_get_statistics(self):
        """Test getting user statistics"""
        print("\n🧪 Test: Get User Statistics")
        
        response = self.client.get('/api/accounts/admin/statistics/')
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"   Total Users: {response.data.get('total_users', 0)}")
            print(f"   Active Users: {response.data.get('active_users', 0)}")
            print(f"   Verified Users: {response.data.get('verified_users', 0)}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_users', response.data)
        self.assertIn('users_by_role', response.data)
        self.assertIn('growth_rate', response.data)
        print("   ✅ Statistics retrieval works correctly")
    
    def test_admin_view_audit_logs(self):
        """Test viewing audit logs"""
        print("\n🧪 Test: View Audit Logs")
        
        response = self.client.get('/api/accounts/admin/audit-logs/')
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"   Audit Logs Count: {response.data.get('count', 0)}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("   ✅ Audit logs retrieval works correctly")
    
    def test_admin_create_rx_verifier(self):
        """Test creating RX Verifier account"""
        print("\n🧪 Test: Create RX Verifier")
        
        rx_data = {
            'email': 'rxverifier@test.com',
            'full_name': 'RX Verifier',
            'contact': '9876543230',
            'password': 'rx123456',
            'password2': 'rx123456',
            'send_credentials_email': False
        }
        
        response = self.client.post('/api/accounts/admin/rx-verifiers/create/', rx_data)
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 201:
            print(f"   Created RX Verifier: {response.data.get('user', {}).get('email', 'N/A')}")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify RX verifier exists with correct role
        rx_user = User.objects.get(email='rxverifier@test.com')
        self.assertEqual(rx_user.role, 'rx_verifier')
        self.assertTrue(rx_user.email_verified)
        print("   ✅ RX Verifier creation works correctly")
    
    def test_admin_export_users_csv(self):
        """Test exporting users to CSV"""
        print("\n🧪 Test: Export Users CSV")
        
        response = self.client.get('/api/accounts/admin/users/export/')
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Content Type: {response.get('Content-Type', 'N/A')}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get('Content-Type'), 'text/csv')
        print("   ✅ CSV export works correctly")
    
    def test_non_admin_cannot_access_admin_endpoints(self):
        """Test that non-admin users cannot access admin endpoints"""
        print("\n🧪 Test: Non-Admin Access Denied")
        
        # Get regular user token
        user_token = str(RefreshToken.for_user(self.user1).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {user_token}')
        
        response = self.client.get('/api/accounts/admin/users/')
        
        print(f"   Status Code: {response.status_code}")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        print("   ✅ Access control works correctly")
    
    def test_pagination(self):
        """Test pagination on user list"""
        print("\n🧪 Test: Pagination")
        
        # Create more users for pagination
        for i in range(25):
            User.objects.create_user(
                email=f'paginationtest{i}@test.com',
                full_name=f'Pagination Test {i}',
                contact=f'98765432{i:02d}',
                password='test123'
            )
        
        response = self.client.get('/api/accounts/admin/users/?page_size=10')
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Results in Page: {len(response.data.get('results', []))}")
        print(f"   Total Count: {response.data.get('count', 0)}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertIn('next', response.data)
        print("   ✅ Pagination works correctly")


class AdminPermissionTestCase(APITestCase):
    """Test admin permissions"""
    
    def setUp(self):
        """Set up test users"""
        self.admin = User.objects.create_user(
            email='admin@test.com',
            password='admin123',
            role='admin'
        )
        self.admin.is_staff = True
        self.admin.is_superuser = True
        self.admin.save()
        
        self.user = User.objects.create_user(
            email='user@test.com',
            password='user123',
            role='user'
        )
    
    def test_admin_role_required(self):
        """Test that admin role is required"""
        print("\n🔒 Test: Admin Role Required")
        
        client = APIClient()
        user_token = str(RefreshToken.for_user(self.user).access_token)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {user_token}')
        
        response = client.get('/api/accounts/admin/users/')
        
        print(f"   Status Code: {response.status_code}")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        print("   ✅ Admin permission check works correctly")
    
    def test_admin_can_access(self):
        """Test that admin can access admin endpoints"""
        print("\n🔒 Test: Admin Can Access")
        
        client = APIClient()
        admin_token = str(RefreshToken.for_user(self.admin).access_token)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
        
        response = client.get('/api/accounts/admin/users/')
        
        print(f"   Status Code: {response.status_code}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("   ✅ Admin access works correctly")


def run_all_tests():
    """Run all admin user management tests"""
    print("\n" + "="*80)
    print("🚀 RUNNING COMPREHENSIVE ADMIN USER MANAGEMENT TESTS")
    print("="*80)
    
    from django.test.runner import DiscoverRunner
    
    test_runner = DiscoverRunner(verbosity=2)
    failures = test_runner.run_tests(['accounts.tests_admin.test_admin_user_management'])
    
    print("\n" + "="*80)
    if failures == 0:
        print("✅ ALL TESTS PASSED!")
    else:
        print(f"❌ {failures} TEST(S) FAILED")
    print("="*80 + "\n")
    
    return failures


if __name__ == '__main__':
    print("\n🧪 Starting Admin User Management Tests...")
    run_all_tests()
