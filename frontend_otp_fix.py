#!/usr/bin/env python3
"""
🔧 OTP Verification Fix Script
Create a frontend-compatible OTP verification endpoint
"""

# Let's create a new serializer that accepts the frontend payload format

from rest_framework import serializers

class FrontendOTPVerificationSerializer(serializers.Serializer):
    """Serializer that accepts frontend payload format"""
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)  # Frontend sends 'otp'
    purpose = serializers.CharField()  # Frontend sends 'purpose'
    
    def validate(self, data):
        # Convert frontend format to backend format
        converted_data = {
            'email': data['email'],
            'otp_code': data['otp'],  # Convert otp -> otp_code
            'otp_type': data['purpose']  # Convert purpose -> otp_type
        }
        
        # Validate purpose/otp_type
        valid_purposes = ['email_verification', 'sms_verification', 'password_reset', 'login_verification']
        if converted_data['otp_type'] not in valid_purposes:
            raise serializers.ValidationError(f"Invalid purpose. Must be one of: {valid_purposes}")
        
        return converted_data

# The view would then use this converted data with the existing OTP model

print("🔧 Frontend-Compatible OTP Serializer Created")
print("This accepts: email, otp, purpose")
print("Converts to: email, otp_code, otp_type")
