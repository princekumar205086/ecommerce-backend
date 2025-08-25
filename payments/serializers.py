from rest_framework import serializers

from orders.models import Order
from .models import Payment
from orders.serializers import OrderSerializer


class PaymentSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'razorpay_payment_id', 'razorpay_order_id',
            'amount', 'currency', 'status', 'created_at', 'updated_at',
            'webhook_verified'
        ]
        read_only_fields = fields


class CreatePaymentFromCartSerializer(serializers.Serializer):
    """Create payment directly from cart - NEW FLOW with COD support"""
    cart_id = serializers.IntegerField(required=False)  # Make optional
    shipping_address = serializers.JSONField(required=False)
    payment_method = serializers.ChoiceField(
        choices=[
            ('razorpay', 'Razorpay (Online)'), 
            ('cod', 'Cash on Delivery'),
            ('pathlog_wallet', 'Pathlog Wallet')
        ],
        default='razorpay'
    )
    currency = serializers.CharField(max_length=3, default='INR')
    coupon_code = serializers.CharField(max_length=50, required=False, allow_null=True)
    cod_notes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    save_address = serializers.BooleanField(default=True, help_text="Save address to user profile for future use")

    def validate_cart_id(self, value):
        """Validate that cart exists and belongs to user"""
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context missing")
        
        from cart.models import Cart
        try:
            cart = Cart.objects.get(id=value, user=request.user)
            if not cart.items.exists():
                raise serializers.ValidationError("Cart is empty")
            return value
        except Cart.DoesNotExist:
            raise serializers.ValidationError("Cart not found or doesn't belong to you")
    
    def validate(self, data):
        """Validate and auto-fill address data"""
        request = self.context.get('request')
        user = request.user if request else None
        
        # If no shipping address provided, try to use user's saved address
        if not data.get('shipping_address') and user and user.has_address:
            data['shipping_address'] = {
                'full_name': user.full_name,
                'address_line_1': user.address_line_1,
                'address_line_2': user.address_line_2,
                'city': user.city,
                'state': user.state,
                'postal_code': user.postal_code,
                'country': user.country,
                'phone': user.contact
            }
        elif not data.get('shipping_address'):
            raise serializers.ValidationError({
                'shipping_address': 'Shipping address is required. Please provide address or save one to your profile.'
            })
        
        # Validate address has required fields
        address = data['shipping_address']
        required_fields = ['full_name', 'address_line_1', 'city', 'state', 'postal_code', 'country']
        missing_fields = [field for field in required_fields if not address.get(field)]
        if missing_fields:
            raise serializers.ValidationError({
                'shipping_address': f'Missing required fields: {", ".join(missing_fields)}'
            })
        
        # For simplicity, billing address = shipping address (as requested)
        data['billing_address'] = data['shipping_address'].copy()
        
        return data


class CreatePaymentSerializer(serializers.Serializer):
    """Create payment from existing order - LEGACY FLOW"""
    order_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(default='INR')

    def validate_order_id(self, value):
        if not Order.objects.filter(id=value).exists():
            raise serializers.ValidationError("Order does not exist")
        return value


class VerifyPaymentSerializer(serializers.Serializer):
    razorpay_payment_id = serializers.CharField(required=False)
    razorpay_order_id = serializers.CharField()
    razorpay_signature = serializers.CharField(required=False)


class ConfirmRazorpaySerializer(serializers.Serializer):
    """Confirm Razorpay payment with complete data"""
    payment_id = serializers.IntegerField()
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()
    
    def validate_payment_id(self, value):
        """Validate payment exists and belongs to user"""
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context missing")
        
        try:
            payment = Payment.objects.get(id=value, user=request.user)
            if payment.payment_method != 'razorpay':
                raise serializers.ValidationError("Payment is not Razorpay")
            return value
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Payment not found or doesn't belong to you")


class ConfirmCODSerializer(serializers.Serializer):
    """Confirm COD payment"""
    payment_id = serializers.IntegerField()
    cod_notes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_payment_id(self, value):
        """Validate payment exists and is COD"""
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context missing")
        
        try:
            payment = Payment.objects.get(id=value, user=request.user)
            if payment.payment_method != 'cod':
                raise serializers.ValidationError("Payment is not COD")
            if payment.status == 'cod_confirmed':
                raise serializers.ValidationError("COD payment already confirmed")
            return value
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Payment not found or doesn't belong to you")


class PathlogWalletVerifySerializer(serializers.Serializer):
    """Serializer for Pathlog Wallet mobile number verification"""
    payment_id = serializers.IntegerField()
    mobile_number = serializers.CharField(max_length=15)
    
    def validate_mobile_number(self, value):
        # Remove any non-digit characters and validate format
        import re
        cleaned = re.sub(r'\D', '', value)
        if len(cleaned) != 10:
            raise serializers.ValidationError("Mobile number must be 10 digits")
        return cleaned
    
    def validate_payment_id(self, value):
        user = self.context['request'].user
        try:
            payment = Payment.objects.get(id=value, user=user)
            if payment.payment_method != 'pathlog_wallet':
                raise serializers.ValidationError("Not a Pathlog Wallet payment")
            return value
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Payment not found or doesn't belong to you")


class PathlogWalletOTPSerializer(serializers.Serializer):
    """Serializer for Pathlog Wallet OTP verification"""
    payment_id = serializers.IntegerField()
    otp = serializers.CharField(max_length=6, min_length=6)
    
    def validate_payment_id(self, value):
        user = self.context['request'].user
        try:
            payment = Payment.objects.get(id=value, user=user)
            if payment.payment_method != 'pathlog_wallet':
                raise serializers.ValidationError("Not a Pathlog Wallet payment")
            if payment.pathlog_wallet_verified:
                raise serializers.ValidationError("Wallet already verified")
            return value
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Payment not found or doesn't belong to you")


class PathlogWalletPaymentSerializer(serializers.Serializer):
    """Serializer for Pathlog Wallet payment processing"""
    payment_id = serializers.IntegerField()
    
    def validate_payment_id(self, value):
        user = self.context['request'].user
        try:
            payment = Payment.objects.get(id=value, user=user)
            if payment.payment_method != 'pathlog_wallet':
                raise serializers.ValidationError("Not a Pathlog Wallet payment")
            if not payment.pathlog_wallet_verified:
                raise serializers.ValidationError("Wallet not verified")
            if payment.status != 'pending':
                raise serializers.ValidationError("Payment already processed")
            return value
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Payment not found or doesn't belong to you")