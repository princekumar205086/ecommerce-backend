# coupon/tests/test_models.py
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model

from coupon.models import Coupon, CouponUsage

User = get_user_model()


class CouponModelTest(TestCase):
    """Test Coupon model functionality"""
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            full_name='Admin User',
            role='admin'
        )
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            password='testpass123',
            full_name='Regular User',
            role='user'
        )
        
        self.valid_from = timezone.now()
        self.valid_to = self.valid_from + timedelta(days=30)
    
    def test_coupon_creation_valid_data(self):
        """Test creating a coupon with valid data"""
        coupon = Coupon.objects.create(
            code='TESTCOUPON',
            description='Test coupon description',
            coupon_type='percentage',
            discount_value=Decimal('20.00'),
            max_discount=Decimal('100.00'),
            min_order_amount=Decimal('500.00'),
            applicable_to='all',
            valid_from=self.valid_from,
            valid_to=self.valid_to,
            max_uses=100,
            is_active=True,
            assigned_to_all=True,
            created_by=self.admin_user
        )
        
        self.assertEqual(coupon.code, 'TESTCOUPON')
        self.assertEqual(coupon.coupon_type, 'percentage')
        self.assertEqual(coupon.discount_value, Decimal('20.00'))
        self.assertTrue(coupon.is_active)
        self.assertEqual(coupon.used_count, 0)
    
    def test_coupon_str_representation(self):
        """Test string representation of coupon"""
        coupon = Coupon.objects.create(
            code='SAVE10',
            coupon_type='percentage',
            discount_value=Decimal('10.00'),
            valid_from=self.valid_from,
            valid_to=self.valid_to,
            created_by=self.admin_user
        )
        
        expected = "SAVE10 (Percentage off)"
        self.assertEqual(str(coupon), expected)
    
    def test_coupon_clean_validation(self):
        """Test model validation in clean method"""
        # Test invalid date range
        coupon = Coupon(
            code='INVALID',
            coupon_type='percentage',
            discount_value=Decimal('20.00'),
            valid_from=self.valid_to,  # Invalid: from > to
            valid_to=self.valid_from,
            created_by=self.admin_user
        )
        
        with self.assertRaises(ValidationError):
            coupon.clean()
    
    def test_coupon_percentage_validation(self):
        """Test percentage discount validation"""
        coupon = Coupon(
            code='INVALID',
            coupon_type='percentage',
            discount_value=Decimal('150.00'),  # Invalid: >100%
            valid_from=self.valid_from,
            valid_to=self.valid_to,
            created_by=self.admin_user
        )
        
        with self.assertRaises(ValidationError):
            coupon.clean()
    
    def test_is_valid_method_basic(self):
        """Test basic is_valid method functionality"""
        coupon = Coupon.objects.create(
            code='VALIDTEST',
            coupon_type='percentage',
            discount_value=Decimal('10.00'),
            min_order_amount=Decimal('100.00'),
            valid_from=self.valid_from,
            valid_to=self.valid_to,
            max_uses=5,
            is_active=True,
            assigned_to_all=True,
            created_by=self.admin_user
        )
        
        # Test valid scenario
        is_valid, message = coupon.is_valid(self.regular_user, Decimal('200.00'))
        self.assertTrue(is_valid)
        self.assertEqual(message, "Valid coupon")
        
        # Test insufficient cart amount
        is_valid, message = coupon.is_valid(self.regular_user, Decimal('50.00'))
        self.assertFalse(is_valid)
        self.assertIn("Minimum order amount not met", message)
    
    def test_is_valid_method_inactive_coupon(self):
        """Test is_valid with inactive coupon"""
        coupon = Coupon.objects.create(
            code='INACTIVE',
            coupon_type='percentage',
            discount_value=Decimal('10.00'),
            valid_from=self.valid_from,
            valid_to=self.valid_to,
            is_active=False,  # Inactive
            assigned_to_all=True,
            created_by=self.admin_user
        )
        
        is_valid, message = coupon.is_valid(self.regular_user)
        self.assertFalse(is_valid)
        self.assertEqual(message, "Coupon is not active")
    
    def test_is_valid_method_expired_coupon(self):
        """Test is_valid with expired coupon"""
        past_date = timezone.now() - timedelta(days=10)
        expired_date = timezone.now() - timedelta(days=5)
        
        coupon = Coupon.objects.create(
            code='EXPIRED',
            coupon_type='percentage',
            discount_value=Decimal('10.00'),
            valid_from=past_date,
            valid_to=expired_date,  # Expired
            is_active=True,
            assigned_to_all=True,
            created_by=self.admin_user
        )
        
        is_valid, message = coupon.is_valid(self.regular_user)
        self.assertFalse(is_valid)
        self.assertEqual(message, "Coupon has expired")
    
    def test_is_valid_method_user_assignment(self):
        """Test is_valid with user-specific assignment"""
        coupon = Coupon.objects.create(
            code='USERSPECIFIC',
            coupon_type='percentage',
            discount_value=Decimal('10.00'),
            valid_from=self.valid_from,
            valid_to=self.valid_to,
            is_active=True,
            assigned_to_all=False,  # Not for all
            created_by=self.admin_user
        )
        coupon.assigned_users.add(self.regular_user)
        
        # Test assigned user
        is_valid, message = coupon.is_valid(self.regular_user)
        self.assertTrue(is_valid)
        
        # Test unassigned user
        other_user = User.objects.create_user(
            email='other@test.com',
            password='testpass123',
            full_name='Other User',
            role='user'
        )
        is_valid, message = coupon.is_valid(other_user)
        self.assertFalse(is_valid)
        self.assertEqual(message, "Coupon not assigned to this user")
    
    def test_apply_discount_percentage(self):
        """Test discount calculation for percentage coupons"""
        coupon = Coupon.objects.create(
            code='PERCENT20',
            coupon_type='percentage',
            discount_value=Decimal('20.00'),
            max_discount=Decimal('100.00'),
            valid_from=self.valid_from,
            valid_to=self.valid_to,
            created_by=self.admin_user
        )
        
        # Test normal percentage discount
        discount = coupon.apply_discount(Decimal('200.00'))
        self.assertEqual(discount, Decimal('40.00'))  # 20% of 200
        
        # Test max discount cap
        discount = coupon.apply_discount(Decimal('1000.00'))
        self.assertEqual(discount, Decimal('100.00'))  # Capped at max_discount
    
    def test_apply_discount_fixed_amount(self):
        """Test discount calculation for fixed amount coupons"""
        coupon = Coupon.objects.create(
            code='FIXED50',
            coupon_type='fixed_amount',
            discount_value=Decimal('50.00'),
            valid_from=self.valid_from,
            valid_to=self.valid_to,
            created_by=self.admin_user
        )
        
        # Test normal fixed discount
        discount = coupon.apply_discount(Decimal('200.00'))
        self.assertEqual(discount, Decimal('50.00'))
        
        # Test discount doesn't exceed cart amount
        discount = coupon.apply_discount(Decimal('30.00'))
        self.assertEqual(discount, Decimal('30.00'))  # Limited to cart amount
    
    def test_record_usage(self):
        """Test recording coupon usage"""
        coupon = Coupon.objects.create(
            code='USAGE_TEST',
            coupon_type='fixed_amount',
            discount_value=Decimal('25.00'),
            valid_from=self.valid_from,
            valid_to=self.valid_to,
            max_uses=3,
            is_active=True,
            assigned_to_all=True,
            created_by=self.admin_user
        )
        
        # Record first usage
        coupon.record_usage(
            user=self.regular_user,
            order_id='ORDER001',
            discount_amount=Decimal('25.00')
        )
        
        coupon.refresh_from_db()
        self.assertEqual(coupon.used_count, 1)
        self.assertEqual(CouponUsage.objects.filter(coupon=coupon).count(), 1)
        
        # Test usage limit
        coupon.used_count = 3
        coupon.save()
        
        with self.assertRaises(ValidationError):
            coupon.record_usage(
                user=self.regular_user,
                order_id='ORDER002',
                discount_amount=Decimal('25.00')
            )


class CouponUsageModelTest(TestCase):
    """Test CouponUsage model functionality"""
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            full_name='Admin User',
            role='admin'
        )
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            password='testpass123',
            full_name='Regular User',
            role='user'
        )
        
        self.coupon = Coupon.objects.create(
            code='USAGE_MODEL_TEST',
            coupon_type='fixed_amount',
            discount_value=Decimal('30.00'),
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            max_uses=10,
            is_active=True,
            assigned_to_all=True,
            created_by=self.admin_user
        )
    
    def test_coupon_usage_creation(self):
        """Test creating a coupon usage record"""
        usage = CouponUsage.objects.create(
            coupon=self.coupon,
            user=self.regular_user,
            order_id='ORDER123',
            discount_amount=Decimal('30.00')
        )
        
        self.assertEqual(usage.coupon, self.coupon)
        self.assertEqual(usage.user, self.regular_user)
        self.assertEqual(usage.order_id, 'ORDER123')
        self.assertEqual(usage.discount_amount, Decimal('30.00'))
        self.assertIsNotNone(usage.applied_at)
    
    def test_coupon_usage_str_representation(self):
        """Test string representation of coupon usage"""
        usage = CouponUsage.objects.create(
            coupon=self.coupon,
            user=self.regular_user,
            order_id='ORDER123',
            discount_amount=Decimal('30.00')
        )
        
        expected = f"{self.regular_user.email} used {self.coupon.code} on {usage.applied_at.date()}"
        self.assertEqual(str(usage), expected)
    
    def test_unique_constraint(self):
        """Test unique constraint on coupon and order_id"""
        # Create first usage
        CouponUsage.objects.create(
            coupon=self.coupon,
            user=self.regular_user,
            order_id='ORDER123',
            discount_amount=Decimal('30.00')
        )
        
        # Try to create duplicate - should raise IntegrityError
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            CouponUsage.objects.create(
                coupon=self.coupon,
                user=self.regular_user,
                order_id='ORDER123',  # Same order_id
                discount_amount=Decimal('25.00')
            )