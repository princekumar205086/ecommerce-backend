# rx_upload/serializers.py
import logging
from rest_framework import serializers
from django.contrib.auth import get_user_model
from accounts.models import upload_to_imagekit
from .models import PrescriptionUpload, VerificationActivity, VerifierWorkload, PrescriptionMedication
import uuid

logger = logging.getLogger(__name__)
User = get_user_model()


class RXVerifierLoginSerializer(serializers.Serializer):
    """Serializer for RX verifier login"""
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)


class PrescriptionMedicationSerializer(serializers.ModelSerializer):
    """Serializer for prescription medications"""
    
    class Meta:
        model = PrescriptionMedication
        fields = [
            'id', 'medication_name', 'dosage', 'frequency', 'duration',
            'quantity', 'special_instructions', 'is_verified', 'verification_notes'
        ]
        read_only_fields = ['id', 'is_verified', 'verification_notes']


class PrescriptionUploadSerializer(serializers.ModelSerializer):
    """Serializer for prescription uploads with ImageKit integration"""
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.full_name', read_only=True)
    medications = PrescriptionMedicationSerializer(many=True, read_only=True)
    processing_time = serializers.ReadOnlyField()
    can_be_verified = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    
    # File upload field for ImageKit integration
    prescription_file = serializers.FileField(write_only=True, required=False, help_text="Upload prescription image or PDF")
    
    class Meta:
        model = PrescriptionUpload
        fields = [
            'id', 'prescription_number', 'customer', 'customer_name', 'customer_email',
            'doctor_name', 'doctor_license', 'hospital_clinic', 'patient_name', 
            'patient_age', 'patient_gender', 'prescription_type', 'prescription_image',
            'prescription_file_url', 'original_filename', 'file_size',
            'diagnosis', 'medications_prescribed', 'dosage_instructions',
            'prescription_date', 'prescription_valid_until', 'verification_status',
            'verified_by', 'verified_by_name', 'verification_date', 'verification_notes',
            'customer_notes', 'clarification_requested', 'customer_response',
            'image_quality_score', 'legibility_score', 'completeness_score',
            'uploaded_at', 'updated_at', 'is_urgent', 'priority_level',
            'customer_phone', 'alternative_contact', 'medications',
            'processing_time', 'can_be_verified', 'is_overdue', 'prescription_file'
        ]
        read_only_fields = [
            'id', 'prescription_number', 'customer', 'customer_name', 'customer_email',
            'verified_by', 'verified_by_name', 'verification_date', 'verification_notes',
            'uploaded_at', 'updated_at', 'processing_time', 'can_be_verified', 'is_overdue'
        ]
    
    def validate_prescription_file(self, value):
        """Validate uploaded prescription file"""
        if value:
            # Check file size (max 10MB)
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError("File size cannot exceed 10MB")
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'application/pdf']
            if hasattr(value, 'content_type') and value.content_type not in allowed_types:
                raise serializers.ValidationError(
                    "Only JPEG, PNG, GIF, WebP images and PDF files are allowed"
                )
            
            # Check file extension
            import os
            ext = os.path.splitext(value.name)[1].lower()
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf']
            if ext not in allowed_extensions:
                raise serializers.ValidationError(
                    "File must have a valid extension (.jpg, .jpeg, .png, .gif, .webp, .pdf)"
                )
        
        return value
    
    def create(self, validated_data):
        """Handle prescription upload creation with ImageKit integration"""
        # Remove file from validated_data to handle separately
        prescription_file = validated_data.pop('prescription_file', None)
        
        # Create prescription instance
        prescription = super().create(validated_data)
        
        # Handle file upload if present
        if prescription_file:
            try:
                # Read file content
                file_content = prescription_file.read()
                filename = prescription_file.name
                
                # Generate unique filename
                import os
                name, ext = os.path.splitext(filename)
                unique_filename = f"prescription_{prescription.id}_{uuid.uuid4().hex[:8]}{ext}"
                
                # Upload to ImageKit
                image_url = upload_to_imagekit(
                    file_content, 
                    unique_filename, 
                    folder="prescriptions"
                )
                
                if image_url:
                    # Update prescription with ImageKit URL
                    prescription.prescription_image = image_url
                    prescription.original_filename = filename
                    prescription.file_size = len(file_content)
                    
                    # Set prescription type based on file
                    if filename.lower().endswith('.pdf'):
                        prescription.prescription_type = 'pdf'
                    else:
                        prescription.prescription_type = 'image'
                    
                    prescription.save()
                    logger.info(f"✅ Prescription file uploaded to ImageKit: {image_url}")
                else:
                    # If upload failed, delete the prescription and raise error
                    logger.error("❌ ImageKit upload failed - no URL returned")
                    prescription.delete()
                    raise serializers.ValidationError({
                        'prescription_file': 'Failed to upload file to ImageKit. Please try again.'
                    })
                    
            except Exception as e:
                # If any error occurs, delete the prescription and raise error
                prescription.delete()
                raise serializers.ValidationError({
                    'prescription_file': f'File upload failed: {str(e)}'
                })
        
        return prescription
    
    def update(self, instance, validated_data):
        """Handle prescription update with optional file replacement"""
        # Remove file from validated_data to handle separately
        prescription_file = validated_data.pop('prescription_file', None)
        
        # Update other fields
        instance = super().update(instance, validated_data)
        
        # Handle file replacement if present
        if prescription_file:
            try:
                # Read file content
                file_content = prescription_file.read()
                filename = prescription_file.name
                
                # Generate unique filename
                import os
                name, ext = os.path.splitext(filename)
                unique_filename = f"prescription_{instance.id}_{uuid.uuid4().hex[:8]}{ext}"
                
                # Upload to ImageKit
                image_url = upload_to_imagekit(
                    file_content, 
                    unique_filename, 
                    folder="prescriptions"
                )
                
                if image_url:
                    # Update prescription with new ImageKit URL
                    instance.prescription_image = image_url
                    instance.original_filename = filename
                    instance.file_size = len(file_content)
                    
                    # Set prescription type based on file
                    if filename.lower().endswith('.pdf'):
                        instance.prescription_type = 'pdf'
                    else:
                        instance.prescription_type = 'image'
                    
                    instance.save()
                else:
                    raise serializers.ValidationError({
                        'prescription_file': 'Failed to upload file to ImageKit. Please try again.'
                    })
                    
            except Exception as e:
                raise serializers.ValidationError({
                    'prescription_file': f'File upload failed: {str(e)}'
                })
        
        return instance


class PrescriptionVerificationSerializer(serializers.ModelSerializer):
    """Serializer for prescription verification actions"""
    
    class Meta:
        model = PrescriptionUpload
        fields = [
            'id', 'prescription_number', 'verification_status', 'verified_by',
            'verification_date', 'verification_notes', 'clarification_requested'
        ]
        read_only_fields = ['id', 'prescription_number', 'verified_by', 'verification_date']


class VerificationActivitySerializer(serializers.ModelSerializer):
    """Serializer for verification activities"""
    verifier_name = serializers.CharField(source='verifier.full_name', read_only=True)
    prescription_number = serializers.CharField(source='prescription.prescription_number', read_only=True)
    
    class Meta:
        model = VerificationActivity
        fields = [
            'id', 'prescription', 'prescription_number', 'verifier', 'verifier_name',
            'action', 'description', 'timestamp'
        ]
        read_only_fields = ['id', 'prescription_number', 'verifier_name', 'timestamp']


class VerifierWorkloadSerializer(serializers.ModelSerializer):
    """Serializer for verifier workload statistics"""
    verifier_name = serializers.CharField(source='verifier.full_name', read_only=True)
    verifier_email = serializers.CharField(source='verifier.email', read_only=True)
    approval_rate = serializers.ReadOnlyField()
    can_accept_more = serializers.ReadOnlyField()
    
    class Meta:
        model = VerifierWorkload
        fields = [
            'id', 'verifier', 'verifier_name', 'verifier_email',
            'pending_count', 'in_review_count', 'total_verified',
            'total_approved', 'total_rejected', 'average_processing_time',
            'accuracy_score', 'customer_satisfaction', 'is_available',
            'max_daily_capacity', 'current_daily_count', 'last_activity',
            'approval_rate', 'can_accept_more'
        ]
        read_only_fields = [
            'id', 'verifier_name', 'verifier_email', 'pending_count',
            'in_review_count', 'last_activity', 'approval_rate', 'can_accept_more'
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for RX verifier user profile"""
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'contact', 'role',
            'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'email', 'role', 'date_joined', 'last_login']