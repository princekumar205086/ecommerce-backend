# coupons/serializers.py
from rest_framework import serializers
from .models import Coupon, CouponUsage
from accounts.models import User
from django.utils import timezone
from rest_framework.exceptions import ValidationError


class CouponUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name']
        read_only_fields = ['id', 'email', 'full_name']


class CouponSerializer(serializers.ModelSerializer):
    assigned_users = CouponUserSerializer(many=True, read_only=True)
    assigned_user_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        write_only=True,
        source='assigned_users',
        required=False
    )
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'description', 'coupon_type', 'discount_value',
            'max_discount', 'min_order_amount', 'applicable_to', 'valid_from',
            'valid_to', 'max_uses', 'used_count', 'is_active', 'assigned_to_all',
            'assigned_users', 'assigned_user_ids', 'created_at', 'updated_at',
            'is_valid'
        ]
        read_only_fields = ['id', 'used_count', 'created_at', 'updated_at', 'created_by']

    def get_is_valid(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        is_valid, message = obj.is_valid(user)
        return {
            'valid': is_valid,
            'message': message
        }

    def validate(self, data):
        if data.get('coupon_type') == 'percentage' and data.get('discount_value', 0) > 100:
            raise ValidationError("Percentage discount cannot exceed 100%")

        valid_from = data.get('valid_from')
        valid_to = data.get('valid_to')

        if valid_from and valid_to and valid_to <= valid_from:
            raise ValidationError("Valid to date must be after valid from date")

        if data.get('coupon_type') == 'fixed_amount' and 'max_discount' in data:
            data.pop('max_discount')

        return data

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class CouponUsageSerializer(serializers.ModelSerializer):
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = CouponUsage
        fields = [
            'id', 'coupon', 'coupon_code', 'user', 'user_email',
            'order_id', 'discount_amount', 'applied_at'
        ]
        read_only_fields = ['id', 'applied_at']


class CouponApplySerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)
    cart_total = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)

    def validate(self, data):
        try:
            coupon = Coupon.objects.get(code=data['code'])
        except Coupon.DoesNotExist:
            raise ValidationError("Invalid coupon code")

        request = self.context.get('request')
        user = request.user if request else None

        is_valid, message = coupon.is_valid(user, data['cart_total'])
        if not is_valid:
            raise ValidationError(message)

        data['coupon'] = coupon
        return data