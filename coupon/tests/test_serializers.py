# coupon/tests/test_serializers.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from rest_framework.exceptions import ValidationError

from coupon.models import Coupon, CouponUsage
from coupon.serializers import (
    AdminCouponSerializer,
    UserCouponSerializer,
    CouponApplySerializer,
    CouponValidationSerializer,
    BulkCouponCreateSerializer
)

User = get_user_model()


class AdminCouponSerializerTest(TestCase):
    """Test AdminCouponSerializer functionality"""
    
    def setUp(self):
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
        
        self.valid_from = timezone.now()
        self.valid_to = self.valid_from + timedelta(days=30)
    
    def test_admin_serializer_create_valid_coupon(self):
        """Test creating coupon with valid data"""
        data = {
            'code': 'TESTCOUPON',
            'description': 'Test coupon',
            'coupon_type': 'percentage',
            'discount_value': '15.00',
            'max_discount': '100.00',
            'min_order_amount': '200.00',
            'applicable_to': 'all',
            'valid_from': self.valid_from.isoformat(),
            'valid_to': self.valid_to.isoformat(),
            'max_uses': 50,
            'is_active': True,
            'assigned_to_all': True
        }
        
        context = {'request': type('MockRequest', (), {'user': self.admin_user})()}
        serializer = AdminCouponSerializer(data=data, context=context)
        
        self.assertTrue(serializer.is_valid())
        coupon = serializer.save()
        
        self.assertEqual(coupon.code, 'TESTCOUPON')
        self.assertEqual(coupon.created_by, self.admin_user)
        self.assertEqual(coupon.discount_value, Decimal('15.00'))
    
    def test_admin_serializer_code_validation(self):
        """Test coupon code validation"""
        # Test code too short
        data = {
            'code': 'AB',  # Too short
            'coupon_type': 'percentage',
            'discount_value': '10.00',
            'valid_from': self.valid_from.isoformat(),
            'valid_to': self.valid_to.isoformat()
        }
        
        serializer = AdminCouponSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('code', serializer.errors)
    
    def test_admin_serializer_percentage_validation(self):
        """Test percentage discount validation"""
        data = {
            'code': 'INVALID',
            'coupon_type': 'percentage',
            'discount_value': '150.00',  # Invalid: > 100%
            'valid_from': self.valid_from.isoformat(),
            'valid_to': self.valid_to.isoformat()
        }
        
        serializer = AdminCouponSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('discount_value', serializer.errors)
    
    def test_admin_serializer_date_validation(self):
        """Test date range validation"""
        data = {
            'code': 'DATETEST',
            'coupon_type': 'percentage',
            'discount_value': '10.00',
            'valid_from': self.valid_to.isoformat(),  # Invalid: from > to
            'valid_to': self.valid_from.isoformat()
        }
        
        serializer = AdminCouponSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('valid_to', serializer.errors)
    
    def test_admin_serializer_max_discount_validation(self):
        """Test max_discount validation"""
        # Test max_discount with fixed_amount (should be removed)
        data = {
            'code': 'FIXED_TEST',
            'coupon_type': 'fixed_amount',
            'discount_value': '50.00',
            'max_discount': '100.00',  # Should be removed
            'valid_from': self.valid_from.isoformat(),
            'valid_to': self.valid_to.isoformat()
        }
        
        serializer = AdminCouponSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        # max_discount should be removed during validation
        self.assertNotIn('max_discount', serializer.validated_data)
    
    def test_admin_serializer_user_assignment(self):
        """Test user assignment functionality"""
        data = {
            'code': 'USERTEST',
            'coupon_type': 'percentage',
            'discount_value': '10.00',
            'valid_from': self.valid_from.isoformat(),
            'valid_to': self.valid_to.isoformat(),
            'assigned_to_all': False,
            'assigned_user_ids': [self.regular_user.id]
        }
        
        context = {'request': type('MockRequest', (), {'user': self.admin_user})()}
        serializer = AdminCouponSerializer(data=data, context=context)
        
        self.assertTrue(serializer.is_valid())
        coupon = serializer.save()
        
        self.assertIn(self.regular_user, coupon.assigned_users.all())
    
    def test_admin_serializer_update(self):
        """Test updating existing coupon"""
        coupon = Coupon.objects.create(
            code='UPDATE_TEST',
            coupon_type='percentage',
            discount_value=Decimal('10.00'),
            valid_from=self.valid_from,
            valid_to=self.valid_to,
            created_by=self.admin_user
        )
        
        data = {
            'description': 'Updated description',
            'discount_value': '20.00',
            'is_active': False
        }
        
        context = {'request': type('MockRequest', (), {'user': self.admin_user})()}
        serializer = AdminCouponSerializer(coupon, data=data, partial=True, context=context)
        
        self.assertTrue(serializer.is_valid())
        updated_coupon = serializer.save()
        
        self.assertEqual(updated_coupon.description, 'Updated description')
        self.assertEqual(updated_coupon.discount_value, Decimal('20.00'))
        self.assertFalse(updated_coupon.is_active)


class UserCouponSerializerTest(TestCase):
    """Test UserCouponSerializer functionality"""
    
    def setUp(self):
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
            code='USERTEST',
            description='Test coupon for users',
            coupon_type='percentage',
            discount_value=Decimal('15.00'),
            max_discount=Decimal('100.00'),
            min_order_amount=Decimal('200.00'),
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            max_uses=50,
            is_active=True,
            assigned_to_all=True,
            created_by=self.admin_user
        )
    
    def test_user_serializer_read_only(self):
        """Test that user serializer is read-only"""
        # All fields should be read-only
        serializer = UserCouponSerializer()
        meta = serializer.Meta
        
        self.assertEqual(meta.read_only_fields, '__all__')
    
    def test_user_serializer_discount_display(self):
        """Test discount display formatting"""
        context = {'request': type('MockRequest', (), {'user': self.regular_user})()}
        serializer = UserCouponSerializer(self.coupon, context=context)
        
        discount_display = serializer.data['discount_display']
        expected = "15.0% off (max ₹100.00)"
        self.assertEqual(discount_display, expected)
    
    def test_user_serializer_fixed_amount_display(self):
        """Test fixed amount discount display"""
        fixed_coupon = Coupon.objects.create(
            code='FIXED50',
            coupon_type='fixed_amount',
            discount_value=Decimal('50.00'),
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            created_by=self.admin_user
        )
        
        context = {'request': type('MockRequest', (), {'user': self.regular_user})()}
        serializer = UserCouponSerializer(fixed_coupon, context=context)
        
        discount_display = serializer.data['discount_display']
        self.assertEqual(discount_display, "₹50.00 off")
    
    def test_user_serializer_validity_status(self):
        """Test validity status calculation"""
        context = {'request': type('MockRequest', (), {'user': self.regular_user})()}
        serializer = UserCouponSerializer(self.coupon, context=context)
        
        validity_status = serializer.data['validity_status']
        
        self.assertIn('is_valid', validity_status)
        self.assertIn('message', validity_status)
        self.assertIn('is_active', validity_status)
        self.assertIn('is_expired', validity_status)
        self.assertIn('days_until_expiry', validity_status)
    
    def test_user_serializer_can_use(self):
        """Test can_use field calculation"""
        context = {'request': type('MockRequest', (), {'user': self.regular_user})()}
        serializer = UserCouponSerializer(self.coupon, context=context)
        
        can_use = serializer.data['can_use']
        self.assertTrue(can_use)
    
    def test_user_serializer_usage_info(self):
        """Test usage information"""
        context = {'request': type('MockRequest', (), {'user': self.regular_user})()}
        serializer = UserCouponSerializer(self.coupon, context=context)
        
        usage_info = serializer.data['usage_info']
        
        self.assertIn('remaining_uses', usage_info)
        self.assertIn('is_unlimited', usage_info)
        self.assertIn('usage_percentage', usage_info)
        self.assertEqual(usage_info['remaining_uses'], 50)


class CouponApplySerializerTest(TestCase):
    """Test CouponApplySerializer functionality"""
    
    def setUp(self):
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
            code='APPLY_TEST',
            coupon_type='percentage',
            discount_value=Decimal('20.00'),
            min_order_amount=Decimal('100.00'),
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            max_uses=10,
            is_active=True,
            assigned_to_all=True,
            created_by=self.admin_user
        )
    
    def test_apply_serializer_valid_data(self):
        """Test serializer with valid data"""
        data = {
            'code': 'APPLY_TEST',
            'cart_total': '200.00'
        }
        
        context = {'request': type('MockRequest', (), {'user': self.regular_user})()}
        serializer = CouponApplySerializer(data=data, context=context)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['coupon'], self.coupon)
        self.assertEqual(serializer.validated_data['cart_total'], Decimal('200.00'))
    
    def test_apply_serializer_code_normalization(self):
        """Test coupon code normalization"""
        data = {
            'code': '  apply_test  ',  # Lowercase with spaces
            'cart_total': '200.00'
        }
        
        context = {'request': type('MockRequest', (), {'user': self.regular_user})()}
        serializer = CouponApplySerializer(data=data, context=context)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['code'], 'APPLY_TEST')
    
    def test_apply_serializer_invalid_coupon(self):
        """Test serializer with invalid coupon code"""
        data = {
            'code': 'INVALID',
            'cart_total': '200.00'
        }
        
        context = {'request': type('MockRequest', (), {'user': self.regular_user})()}
        serializer = CouponApplySerializer(data=data, context=context)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('code', serializer.errors)
    
    def test_apply_serializer_insufficient_cart_amount(self):
        """Test serializer with insufficient cart amount"""
        data = {
            'code': 'APPLY_TEST',
            'cart_total': '50.00'  # Below minimum
        }
        
        context = {'request': type('MockRequest', (), {'user': self.regular_user})()}
        serializer = CouponApplySerializer(data=data, context=context)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)


class CouponValidationSerializerTest(TestCase):
    """Test CouponValidationSerializer functionality"""
    
    def setUp(self):
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
            code='VALIDATE_TEST',
            coupon_type='fixed_amount',
            discount_value=Decimal('25.00'),
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            max_uses=5,
            is_active=True,
            assigned_to_all=True,
            created_by=self.admin_user
        )
    
    def test_validation_serializer_valid_coupon(self):
        """Test validation serializer with valid coupon"""
        data = {
            'code': 'VALIDATE_TEST',
            'cart_total': '100.00'
        }
        
        context = {'request': type('MockRequest', (), {'user': self.regular_user})()}
        serializer = CouponValidationSerializer(data=data, context=context)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['coupon'], self.coupon)
        self.assertTrue(serializer.validated_data['is_valid'])
        self.assertEqual(serializer.validated_data['message'], 'Valid coupon')
    
    def test_validation_serializer_nonexistent_coupon(self):
        """Test validation serializer with nonexistent coupon"""
        data = {
            'code': 'NONEXISTENT',
            'cart_total': '100.00'
        }
        
        context = {'request': type('MockRequest', (), {'user': self.regular_user})()}
        serializer = CouponValidationSerializer(data=data, context=context)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('code', serializer.errors)


class BulkCouponCreateSerializerTest(TestCase):
    """Test BulkCouponCreateSerializer functionality"""
    
    def setUp(self):
        self.valid_from = timezone.now()
        self.valid_to = self.valid_from + timedelta(days=30)
    
    def test_bulk_serializer_valid_data(self):
        """Test bulk create serializer with valid data"""
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
        
        serializer = BulkCouponCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_bulk_serializer_invalid_quantity(self):
        """Test bulk serializer with invalid quantity"""
        data = {
            'base_code': 'BULK',
            'quantity': 0,  # Invalid
            'coupon_type': 'percentage',
            'discount_value': '10.00',
            'valid_from': self.valid_from.isoformat(),
            'valid_to': self.valid_to.isoformat()
        }
        
        serializer = BulkCouponCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('quantity', serializer.errors)
    
    def test_bulk_serializer_percentage_validation(self):
        """Test bulk serializer percentage validation"""
        data = {
            'base_code': 'BULK',
            'quantity': 5,
            'coupon_type': 'percentage',
            'discount_value': '150.00',  # Invalid
            'valid_from': self.valid_from.isoformat(),
            'valid_to': self.valid_to.isoformat()
        }
        
        serializer = BulkCouponCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('discount_value', serializer.errors)