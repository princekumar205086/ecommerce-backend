# coupon/tests/test_user_views.py
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from coupon.models import Coupon, CouponUsage

User = get_user_model()


class UserCouponViewTest(TestCase):
    """Test user coupon views"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='adminpass123',
            full_name='Admin User',
            role='admin'
        )
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            password='userpass123',
            full_name='User One',
            role='user'
        )
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            password='userpass123',
            full_name='User Two',
            role='user'
        )
        
        # Set up test dates
        self.valid_from = timezone.now()
        self.valid_to = self.valid_from + timedelta(days=30)
        
        # Create public coupon (available to all)
        self.public_coupon = Coupon.objects.create(
            code='PUBLIC10',
            description='Public coupon for all users',
            coupon_type='percentage',
            discount_value=Decimal('10.00'),
            min_order_amount=Decimal('100.00'),
            applicable_to='all',
            valid_from=self.valid_from,
            valid_to=self.valid_to,
            max_uses=100,
            is_active=True,
            assigned_to_all=True,
            created_by=self.admin_user
        )
        
        # Create user-specific coupon
        self.user_specific_coupon = Coupon.objects.create(
            code='USER1SPECIAL',
            description='Special coupon for user1',
            coupon_type='fixed_amount',
            discount_value=Decimal('50.00'),
            min_order_amount=Decimal('200.00'),
            applicable_to='all',
            valid_from=self.valid_from,
            valid_to=self.valid_to,
            max_uses=5,
            is_active=True,
            assigned_to_all=False,
            created_by=self.admin_user
        )
        self.user_specific_coupon.assigned_users.add(self.user1)
        
        # Create inactive coupon (should not appear in user lists)
        self.inactive_coupon = Coupon.objects.create(
            code='INACTIVE',
            description='Inactive coupon',
            coupon_type='percentage',
            discount_value=Decimal('20.00'),
            valid_from=self.valid_from,
            valid_to=self.valid_to,
            is_active=False,
            assigned_to_all=True,
            created_by=self.admin_user
        )
    
    def test_user_can_list_available_coupons(self):
        """Test authenticated user can list their available coupons"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('user-coupon-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)  # Public + user-specific
        
        # Check response structure
        self.assertIn('available_coupons', response.data)
        self.assertIn('summary', response.data)
        
        # Check that both coupons are returned
        codes = [coupon['code'] for coupon in response.data['available_coupons']]
        self.assertIn('PUBLIC10', codes)
        self.assertIn('USER1SPECIAL', codes)
        
        # Check that inactive coupon is not returned
        self.assertNotIn('INACTIVE', codes)
    
    def test_user_only_sees_their_assigned_coupons(self):
        """Test user only sees coupons assigned to them or public coupons"""
        self.client.force_authenticate(user=self.user2)
        url = reverse('user-coupon-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)  # Only public coupon
        
        codes = [coupon['code'] for coupon in response.data['available_coupons']]
        self.assertIn('PUBLIC10', codes)
        self.assertNotIn('USER1SPECIAL', codes)  # Not assigned to user2
    
    def test_unauthenticated_user_cannot_list_coupons(self):
        """Test unauthenticated users cannot access user coupon list"""
        url = reverse('user-coupon-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_user_can_get_coupon_details(self):
        """Test user can get details of available coupon"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('user-coupon-detail', kwargs={'pk': self.public_coupon.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 'PUBLIC10')
        self.assertIn('discount_display', response.data)
        self.assertIn('validity_status', response.data)
        self.assertIn('can_use', response.data)
    
    def test_user_cannot_get_unassigned_coupon_details(self):
        """Test user cannot get details of coupons not assigned to them"""
        self.client.force_authenticate(user=self.user2)
        url = reverse('user-coupon-detail', kwargs={'pk': self.user_specific_coupon.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_user_coupon_list_filtering(self):
        """Test user can filter their available coupons"""
        self.client.force_authenticate(user=self.user1)
        
        # Filter by coupon type
        url = reverse('user-coupon-list') + '?coupon_type=percentage'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)  # Only percentage coupon
        
        # Filter by applicable_to
        url = reverse('user-coupon-list') + '?applicable_to=all'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)  # Both coupons are for 'all'
    
    def test_user_coupon_list_search(self):
        """Test user can search their available coupons"""
        self.client.force_authenticate(user=self.user1)
        
        # Search by code
        url = reverse('user-coupon-list') + '?search=PUBLIC'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['available_coupons'][0]['code'], 'PUBLIC10')
    
    def test_expired_coupons_not_shown(self):
        """Test expired coupons are not shown in user list"""
        # Create expired coupon
        past_date = timezone.now() - timedelta(days=10)
        expired_coupon = Coupon.objects.create(
            code='EXPIRED',
            coupon_type='percentage',
            discount_value=Decimal('15.00'),
            valid_from=past_date,
            valid_to=past_date + timedelta(days=5),  # Expired
            is_active=True,
            assigned_to_all=True,
            created_by=self.admin_user
        )
        
        self.client.force_authenticate(user=self.user1)
        url = reverse('user-coupon-list')
        response = self.client.get(url)
        
        codes = [coupon['code'] for coupon in response.data['available_coupons']]
        self.assertNotIn('EXPIRED', codes)
    
    def test_future_coupons_not_shown(self):
        """Test future coupons are not shown in user list"""
        # Create future coupon
        future_date = timezone.now() + timedelta(days=10)
        future_coupon = Coupon.objects.create(
            code='FUTURE',
            coupon_type='percentage',
            discount_value=Decimal('15.00'),
            valid_from=future_date,  # Future start date
            valid_to=future_date + timedelta(days=30),
            is_active=True,
            assigned_to_all=True,
            created_by=self.admin_user
        )
        
        self.client.force_authenticate(user=self.user1)
        url = reverse('user-coupon-list')
        response = self.client.get(url)
        
        codes = [coupon['code'] for coupon in response.data['available_coupons']]
        self.assertNotIn('FUTURE', codes)


class UserCouponUsageViewTest(TestCase):
    """Test user coupon usage views"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='adminpass123',
            full_name='Admin User',
            role='admin'
        )
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            password='userpass123',
            full_name='User One',
            role='user'
        )
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            password='userpass123',
            full_name='User Two',
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
        
        # Create usage records for both users
        self.usage1 = CouponUsage.objects.create(
            coupon=self.coupon,
            user=self.user1,
            order_id='ORDER123',
            discount_amount=Decimal('25.00')
        )
        self.usage2 = CouponUsage.objects.create(
            coupon=self.coupon,
            user=self.user2,
            order_id='ORDER456',
            discount_amount=Decimal('25.00')
        )
    
    def test_user_can_list_own_usage_history(self):
        """Test user can list their own coupon usage history"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('user-coupon-usage')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['order_id'], 'ORDER123')
    
    def test_user_only_sees_own_usage_history(self):
        """Test user only sees their own usage records, not others'"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('user-coupon-usage')
        response = self.client.get(url)
        
        # Should only see user1's usage, not user2's
        self.assertEqual(response.data['count'], 1)
        order_ids = [usage['order_id'] for usage in response.data['results']]
        self.assertIn('ORDER123', order_ids)
        self.assertNotIn('ORDER456', order_ids)
    
    def test_unauthenticated_user_cannot_access_usage_history(self):
        """Test unauthenticated users cannot access usage history"""
        url = reverse('user-coupon-usage')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_user_usage_history_filtering(self):
        """Test user can filter their usage history"""
        # Create another coupon with different type
        percentage_coupon = Coupon.objects.create(
            code='PERCENTAGE_TEST',
            coupon_type='percentage',
            discount_value=Decimal('15.00'),
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            is_active=True,
            assigned_to_all=True,
            created_by=self.admin_user
        )
        
        CouponUsage.objects.create(
            coupon=percentage_coupon,
            user=self.user1,
            order_id='ORDER789',
            discount_amount=Decimal('30.00')
        )
        
        self.client.force_authenticate(user=self.user1)
        
        # Filter by coupon type
        url = reverse('user-coupon-usage') + '?coupon__coupon_type=fixed_amount'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['coupon_code'], 'USAGE_TEST')


class PublicCouponViewTest(TestCase):
    """Test public coupon views (no authentication required)"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='adminpass123',
            full_name='Admin User',
            role='admin'
        )
        
        # Create public coupons
        self.public_coupon1 = Coupon.objects.create(
            code='PUBLIC20',
            description='Public discount for all',
            coupon_type='percentage',
            discount_value=Decimal('20.00'),
            max_discount=Decimal('200.00'),
            min_order_amount=Decimal('500.00'),
            applicable_to='all',
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            max_uses=1000,
            is_active=True,
            assigned_to_all=True,
            created_by=self.admin_user
        )
        
        self.public_coupon2 = Coupon.objects.create(
            code='FIXED100',
            description='Fixed discount for all',
            coupon_type='fixed_amount',
            discount_value=Decimal('100.00'),
            min_order_amount=Decimal('800.00'),
            applicable_to='medical',
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=15),
            max_uses=500,
            is_active=True,
            assigned_to_all=True,
            created_by=self.admin_user
        )
        
        # Create private coupon (should not appear in public list)
        self.private_coupon = Coupon.objects.create(
            code='PRIVATE',
            description='Private coupon',
            coupon_type='percentage',
            discount_value=Decimal('25.00'),
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            is_active=True,
            assigned_to_all=False,  # Not public
            created_by=self.admin_user
        )
    
    def test_public_coupon_list_no_authentication(self):
        """Test public coupon list can be accessed without authentication"""
        url = reverse('public-coupon-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)  # Only public coupons
        
        codes = [coupon['code'] for coupon in response.data['promotional_coupons']]
        self.assertIn('PUBLIC20', codes)
        self.assertIn('FIXED100', codes)
        self.assertNotIn('PRIVATE', codes)  # Private coupon not shown
    
    def test_public_coupon_list_limited_information(self):
        """Test public coupon list returns limited information"""
        url = reverse('public-coupon-list')
        response = self.client.get(url)
        
        coupon_data = response.data['promotional_coupons'][0]
        
        # Check that only basic info is exposed
        expected_fields = [
            'code', 'description', 'discount_display', 
            'min_order_amount', 'applicable_to', 'valid_until', 'days_remaining'
        ]
        
        for field in expected_fields:
            self.assertIn(field, coupon_data)
        
        # Check that sensitive info is not exposed
        sensitive_fields = ['max_uses', 'used_count', 'created_by']
        for field in sensitive_fields:
            self.assertNotIn(field, coupon_data)
    
    def test_public_coupon_list_with_authenticated_user(self):
        """Test public coupon list works even with authenticated user"""
        user = User.objects.create_user(
            email='user@test.com',
            password='userpass123',
            full_name='Test User',
            role='user'
        )
        
        self.client.force_authenticate(user=user)
        url = reverse('public-coupon-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
    
    def test_public_coupon_list_filtering(self):
        """Test public coupon list supports filtering"""
        url = reverse('public-coupon-list') + '?coupon_type=percentage'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['promotional_coupons'][0]['code'], 'PUBLIC20')
    
    def test_inactive_coupons_not_in_public_list(self):
        """Test inactive coupons don't appear in public list"""
        self.public_coupon1.is_active = False
        self.public_coupon1.save()
        
        url = reverse('public-coupon-list')
        response = self.client.get(url)
        
        self.assertEqual(response.data['count'], 1)  # Only FIXED100 should remain
        codes = [coupon['code'] for coupon in response.data['promotional_coupons']]
        self.assertNotIn('PUBLIC20', codes)
        self.assertIn('FIXED100', codes)