# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import OTP, PasswordResetToken

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = get_user_model()
        fields = ['email', 'full_name', 'contact', 'password', 'password2']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = get_user_model().objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        # Send email verification - don't fail registration if email fails
        try:
            success, message = user.send_verification_email()
            if not success:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to send verification email to {user.email}: {message}")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Exception while sending verification email to {user.email}: {str(e)}")
        
        return user

class SupplierRegisterSerializer(UserRegisterSerializer):
    company_name = serializers.CharField(required=True, max_length=255)
    gst_number = serializers.CharField(required=True, max_length=15)

    class Meta(UserRegisterSerializer.Meta):
        fields = UserRegisterSerializer.Meta.fields + ['company_name', 'gst_number']

    def validate(self, data):
        data = super().validate(data)
        if self.context.get('role') == 'supplier':
            if not data.get('company_name') or not data.get('gst_number'):
                raise serializers.ValidationError({
                    "company_name": "Company name is required for suppliers.",
                    "gst_number": "GST number is required for suppliers."
                })
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = get_user_model().objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        # Send email verification - don't fail registration if email fails
        try:
            success, message = user.send_verification_email()
            if not success:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to send verification email to {user.email}: {message}")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Exception while sending verification email to {user.email}: {str(e)}")
        
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(email=email, password=password)
            if user:
                if user.is_active:
                    data['user'] = user
                else:
                    raise ValidationError("User is deactivated.")
            else:
                raise ValidationError("Unable to log in with provided credentials.")
        else:
            raise ValidationError("Must include 'email' and 'password'.")

        return data

class UserSerializer(serializers.ModelSerializer):
    has_address = serializers.ReadOnlyField()
    
    class Meta:
        model = get_user_model()
        fields = ['id', 'email', 'full_name', 'contact', 'role', 'has_address', 'medixmall_mode', 'email_verified']


class OTPVerificationSerializer(serializers.Serializer):
    """Serializer for OTP verification"""
    otp_code = serializers.CharField(max_length=6, min_length=6)
    otp_type = serializers.ChoiceField(choices=OTP.OTP_TYPES)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=20, required=False)

    def validate(self, data):
        if not data.get('email') and not data.get('phone'):
            raise serializers.ValidationError("Either email or phone must be provided")
        return data


class OTPRequestSerializer(serializers.Serializer):
    """Serializer for requesting OTP"""
    otp_type = serializers.ChoiceField(choices=OTP.OTP_TYPES)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=20, required=False)

    def validate(self, data):
        if not data.get('email') and not data.get('phone'):
            raise serializers.ValidationError("Either email or phone must be provided")
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    email = serializers.EmailField()

    def validate_email(self, value):
        User = get_user_model()
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords don't match."})
        
        # Validate token
        try:
            reset_token = PasswordResetToken.objects.get(token=data['token'])
            if not reset_token.is_valid():
                raise serializers.ValidationError({"token": "Invalid or expired token."})
            data['reset_token'] = reset_token
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError({"token": "Invalid token."})
        
        return data


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification"""
    token = serializers.CharField()


class ResendVerificationSerializer(serializers.Serializer):
    """Serializer for resending verification email"""
    email = serializers.EmailField()

    def validate_email(self, value):
        User = get_user_model()
        try:
            user = User.objects.get(email=value)
            if user.email_verified:
                raise serializers.ValidationError("Email is already verified.")
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords don't match."})
        return data

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Invalid current password.")
        return value


class MedixMallModeSerializer(serializers.Serializer):
    """Serializer for toggling MedixMall mode"""
    medixmall_mode = serializers.BooleanField(
        help_text="Enable to show only medicine products (MedixMall mode)"
    )
    
    def update(self, instance, validated_data):
        instance.medixmall_mode = validated_data.get('medixmall_mode', instance.medixmall_mode)
        instance.save()
        return instance


class UserAddressSerializer(serializers.ModelSerializer):
    """Serializer for user address management"""
    has_address = serializers.ReadOnlyField()
    full_address = serializers.ReadOnlyField()
    
    class Meta:
        model = get_user_model()
        fields = [
            'id', 'email', 'full_name', 'contact', 
            'address_line_1', 'address_line_2', 'city', 'state', 
            'postal_code', 'country', 'has_address', 'full_address'
        ]
        read_only_fields = ['id', 'email']


class UpdateAddressSerializer(serializers.ModelSerializer):
    """Serializer for updating user address"""
    
    class Meta:
        model = get_user_model()
        fields = [
            'address_line_1', 'address_line_2', 'city', 'state', 
            'postal_code', 'country'
        ]
    
    def validate(self, data):
        """Validate required address fields"""
        required_fields = ['address_line_1', 'city', 'state', 'postal_code', 'country']
        missing_fields = []
        
        for field in required_fields:
            if not data.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            raise serializers.ValidationError({
                'required_fields': f'Missing required fields: {", ".join(missing_fields)}'
            })
        
        return data


class OTPLoginRequestSerializer(serializers.Serializer):
    """Serializer for requesting OTP login"""
    email = serializers.EmailField(required=False)
    contact = serializers.CharField(max_length=15, required=False)
    
    def validate(self, data):
        if not data.get('email') and not data.get('contact'):
            raise serializers.ValidationError(
                "Either email or contact number is required"
            )
        
        # Check if user exists with provided email or contact
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if data.get('email'):
            if not User.objects.filter(email=data['email']).exists():
                raise serializers.ValidationError(
                    {"email": "No account found with this email address"}
                )
        
        if data.get('contact'):
            if not User.objects.filter(contact=data['contact']).exists():
                raise serializers.ValidationError(
                    {"contact": "No account found with this contact number"}
                )
        
        return data


class OTPLoginVerifySerializer(serializers.Serializer):
    """Serializer for verifying OTP login"""
    email = serializers.EmailField(required=False)
    contact = serializers.CharField(max_length=15, required=False)
    otp_code = serializers.CharField(max_length=6, required=True)
    
    def validate(self, data):
        if not data.get('email') and not data.get('contact'):
            raise serializers.ValidationError(
                "Either email or contact number is required"
            )
        
        return data


class LoginChoiceSerializer(serializers.Serializer):
    """Serializer for login - supports both password and OTP"""
    email = serializers.EmailField(required=False)
    contact = serializers.CharField(max_length=15, required=False)
    password = serializers.CharField(required=False)
    login_type = serializers.ChoiceField(
        choices=[('password', 'Password'), ('otp', 'OTP')],
        required=True
    )
    
    def validate(self, data):
        if not data.get('email') and not data.get('contact'):
            raise serializers.ValidationError(
                "Either email or contact number is required"
            )
        
        if data.get('login_type') == 'password' and not data.get('password'):
            raise serializers.ValidationError(
                {"password": "Password is required for password login"}
            )
        
        return data
