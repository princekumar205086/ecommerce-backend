# coupon/tests/test_admin_views.py
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json

from coupon.models import Coupon, CouponUsage

User = get_user_model()


class AdminCouponViewTest(TestCase):
    """Test admin coupon management views"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='adminpass123',
            full_name='Admin User',
            role='admin'
        )
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            password='userpass123',
            full_name='Regular User',
            role='user'
        )
        self.supplier_user = User.objects.create_user(
            email='supplier@test.com',
            password='supplierpass123',
            full_name='Supplier User',
            role='supplier'
        )
        
        # Set up test dates
        self.valid_from = timezone.now()
        self.valid_to = self.valid_from + timedelta(days=30)
        
        # Create test coupon
        self.test_coupon = Coupon.objects.create(
            code='TESTCOUPON',
            description='Test coupon for admin tests',
            coupon_type='percentage',
            discount_value=Decimal('15.00'),
            max_discount=Decimal('100.00'),
            min_order_amount=Decimal('200.00'),
            applicable_to='all',
            valid_from=self.valid_from,
            valid_to=self.valid_to,
            max_uses=50,
            is_active=True,
            assigned_to_all=True,
            created_by=self.admin_user
        )
    
    def test_admin_can_list_coupons(self):
        """Test admin can list all coupons"""
        self.client.force_authenticate(user=self.admin_user)
        url = '/api/coupons/admin/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['code'], 'TESTCOUPON')
    
    def test_non_admin_cannot_list_coupons(self):
        """Test non-admin users cannot access admin coupon list"""
        self.client.force_authenticate(user=self.regular_user)
        url = '/api/coupons/admin/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_admin_can_create_coupon(self):
        """Test admin can create new coupons"""
        self.client.force_authenticate(user=self.admin_user)
        url = '/api/coupons/admin/'
        
        data = {
            'code': 'NEWCOUPON',
            'description': 'New test coupon',
            'coupon_type': 'fixed_amount',
            'discount_value': '50.00',
            'min_order_amount': '100.00',
            'applicable_to': 'all',
            'valid_from': self.valid_from.isoformat(),
            'valid_to': self.valid_to.isoformat(),
            'max_uses': 25,
            'is_active': True,
            'assigned_to_all': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['code'], 'NEWCOUPON')
        self.assertEqual(Coupon.objects.filter(code='NEWCOUPON').count(), 1)
    
    def test_admin_can_create_coupon_with_user_assignment(self):
        """Test admin can create coupon with specific user assignment"""
        self.client.force_authenticate(user=self.admin_user)
        url = '/api/coupons/admin/'
        
        data = {
            'code': 'USERCOUPON',
            'description': 'User-specific coupon',
            'coupon_type': 'percentage',
            'discount_value': '20.00',
            'max_discount': '100.00',
            'min_order_amount': '200.00',
            'applicable_to': 'all',
            'valid_from': self.valid_from.isoformat(),
            'valid_to': self.valid_to.isoformat(),
            'max_uses': 10,
            'is_active': True,
            'assigned_to_all': False,
            'assigned_user_ids': [self.regular_user.id]
        }
        
        response = self.client.post(url, data, format='json')
        
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Error response: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        coupon = Coupon.objects.get(code='USERCOUPON')
        self.assertIn(self.regular_user, coupon.assigned_users.all())
    
    def test_admin_cannot_create_invalid_coupon(self):
        """Test admin cannot create coupon with invalid data"""
        self.client.force_authenticate(user=self.admin_user)
        url = '/api/coupons/admin/'
        
        # Test invalid percentage > 100
        data = {
            'code': 'INVALID',
            'coupon_type': 'percentage',
            'discount_value': '150.00',  # Invalid
            'valid_from': self.valid_from.isoformat(),
            'valid_to': self.valid_to.isoformat()
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_admin_can_retrieve_coupon_detail(self):
        """Test admin can retrieve specific coupon details"""
        self.client.force_authenticate(user=self.admin_user)
        url = f'/api/coupons/admin/{self.test_coupon.pk}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 'TESTCOUPON')
        self.assertIn('usage_stats', response.data)
        self.assertIn('remaining_uses', response.data)
    
    def test_admin_can_update_coupon(self):
        """Test admin can update existing coupons"""
        self.client.force_authenticate(user=self.admin_user)
        url = f'/api/coupons/admin/{self.test_coupon.pk}/'
        
        data = {
            'description': 'Updated test coupon description',
            'discount_value': '25.00',
            'is_active': False
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.test_coupon.refresh_from_db()
        self.assertEqual(self.test_coupon.description, 'Updated test coupon description')
        self.assertEqual(self.test_coupon.discount_value, Decimal('25.00'))
        self.assertFalse(self.test_coupon.is_active)
    
    def test_admin_can_delete_unused_coupon(self):
        """Test admin can delete unused coupons"""
        self.client.force_authenticate(user=self.admin_user)
        url = f'/api/coupons/admin/{self.test_coupon.pk}/'
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Coupon.objects.filter(pk=self.test_coupon.pk).count(), 0)
    
    def test_admin_cannot_delete_used_coupon(self):
        """Test admin cannot delete coupons that have been used"""
        # Create a usage record
        CouponUsage.objects.create(
            coupon=self.test_coupon,
            user=self.regular_user,
            order_id='ORDER123',
            discount_amount=Decimal('30.00')
        )
        self.test_coupon.used_count = 1
        self.test_coupon.save()
        
        self.client.force_authenticate(user=self.admin_user)
        url = f'/api/coupons/admin/{self.test_coupon.pk}/'
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Coupon should still exist but be deactivated
        self.test_coupon.refresh_from_db()
        self.assertFalse(self.test_coupon.is_active)
    
    def test_admin_bulk_create_coupons(self):
        """Test admin can bulk create multiple coupons"""
        self.client.force_authenticate(user=self.admin_user)
        url = '/api/coupons/admin/bulk_create/'
        
        data = {
            'base_code': 'BULK',
            'quantity': 5,
            'coupon_type': 'percentage',
            'discount_value': '10.00',
            'min_order_amount': '100.00',
            'applicable_to': 'all',
            'valid_from': self.valid_from.isoformat(),
            'valid_to': self.valid_to.isoformat(),
            'max_uses': 1,
            'assigned_to_all': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['coupons']), 5)
        
        # Check that coupons were created with sequential codes
        bulk_coupons = Coupon.objects.filter(code__startswith='BULK')
        self.assertEqual(bulk_coupons.count(), 5)
        codes = [c.code for c in bulk_coupons]
        self.assertIn('BULK001', codes)
        self.assertIn('BULK005', codes)
    
    def test_admin_get_analytics(self):
        """Test admin can get coupon analytics"""
        self.client.force_authenticate(user=self.admin_user)
        url = '/api/coupons/admin/coupons/analytics/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('overview', response.data)
        self.assertIn('financial', response.data)
        self.assertIn('top_performers', response.data)
        self.assertIn('type_distribution', response.data)
    
    def test_admin_get_usage_history(self):
        """Test admin can get coupon usage history"""
        # Create usage record
        CouponUsage.objects.create(
            coupon=self.test_coupon,
            user=self.regular_user,
            order_id='ORDER123',
            discount_amount=Decimal('30.00')
        )
        
        self.client.force_authenticate(user=self.admin_user)
        url = f'/api/coupons/admin/coupons/{self.test_coupon.pk}/usage_history/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_usages'], 1)
        self.assertEqual(len(response.data['usages']), 1)
    
    def test_admin_toggle_coupon_status(self):
        """Test admin can toggle coupon active status"""
        self.client.force_authenticate(user=self.admin_user)
        url = f'/api/coupons/admin/coupons/{self.test_coupon.pk}/toggle_status/'
        
        # Toggle to inactive
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.test_coupon.refresh_from_db()
        self.assertFalse(self.test_coupon.is_active)
        
        # Toggle back to active
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.test_coupon.refresh_from_db()
        self.assertTrue(self.test_coupon.is_active)
    
    def test_admin_list_with_filters(self):
        """Test admin can filter coupon list"""
        # Create additional test coupons
        Coupon.objects.create(
            code='INACTIVE',
            coupon_type='fixed_amount',
            discount_value=Decimal('25.00'),
            valid_from=self.valid_from,
            valid_to=self.valid_to,
            is_active=False,
            created_by=self.admin_user
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        # Test active filter
        url = '/api/coupons/admin/bulk_create/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)  # Only active coupon
        
        # Test coupon type filter
        url = '/api/coupons/admin/coupons/?coupon_type=percentage'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)  # Only percentage coupon
        
        # Test search
        url = '/api/coupons/admin/coupons/?search=TEST'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)  # Only coupon with TEST in code


class AdminCouponUsageViewTest(TestCase):
    """Test admin coupon usage views"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='adminpass123',
            full_name='Admin User',
            role='admin'
        )
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            password='userpass123',
            full_name='Regular User',
            role='user'
        )
        
        self.coupon = Coupon.objects.create(
            code='USAGE_TEST',
            coupon_type='fixed_amount',
            discount_value=Decimal('25.00'),
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            max_uses=10,
            is_active=True,
            assigned_to_all=True,
            created_by=self.admin_user
        )
        
        self.usage = CouponUsage.objects.create(
            coupon=self.coupon,
            user=self.regular_user,
            order_id='ORDER123',
            discount_amount=Decimal('25.00')
        )
    
    def test_admin_can_list_all_usages(self):
        """Test admin can list all coupon usages"""
        self.client.force_authenticate(user=self.admin_user)
        url = '/api/coupons/admin/usages/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['order_id'], 'ORDER123')
    
    def test_admin_can_filter_usages(self):
        """Test admin can filter usage list"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Filter by coupon
        url = f'/api/coupons/admin/usages/?coupon={self.coupon.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        
        # Filter by user
        url = f'/api/coupons/admin/usages/?user={self.regular_user.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
    
    def test_non_admin_cannot_access_usage_list(self):
        """Test non-admin users cannot access admin usage list"""
        self.client.force_authenticate(user=self.regular_user)
        url = '/api/coupons/admin/usages/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)