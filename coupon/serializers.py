# coupons/serializers.py
from rest_framework import serializers
from .models import Coupon, CouponUsage
from accounts.models import User
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from decimal import Decimal
from django.db import transaction


class CouponUserSerializer(serializers.ModelSerializer):
    """Serializer for user information in coupon assignments"""
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'role']
        read_only_fields = ['id', 'email', 'full_name', 'role']


# ============ ADMIN SERIALIZERS ============

class AdminCouponSerializer(serializers.ModelSerializer):
    """Full admin serializer with all coupon management capabilities"""
    assigned_users = CouponUserSerializer(many=True, read_only=True)
    assigned_user_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.filter(role='user'),  # Only regular users can be assigned
        write_only=True,
        source='assigned_users',
        required=False,
        help_text="List of user IDs to assign this coupon to"
    )
    created_by_info = CouponUserSerializer(source='created_by', read_only=True)
    usage_stats = serializers.SerializerMethodField()
    remaining_uses = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'description', 'coupon_type', 'discount_value',
            'max_discount', 'min_order_amount', 'applicable_to', 'valid_from',
            'valid_to', 'max_uses', 'used_count', 'is_active', 'assigned_to_all',
            'assigned_users', 'assigned_user_ids', 'created_at', 'updated_at',
            'created_by_info', 'usage_stats', 'remaining_uses', 'is_expired'
        ]
        read_only_fields = ['id', 'used_count', 'created_at', 'updated_at', 'created_by']

    def get_usage_stats(self, obj):
        """Get detailed usage statistics"""
        return {
            'total_uses': obj.used_count,
            'max_uses': obj.max_uses,
            'usage_percentage': round((obj.used_count / obj.max_uses) * 100, 2) if obj.max_uses > 0 else 0,
            'remaining_uses': max(0, obj.max_uses - obj.used_count)
        }
    
    def get_remaining_uses(self, obj):
        """Get remaining usage count"""
        return max(0, obj.max_uses - obj.used_count)
    
    def get_is_expired(self, obj):
        """Check if coupon is expired"""
        now = timezone.now()
        return now > obj.valid_to

    def validate_code(self, value):
        """Validate coupon code uniqueness and format"""
        value = value.upper().strip()
        if len(value) < 3:
            raise ValidationError("Coupon code must be at least 3 characters long")
        if len(value) > 50:
            raise ValidationError("Coupon code cannot exceed 50 characters")
        
        # Check for update vs create
        if self.instance:
            if Coupon.objects.exclude(pk=self.instance.pk).filter(code=value).exists():
                raise ValidationError("A coupon with this code already exists")
        else:
            if Coupon.objects.filter(code=value).exists():
                raise ValidationError("A coupon with this code already exists")
        
        return value

    def validate_discount_value(self, value):
        """Validate discount value based on type"""
        if value <= 0:
            raise ValidationError("Discount value must be greater than 0")
        
        # For percentage type, check during full validation
        return value

    def validate_max_discount(self, value):
        """Validate max discount amount"""
        if value is not None and value < 0:
            raise ValidationError("Max discount cannot be negative")
        return value

    def validate_min_order_amount(self, value):
        """Validate minimum order amount"""
        if value < 0:
            raise ValidationError("Minimum order amount cannot be negative")
        return value

    def validate_max_uses(self, value):
        """Validate max uses"""
        if value <= 0:
            raise ValidationError("Max uses must be greater than 0")
        if value > 10000:
            raise ValidationError("Max uses cannot exceed 10,000")
        return value

    def validate(self, data):
        """Cross-field validation"""
        errors = {}
        
        # Validate coupon type and discount value relationship
        coupon_type = data.get('coupon_type', getattr(self.instance, 'coupon_type', None))
        discount_value = data.get('discount_value', getattr(self.instance, 'discount_value', None))
        
        if coupon_type == 'percentage' and discount_value and discount_value > 100:
            errors['discount_value'] = "Percentage discount cannot exceed 100%"
        
        # Validate date range
        valid_from = data.get('valid_from', getattr(self.instance, 'valid_from', None))
        valid_to = data.get('valid_to', getattr(self.instance, 'valid_to', None))
        
        if valid_from and valid_to and valid_to <= valid_from:
            errors['valid_to'] = "Valid to date must be after valid from date"
        
        # Validate max_discount only for percentage coupons
        max_discount = data.get('max_discount')
        if coupon_type == 'fixed_amount' and max_discount is not None:
            errors['max_discount'] = "Max discount is only applicable to percentage coupons"
        
        # For percentage coupons, ensure max_discount is reasonable (optional validation)
        # This validation is removed as it's too restrictive for enterprise use cases
        
        # Validate assignment logic
        assigned_to_all = data.get('assigned_to_all', getattr(self.instance, 'assigned_to_all', True))
        assigned_users = data.get('assigned_users', [])
        
        if not assigned_to_all and not assigned_users and not getattr(self.instance, 'assigned_users', None):
            errors['assigned_users'] = "Either assign to all users or specify specific users"
        
        if errors:
            raise ValidationError(errors)
        
        # Clean max_discount for fixed_amount coupons
        if coupon_type == 'fixed_amount':
            data.pop('max_discount', None)
        
        return data

    def create(self, validated_data):
        """Create coupon with proper user assignment"""
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        
        with transaction.atomic():
            coupon = super().create(validated_data)
            # Log creation in audit if available
            try:
                from accounts.models import AuditLog
                AuditLog.log_action(
                    user=request.user,
                    action='coupon_create',
                    resource=f'Coupon {coupon.code}',
                    details={'coupon_id': coupon.id, 'code': coupon.code}
                )
            except Exception as e:
                # Skip audit logging if it fails
                pass
        return coupon

    def update(self, instance, validated_data):
        """Update coupon with audit trail"""
        request = self.context.get('request')
        old_data = {
            'code': instance.code,
            'discount_value': instance.discount_value,
            'is_active': instance.is_active
        }
        
        with transaction.atomic():
            coupon = super().update(instance, validated_data)
            # Log update in audit if available
            try:
                from accounts.models import AuditLog
                AuditLog.log_action(
                    user=request.user,
                    action='coupon_update',
                    resource=f'Coupon {coupon.code}',
                    details={'coupon_id': coupon.id, 'old_data': str(old_data)}
                )
            except Exception as e:
                # Skip audit logging if it fails
                pass
        return coupon


# ============ USER SERIALIZERS ============

class UserCouponSerializer(serializers.ModelSerializer):
    """Limited serializer for regular users to view their assigned coupons"""
    discount_display = serializers.SerializerMethodField()
    validity_status = serializers.SerializerMethodField()
    can_use = serializers.SerializerMethodField()
    usage_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'description', 'coupon_type', 'discount_value',
            'max_discount', 'min_order_amount', 'applicable_to', 'valid_from',
            'valid_to', 'discount_display', 'validity_status', 'can_use',
            'usage_info'
        ]
        read_only_fields = ('id', 'code', 'description', 'coupon_type', 'discount_value',
                         'max_discount', 'min_order_amount', 'applicable_to', 'valid_from',
                         'valid_to', 'discount_display', 'validity_status', 'can_use',
                         'usage_info')  # Users can only view, not modify
    
    def get_discount_display(self, obj):
        """Human-readable discount description"""
        if obj.coupon_type == 'percentage':
            base = f"{obj.discount_value}% off"
            if obj.max_discount:
                base += f" (max ₹{obj.max_discount})"
            return base
        else:
            return f"₹{obj.discount_value} off"
    
    def get_validity_status(self, obj):
        """Check validity status for current user"""
        request = self.context.get('request')
        user = request.user if request else None
        is_valid, message = obj.is_valid(user)
        
        now = timezone.now()
        return {
            'is_valid': is_valid,
            'message': message,
            'is_active': obj.is_active,
            'is_expired': now > obj.valid_to,
            'is_future': now < obj.valid_from,
            'days_until_expiry': (obj.valid_to - now).days if now < obj.valid_to else 0
        }
    
    def get_can_use(self, obj):
        """Check if current user can use this coupon"""
        request = self.context.get('request')
        if not request or not request.user:
            return False
        
        is_valid, _ = obj.is_valid(request.user)
        return is_valid
    
    def get_usage_info(self, obj):
        """Get usage information relevant to user"""
        remaining = max(0, obj.max_uses - obj.used_count)
        return {
            'remaining_uses': remaining,
            'is_unlimited': obj.max_uses >= 10000,  # Treat high numbers as unlimited
            'usage_percentage': round((obj.used_count / obj.max_uses) * 100, 1) if obj.max_uses > 0 else 0
        }


# ============ USAGE SERIALIZERS ============

class AdminCouponUsageSerializer(serializers.ModelSerializer):
    """Admin view of coupon usage with full details"""
    coupon_info = serializers.SerializerMethodField()
    user_info = CouponUserSerializer(source='user', read_only=True)
    
    class Meta:
        model = CouponUsage
        fields = [
            'id', 'coupon', 'coupon_info', 'user', 'user_info',
            'order_id', 'discount_amount', 'applied_at'
        ]
        read_only_fields = ['id', 'applied_at']
    
    def get_coupon_info(self, obj):
        """Get coupon details for usage record"""
        return {
            'code': obj.coupon.code,
            'type': obj.coupon.get_coupon_type_display(),
            'discount_value': obj.coupon.discount_value,
            'description': obj.coupon.description
        }


class UserCouponUsageSerializer(serializers.ModelSerializer):
    """User view of their own coupon usage"""
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)
    coupon_description = serializers.CharField(source='coupon.description', read_only=True)
    
    class Meta:
        model = CouponUsage
        fields = [
            'id', 'coupon_code', 'coupon_description', 'order_id', 
            'discount_amount', 'applied_at'
        ]
        read_only_fields = ('id', 'coupon_code', 'coupon_description', 'order_id', 
                          'discount_amount', 'applied_at')


# ============ APPLICATION SERIALIZERS ============

class CouponApplySerializer(serializers.Serializer):
    """Serializer for applying coupons to cart"""
    code = serializers.CharField(
        max_length=50,
        help_text="Coupon code to apply"
    )
    cart_total = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        min_value=Decimal('0.01'),
        help_text="Total cart amount before discount"
    )
    applicable_products = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="List of product categories/types in cart for validation"
    )

    def validate_code(self, value):
        """Validate and normalize coupon code"""
        return value.upper().strip()

    def validate(self, data):
        """Validate coupon application"""
        code = data['code']
        cart_total = data['cart_total']
        applicable_products = data.get('applicable_products', [])
        
        try:
            coupon = Coupon.objects.get(code=code, is_active=True)
        except Coupon.DoesNotExist:
            raise ValidationError({
                'code': "Invalid or inactive coupon code"
            })

        request = self.context.get('request')
        user = request.user if request else None

        # Basic validity check
        is_valid, message = coupon.is_valid(user, cart_total)
        if not is_valid:
            raise ValidationError({
                'non_field_errors': message
            })
        
        # Check product applicability
        if coupon.applicable_to != 'all' and applicable_products:
            applicable_map = {
                'pathology': 'pathology',
                'doctor': 'doctor',
                'medical': 'medicine'  # Assuming medical = medicine products
            }
            required_category = applicable_map.get(coupon.applicable_to)
            if required_category and required_category not in applicable_products:
                raise ValidationError({
                    'non_field_errors': f"This coupon is only valid for {coupon.get_applicable_to_display().lower()} products"
                })

        data['coupon'] = coupon
        return data


class CouponValidationSerializer(serializers.Serializer):
    """Serializer for validating coupon without applying"""
    code = serializers.CharField(max_length=50)
    cart_total = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        min_value=0,
        required=False
    )
    
    def validate_code(self, value):
        return value.upper().strip()

    def validate(self, data):
        code = data['code']
        
        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            raise ValidationError({
                'code': "Coupon not found"
            })
        
        request = self.context.get('request')
        user = request.user if request else None
        cart_total = data.get('cart_total', 0)
        
        is_valid, message = coupon.is_valid(user, cart_total)
        
        data['coupon'] = coupon
        data['is_valid'] = is_valid
        data['message'] = message
        
        return data


# ============ BULK OPERATIONS SERIALIZERS ============

class BulkCouponCreateSerializer(serializers.Serializer):
    """Serializer for creating multiple coupons at once"""
    base_code = serializers.CharField(
        max_length=40,
        help_text="Base code for coupons (numbers will be appended)"
    )
    quantity = serializers.IntegerField(
        min_value=1,
        max_value=100,
        help_text="Number of coupons to create"
    )
    coupon_type = serializers.ChoiceField(choices=Coupon.COUPON_TYPES)
    discount_value = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    max_discount = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False, 
        allow_null=True
    )
    min_order_amount = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0
    )
    applicable_to = serializers.ChoiceField(
        choices=Coupon.APPLICABLE_TO,
        default='all'
    )
    valid_from = serializers.DateTimeField()
    valid_to = serializers.DateTimeField()
    max_uses = serializers.IntegerField(min_value=1, default=1)
    assigned_to_all = serializers.BooleanField(default=True)

    def validate(self, data):
        # Same validation as AdminCouponSerializer
        if data['coupon_type'] == 'percentage' and data['discount_value'] > 100:
            raise ValidationError("Percentage discount cannot exceed 100%")
        
        if data['valid_to'] <= data['valid_from']:
            raise ValidationError("Valid to date must be after valid from date")
        
        if data['coupon_type'] == 'fixed_amount':
            data.pop('max_discount', None)
        
        return data


# ============ BACKWARD COMPATIBILITY ============
# Aliases for existing imports in other apps
CouponSerializer = AdminCouponSerializer
CouponUsageSerializer = AdminCouponUsageSerializer