# coupon/tests/test_application_views.py
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


class CouponValidationViewTest(TestCase):
    """Test coupon validation endpoint"""
    
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
        
        # Create valid coupon
        self.valid_coupon = Coupon.objects.create(
            code='VALIDATE10',
            description='Validation test coupon',
            coupon_type='percentage',
            discount_value=Decimal('10.00'),
            max_discount=Decimal('50.00'),
            min_order_amount=Decimal('100.00'),
            applicable_to='all',
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            max_uses=10,
            is_active=True,
            assigned_to_all=True,
            created_by=self.admin_user
        )
        
        # Create user-specific coupon
        self.user_specific = Coupon.objects.create(
            code='USERONLY',
            coupon_type='fixed_amount',
            discount_value=Decimal('25.00'),
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            max_uses=5,
            is_active=True,
            assigned_to_all=False,
            created_by=self.admin_user
        )
        self.user_specific.assigned_users.add(self.regular_user)
    
    def test_validate_valid_coupon(self):
        """Test validating a valid coupon"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('coupon-validate')
        
        data = {
            'code': 'VALIDATE10',
            'cart_total': '200.00'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['coupon_code'], 'VALIDATE10')
        self.assertTrue(response.data['is_valid'])
        self.assertEqual(response.data['message'], 'Valid coupon')
        self.assertIn('coupon_details', response.data)
        self.assertIn('preview', response.data)
        
        # Check preview calculation
        preview = response.data['preview']
        self.assertEqual(preview['cart_total'], Decimal('200.00'))
        self.assertEqual(preview['discount_amount'], Decimal('20.00'))  # 10% of 200
        self.assertEqual(preview['final_total'], Decimal('180.00'))
    
    def test_validate_invalid_coupon_code(self):
        """Test validating non-existent coupon code"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('coupon-validate')
        
        data = {
            'code': 'NONEXISTENT',
            'cart_total': '200.00'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('code', response.data)
    
    def test_validate_coupon_insufficient_cart_amount(self):
        """Test validating coupon with insufficient cart amount"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('coupon-validate')
        
        data = {
            'code': 'VALIDATE10',
            'cart_total': '50.00'  # Below minimum of 100
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_valid'])
        self.assertIn('Minimum order amount not met', response.data['message'])
    
    def test_validate_user_specific_coupon_correct_user(self):
        """Test validating user-specific coupon with correct user"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('coupon-validate')
        
        data = {
            'code': 'USERONLY',
            'cart_total': '100.00'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_valid'])
    
    def test_validate_user_specific_coupon_wrong_user(self):
        """Test validating user-specific coupon with wrong user"""
        wrong_user = User.objects.create_user(
            email='wrong@test.com',
            password='wrongpass123',
            full_name='Wrong User',
            role='user'
        )
        
        self.client.force_authenticate(user=wrong_user)
        url = reverse('coupon-validate')
        
        data = {
            'code': 'USERONLY',
            'cart_total': '100.00'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_valid'])
        self.assertIn('not assigned to this user', response.data['message'])
    
    def test_validate_requires_authentication(self):
        """Test validation endpoint requires authentication"""
        url = reverse('coupon-validate')
        
        data = {
            'code': 'VALIDATE10',
            'cart_total': '200.00'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CouponApplyViewTest(TestCase):
    """Test coupon application endpoint"""
    
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
        
        # Create test coupons
        self.percentage_coupon = Coupon.objects.create(
            code='APPLY20',
            description='Application test coupon',
            coupon_type='percentage',
            discount_value=Decimal('20.00'),
            max_discount=Decimal('100.00'),
            min_order_amount=Decimal('200.00'),
            applicable_to='all',
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            max_uses=10,
            is_active=True,
            assigned_to_all=True,
            created_by=self.admin_user
        )
        
        self.fixed_coupon = Coupon.objects.create(
            code='FIXED50',
            coupon_type='fixed_amount',
            discount_value=Decimal('50.00'),
            min_order_amount=Decimal('100.00'),
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            max_uses=5,
            is_active=True,
            assigned_to_all=True,
            created_by=self.admin_user
        )
    
    def test_apply_valid_percentage_coupon(self):
        """Test applying valid percentage coupon"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('coupon-apply')
        
        data = {
            'code': 'APPLY20',
            'cart_total': '300.00'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['coupon_code'], 'APPLY20')
        self.assertEqual(response.data['discount_amount'], Decimal('60.00'))  # 20% of 300
        self.assertEqual(response.data['original_total'], Decimal('300.00'))
        self.assertEqual(response.data['new_total'], Decimal('240.00'))
        self.assertEqual(response.data['savings_percentage'], 20.0)
        self.assertIn('coupon_details', response.data)
    
    def test_apply_valid_fixed_amount_coupon(self):
        """Test applying valid fixed amount coupon"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('coupon-apply')
        
        data = {
            'code': 'FIXED50',
            'cart_total': '150.00'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['discount_amount'], Decimal('50.00'))
        self.assertEqual(response.data['new_total'], Decimal('100.00'))
    
    def test_apply_percentage_coupon_with_max_discount(self):
        """Test percentage coupon respects max discount limit"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('coupon-apply')
        
        data = {
            'code': 'APPLY20',
            'cart_total': '1000.00'  # 20% would be 200, but max is 100
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['discount_amount'], Decimal('100.00'))  # Capped at max_discount
        self.assertEqual(response.data['new_total'], Decimal('900.00'))
    
    def test_apply_invalid_coupon_code(self):
        """Test applying invalid coupon code"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('coupon-apply')
        
        data = {
            'code': 'INVALID',
            'cart_total': '200.00'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_apply_coupon_insufficient_cart_amount(self):
        """Test applying coupon with insufficient cart amount"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('coupon-apply')
        
        data = {
            'code': 'APPLY20',
            'cart_total': '100.00'  # Below minimum of 200
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_apply_coupon_requires_authentication(self):
        """Test coupon application requires authentication"""
        url = reverse('coupon-apply')
        
        data = {
            'code': 'APPLY20',
            'cart_total': '300.00'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CouponRecordUsageViewTest(TestCase):
    """Test coupon usage recording endpoint"""
    
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
            code='RECORD_TEST',
            coupon_type='fixed_amount',
            discount_value=Decimal('30.00'),
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            max_uses=5,
            is_active=True,
            assigned_to_all=True,
            created_by=self.admin_user
        )
    
    def test_record_coupon_usage_success(self):
        """Test successfully recording coupon usage"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('coupon-record-usage')
        
        data = {
            'coupon_code': 'RECORD_TEST',
            'order_id': 'ORDER123',
            'discount_amount': '30.00'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['coupon_code'], 'RECORD_TEST')
        
        # Verify usage was recorded
        usage = CouponUsage.objects.get(order_id='ORDER123')
        self.assertEqual(usage.coupon, self.coupon)
        self.assertEqual(usage.user, self.regular_user)
        self.assertEqual(usage.discount_amount, Decimal('30.00'))
        
        # Verify coupon usage count updated
        self.coupon.refresh_from_db()
        self.assertEqual(self.coupon.used_count, 1)
    
    def test_record_usage_missing_fields(self):
        """Test recording usage with missing required fields"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('coupon-record-usage')
        
        # Missing discount_amount
        data = {
            'coupon_code': 'RECORD_TEST',
            'order_id': 'ORDER123'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_record_usage_invalid_coupon(self):
        """Test recording usage for invalid coupon"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('coupon-record-usage')
        
        data = {
            'coupon_code': 'INVALID',
            'order_id': 'ORDER123',
            'discount_amount': '30.00'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid coupon code', response.data['error'])
    
    def test_record_usage_duplicate_order(self):
        """Test recording usage for same order twice"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('coupon-record-usage')
        
        data = {
            'coupon_code': 'RECORD_TEST',
            'order_id': 'ORDER123',
            'discount_amount': '30.00'
        }
        
        # First usage - should succeed
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Second usage with same order_id - should fail
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_record_usage_max_uses_exceeded(self):
        """Test recording usage when max uses exceeded"""
        # Set coupon to max uses
        self.coupon.used_count = 5  # Max uses is 5
        self.coupon.save()
        
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('coupon-record-usage')
        
        data = {
            'coupon_code': 'RECORD_TEST',
            'order_id': 'ORDER123',
            'discount_amount': '30.00'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_record_usage_requires_authentication(self):
        """Test usage recording requires authentication"""
        url = reverse('coupon-record-usage')
        
        data = {
            'coupon_code': 'RECORD_TEST',
            'order_id': 'ORDER123',
            'discount_amount': '30.00'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)