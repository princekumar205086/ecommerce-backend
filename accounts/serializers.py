# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ValidationError

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
        fields = ['id', 'email', 'full_name', 'contact', 'role', 'has_address', 'medixmall_mode']


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
