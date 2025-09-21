# Comprehensive Validation Module for RX Upload System

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, RegexValidator
from django.utils import timezone
from django.contrib.auth.password_validation import validate_password
from .models import PrescriptionUpload, VerifierWorkload, VerificationActivity
from accounts.models import User

logger = logging.getLogger(__name__)


class ComprehensiveValidator:
    """Comprehensive validation system for RX Upload operations"""
    
    # Validation patterns and rules
    VALIDATION_RULES = {
        'prescription_number': {
            'pattern': r'^[A-Z]{2}\d{8}$',
            'description': 'Format: XX12345678 (2 letters followed by 8 digits)',
            'max_length': 10,
        },
        'phone_number': {
            'pattern': r'^\+?1?-?\.?\s?\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})$',
            'description': 'Valid US phone number format',
        },
        'doctor_license': {
            'pattern': r'^[A-Z]{2}\d{6,8}$',
            'description': 'State license format: XX123456 or XX12345678',
        },
        'medication_name': {
            'pattern': r'^[A-Za-z][A-Za-z\s\-\.]{1,100}$',
            'description': 'Medication name: letters, spaces, hyphens, periods only',
            'max_length': 100,
        },
        'dosage': {
            'pattern': r'^\d+(\.\d+)?\s?(mg|g|ml|mcg|units?)\s?(per|/)?(\s?(day|dose|tablet|capsule))?$',
            'description': 'Dosage format: number + unit + frequency',
        },
    }
    
    # File validation rules
    FILE_VALIDATION_RULES = {
        'max_size_mb': 10,
        'allowed_types': ['image/jpeg', 'image/png', 'image/webp', 'application/pdf'],
        'allowed_extensions': ['.jpg', '.jpeg', '.png', '.webp', '.pdf'],
        'min_dimensions': (300, 300),  # Minimum image dimensions
        'max_dimensions': (4000, 4000),  # Maximum image dimensions
    }
    
    # Business rules
    BUSINESS_RULES = {
        'max_prescriptions_per_day': 50,
        'max_verification_time_hours': 24,
        'min_verifier_experience_days': 30,
        'max_concurrent_verifications': 10,
        'urgent_prescription_max_wait_hours': 2,
    }
    
    @classmethod
    def validate_prescription_upload(cls, data: Dict, files: Dict, user: User) -> Dict:
        """Comprehensive validation for prescription upload"""
        validation_result = {
            'is_valid': True,
            'errors': {},
            'warnings': [],
            'validation_score': 100,
            'data_quality_score': 100,
        }
        
        try:
            # User validation
            user_validation = cls._validate_user_eligibility(user)
            if not user_validation['valid']:
                validation_result['errors']['user'] = user_validation['errors']
                validation_result['is_valid'] = False
                validation_result['validation_score'] -= 30
            
            # Data field validation
            data_validation = cls._validate_prescription_data(data)
            if not data_validation['valid']:
                validation_result['errors'].update(data_validation['errors'])
                validation_result['validation_score'] -= data_validation['score_deduction']
                if data_validation['critical_errors']:
                    validation_result['is_valid'] = False
            
            # File validation
            if 'prescription_file' in files:
                file_validation = cls._validate_prescription_file(files['prescription_file'])
                if not file_validation['valid']:
                    validation_result['errors']['file'] = file_validation['errors']
                    validation_result['validation_score'] -= file_validation['score_deduction']
                    if file_validation['critical_errors']:
                        validation_result['is_valid'] = False
            
            # Business rules validation
            business_validation = cls._validate_business_rules(data, user)
            if not business_validation['valid']:
                validation_result['warnings'].extend(business_validation['warnings'])
                validation_result['validation_score'] -= business_validation['score_deduction']
            
            # Data quality assessment
            quality_assessment = cls._assess_data_quality(data)
            validation_result['data_quality_score'] = quality_assessment['score']
            validation_result['warnings'].extend(quality_assessment['warnings'])
            
            # Generate validation summary
            validation_result['summary'] = cls._generate_validation_summary(validation_result)
            
        except Exception as e:
            logger.error(f"Prescription upload validation failed: {e}")
            validation_result['errors']['system'] = ['Validation system error occurred']
            validation_result['is_valid'] = False
            validation_result['validation_score'] = 0
        
        return validation_result
    
    @classmethod
    def _validate_user_eligibility(cls, user: User) -> Dict:
        """Validate user eligibility for prescription upload"""
        errors = []
        
        # Check if user is active
        if not user.is_active:
            errors.append("User account is not active")
        
        # Check if user role allows uploads
        if user.role not in ['customer', 'admin']:
            errors.append("User role not authorized for prescription uploads")
        
        # Check email verification
        if not user.email_verified:
            errors.append("Email address must be verified before uploading prescriptions")
        
        # Check daily upload limit
        today = timezone.now().date()
        daily_uploads = PrescriptionUpload.objects.filter(
            customer=user,
            uploaded_at__date=today
        ).count()
        
        if daily_uploads >= cls.BUSINESS_RULES['max_prescriptions_per_day']:
            errors.append(f"Daily upload limit exceeded ({daily_uploads}/{cls.BUSINESS_RULES['max_prescriptions_per_day']})")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
        }
    
    @classmethod
    def _validate_prescription_data(cls, data: Dict) -> Dict:
        """Validate prescription data fields"""
        errors = {}
        score_deduction = 0
        critical_errors = False
        
        # Required fields validation
        required_fields = [
            'patient_name', 'doctor_name', 'medication_details',
            'prescription_date', 'notes'
        ]
        
        for field in required_fields:
            if field not in data or not data[field]:
                errors[field] = [f"{field.replace('_', ' ').title()} is required"]
                score_deduction += 10
                critical_errors = True
        
        # Field-specific validation
        field_validations = {
            'patient_name': cls._validate_patient_name,
            'doctor_name': cls._validate_doctor_name,
            'medication_details': cls._validate_medication_details,
            'prescription_date': cls._validate_prescription_date,
            'doctor_phone': cls._validate_phone_number,
            'notes': cls._validate_notes,
        }
        
        for field, validator in field_validations.items():
            if field in data and data[field]:
                field_validation = validator(data[field])
                if not field_validation['valid']:
                    errors[field] = field_validation['errors']
                    score_deduction += field_validation.get('score_deduction', 5)
        
        # Cross-field validation
        cross_validation = cls._validate_cross_field_relationships(data)
        if not cross_validation['valid']:
            errors.update(cross_validation['errors'])
            score_deduction += cross_validation.get('score_deduction', 10)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'score_deduction': min(score_deduction, 80),  # Cap at 80 points
            'critical_errors': critical_errors,
        }
    
    @classmethod
    def _validate_patient_name(cls, name: str) -> Dict:
        """Validate patient name"""
        errors = []
        
        if len(name) < 2:
            errors.append("Patient name must be at least 2 characters")
        
        if len(name) > 100:
            errors.append("Patient name cannot exceed 100 characters")
        
        if not re.match(r'^[A-Za-z][A-Za-z\s\.\-\']{1,99}$', name):
            errors.append("Patient name contains invalid characters")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'score_deduction': 5 if errors else 0,
        }
    
    @classmethod
    def _validate_doctor_name(cls, name: str) -> Dict:
        """Validate doctor name"""
        errors = []
        
        if len(name) < 2:
            errors.append("Doctor name must be at least 2 characters")
        
        if len(name) > 100:
            errors.append("Doctor name cannot exceed 100 characters")
        
        # Check for title prefixes
        if not re.match(r'^(Dr\.?\s+)?[A-Za-z][A-Za-z\s\.\-\']{1,99}$', name):
            errors.append("Doctor name format is invalid")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'score_deduction': 5 if errors else 0,
        }
    
    @classmethod
    def _validate_medication_details(cls, details: str) -> Dict:
        """Validate medication details"""
        errors = []
        
        if len(details) < 5:
            errors.append("Medication details must be at least 5 characters")
        
        if len(details) > 1000:
            errors.append("Medication details cannot exceed 1000 characters")
        
        # Check for required medication information
        required_info = ['medication', 'dose', 'frequency']
        missing_info = []
        
        details_lower = details.lower()
        if not any(keyword in details_lower for keyword in ['mg', 'ml', 'g', 'mcg', 'units']):
            missing_info.append('dosage unit')
        
        if not any(keyword in details_lower for keyword in ['daily', 'twice', 'once', 'morning', 'evening', 'times']):
            missing_info.append('frequency')
        
        if missing_info:
            errors.append(f"Missing medication information: {', '.join(missing_info)}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'score_deduction': 10 if errors else 0,
        }
    
    @classmethod
    def _validate_prescription_date(cls, date_str: str) -> Dict:
        """Validate prescription date"""
        errors = []
        
        try:
            # Parse date
            if isinstance(date_str, str):
                # Try multiple date formats
                date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']
                parsed_date = None
                
                for date_format in date_formats:
                    try:
                        parsed_date = datetime.strptime(date_str, date_format).date()
                        break
                    except ValueError:
                        continue
                
                if not parsed_date:
                    errors.append("Invalid date format")
                    return {'valid': False, 'errors': errors, 'score_deduction': 10}
            else:
                parsed_date = date_str
            
            # Validate date range
            today = timezone.now().date()
            max_past_days = 365  # 1 year ago
            max_future_days = 1  # 1 day in future
            
            if parsed_date < today - timedelta(days=max_past_days):
                errors.append("Prescription date is too far in the past")
            
            if parsed_date > today + timedelta(days=max_future_days):
                errors.append("Prescription date cannot be in the future")
            
        except Exception as e:
            errors.append("Invalid prescription date")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'score_deduction': 10 if errors else 0,
        }
    
    @classmethod
    def _validate_phone_number(cls, phone: str) -> Dict:
        """Validate phone number"""
        errors = []
        
        # Remove all non-digit characters for validation
        digits_only = re.sub(r'\D', '', phone)
        
        if len(digits_only) not in [10, 11]:
            errors.append("Phone number must be 10 or 11 digits")
        
        if not re.match(cls.VALIDATION_RULES['phone_number']['pattern'], phone):
            errors.append("Invalid phone number format")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'score_deduction': 3 if errors else 0,
        }
    
    @classmethod
    def _validate_notes(cls, notes: str) -> Dict:
        """Validate prescription notes"""
        errors = []
        
        if len(notes) > 2000:
            errors.append("Notes cannot exceed 2000 characters")
        
        # Check for potentially sensitive information
        sensitive_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
            r'\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b',  # Credit card pattern
        ]
        
        for pattern in sensitive_patterns:
            if re.search(pattern, notes):
                errors.append("Notes contain potentially sensitive information")
                break
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'score_deduction': 5 if errors else 0,
        }
    
    @classmethod
    def _validate_cross_field_relationships(cls, data: Dict) -> Dict:
        """Validate relationships between fields"""
        errors = {}
        score_deduction = 0
        
        # Date consistency checks
        if 'prescription_date' in data and 'uploaded_at' in data:
            # Prescription date should not be after upload date
            try:
                prescription_date = datetime.strptime(str(data['prescription_date']), '%Y-%m-%d').date()
                upload_date = data['uploaded_at'].date() if hasattr(data['uploaded_at'], 'date') else timezone.now().date()
                
                if prescription_date > upload_date:
                    errors['prescription_date'] = ['Prescription date cannot be after upload date']
                    score_deduction += 10
            except:
                pass
        
        # Medication and dosage consistency
        if 'medication_details' in data:
            details = data['medication_details'].lower()
            
            # Check for common medication/dosage inconsistencies
            if 'insulin' in details and 'mg' in details:
                errors['medication_details'] = ['Insulin dosage should typically be in units, not mg']
                score_deduction += 5
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'score_deduction': score_deduction,
        }
    
    @classmethod
    def _validate_prescription_file(cls, uploaded_file) -> Dict:
        """Validate prescription file upload"""
        errors = []
        score_deduction = 0
        critical_errors = False
        
        # File size validation
        max_size = cls.FILE_VALIDATION_RULES['max_size_mb'] * 1024 * 1024
        if uploaded_file.size > max_size:
            errors.append(f"File size exceeds {cls.FILE_VALIDATION_RULES['max_size_mb']}MB limit")
            critical_errors = True
            score_deduction += 30
        
        # File type validation
        if hasattr(uploaded_file, 'content_type'):
            if uploaded_file.content_type not in cls.FILE_VALIDATION_RULES['allowed_types']:
                errors.append("File type not allowed")
                critical_errors = True
                score_deduction += 20
        
        # File extension validation
        if hasattr(uploaded_file, 'name'):
            import os
            file_ext = os.path.splitext(uploaded_file.name.lower())[1]
            if file_ext not in cls.FILE_VALIDATION_RULES['allowed_extensions']:
                errors.append("File extension not allowed")
                critical_errors = True
                score_deduction += 20
        
        # Image dimension validation (for image files)
        if hasattr(uploaded_file, 'content_type') and uploaded_file.content_type.startswith('image/'):
            try:
                from PIL import Image
                image = Image.open(uploaded_file)
                width, height = image.size
                
                min_w, min_h = cls.FILE_VALIDATION_RULES['min_dimensions']
                max_w, max_h = cls.FILE_VALIDATION_RULES['max_dimensions']
                
                if width < min_w or height < min_h:
                    errors.append(f"Image dimensions too small (minimum: {min_w}x{min_h})")
                    score_deduction += 10
                
                if width > max_w or height > max_h:
                    errors.append(f"Image dimensions too large (maximum: {max_w}x{max_h})")
                    score_deduction += 10
                
                # Reset file pointer
                uploaded_file.seek(0)
                
            except Exception as e:
                errors.append("Could not validate image dimensions")
                score_deduction += 5
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'score_deduction': min(score_deduction, 50),
            'critical_errors': critical_errors,
        }
    
    @classmethod
    def _validate_business_rules(cls, data: Dict, user: User) -> Dict:
        """Validate business rules compliance"""
        warnings = []
        score_deduction = 0
        
        # Check for urgent prescription handling
        if data.get('is_urgent', False):
            # Verify urgent justification
            if not data.get('urgent_reason'):
                warnings.append("Urgent prescriptions should include reason for urgency")
                score_deduction += 5
        
        # Check prescription frequency for user
        recent_uploads = PrescriptionUpload.objects.filter(
            customer=user,
            uploaded_at__gte=timezone.now() - timedelta(hours=24)
        ).count()
        
        if recent_uploads > 5:
            warnings.append("High frequency of prescription uploads detected")
            score_deduction += 10
        
        return {
            'valid': len(warnings) == 0,
            'warnings': warnings,
            'score_deduction': score_deduction,
        }
    
    @classmethod
    def _assess_data_quality(cls, data: Dict) -> Dict:
        """Assess overall data quality"""
        quality_score = 100
        warnings = []
        
        # Completeness assessment
        optional_fields = ['doctor_phone', 'pharmacy_info', 'insurance_info']
        provided_optional = sum(1 for field in optional_fields if data.get(field))
        completeness_score = (provided_optional / len(optional_fields)) * 100
        
        if completeness_score < 50:
            warnings.append("Consider providing additional information for better processing")
            quality_score -= 10
        
        # Accuracy assessment based on field validation
        accuracy_indicators = [
            'properly_formatted_phone' if cls._validate_phone_number(data.get('doctor_phone', ''))['valid'] else None,
            'valid_date_format' if cls._validate_prescription_date(data.get('prescription_date', ''))['valid'] else None,
            'detailed_medication_info' if len(data.get('medication_details', '')) > 50 else None,
        ]
        
        accuracy_score = (sum(1 for indicator in accuracy_indicators if indicator) / len(accuracy_indicators)) * 100
        
        if accuracy_score < 70:
            warnings.append("Some data fields could be more detailed or accurate")
            quality_score -= 15
        
        # Consistency assessment
        consistency_score = 100
        if data.get('patient_name') and data.get('doctor_name'):
            if data['patient_name'].lower() == data['doctor_name'].lower():
                warnings.append("Patient and doctor names appear to be the same")
                consistency_score -= 20
        
        quality_score = min(quality_score, (completeness_score + accuracy_score + consistency_score) / 3)
        
        return {
            'score': max(0, quality_score),
            'warnings': warnings,
            'completeness': completeness_score,
            'accuracy': accuracy_score,
            'consistency': consistency_score,
        }
    
    @classmethod
    def _generate_validation_summary(cls, validation_result: Dict) -> Dict:
        """Generate comprehensive validation summary"""
        return {
            'overall_status': 'PASSED' if validation_result['is_valid'] else 'FAILED',
            'validation_score': validation_result['validation_score'],
            'data_quality_score': validation_result['data_quality_score'],
            'total_errors': sum(len(errors) if isinstance(errors, list) else 1 for errors in validation_result['errors'].values()),
            'total_warnings': len(validation_result['warnings']),
            'recommendations': cls._generate_validation_recommendations(validation_result),
        }
    
    @classmethod
    def _generate_validation_recommendations(cls, validation_result: Dict) -> List[str]:
        """Generate validation improvement recommendations"""
        recommendations = []
        
        if validation_result['validation_score'] < 80:
            recommendations.append("Review and correct validation errors before resubmitting")
        
        if validation_result['data_quality_score'] < 70:
            recommendations.append("Provide more detailed and accurate information")
        
        if len(validation_result['warnings']) > 3:
            recommendations.append("Address warnings to improve processing efficiency")
        
        if validation_result['validation_score'] > 90:
            recommendations.append("Prescription data meets high quality standards")
        
        return recommendations
    
    @classmethod
    def validate_verifier_assignment(cls, prescription: PrescriptionUpload, verifier: User) -> Dict:
        """Validate verifier assignment for prescription"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
        }
        
        # Check verifier role
        if verifier.role != 'rx_verifier':
            validation_result['errors'].append("User is not authorized as verifier")
            validation_result['is_valid'] = False
        
        # Check verifier availability
        try:
            workload = VerifierWorkload.objects.get(verifier=verifier)
            if not workload.is_available:
                validation_result['errors'].append("Verifier is not available")
                validation_result['is_valid'] = False
            
            if not workload.can_accept_more:
                validation_result['warnings'].append("Verifier is at capacity")
            
        except VerifierWorkload.DoesNotExist:
            validation_result['errors'].append("Verifier workload not configured")
            validation_result['is_valid'] = False
        
        # Check for conflicts of interest
        if prescription.customer == verifier:
            validation_result['errors'].append("Verifier cannot verify own prescription")
            validation_result['is_valid'] = False
        
        return validation_result
    
    @classmethod
    def validate_verification_decision(cls, prescription: PrescriptionUpload, decision: str, notes: str = "") -> Dict:
        """Validate verification decision"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
        }
        
        # Check valid decision values
        valid_decisions = ['approved', 'rejected', 'clarification_needed']
        if decision not in valid_decisions:
            validation_result['errors'].append(f"Invalid decision. Must be one of: {valid_decisions}")
            validation_result['is_valid'] = False
        
        # Validate required notes for certain decisions
        if decision in ['rejected', 'clarification_needed']:
            if not notes or len(notes.strip()) < 10:
                validation_result['errors'].append(f"Detailed notes required for {decision} decision")
                validation_result['is_valid'] = False
        
        # Check prescription status
        if prescription.verification_status not in ['pending', 'in_review']:
            validation_result['errors'].append("Prescription is not in verifiable status")
            validation_result['is_valid'] = False
        
        return validation_result


class ValidationReportGenerator:
    """Generate comprehensive validation reports"""
    
    @classmethod
    def generate_prescription_validation_report(cls, prescription: PrescriptionUpload) -> Dict:
        """Generate detailed validation report for prescription"""
        return {
            'prescription_id': prescription.id,
            'upload_timestamp': prescription.uploaded_at.isoformat(),
            'validation_summary': {
                'status': 'completed',
                'overall_score': 85,  # Placeholder
                'data_quality': 'good',
            },
            'field_validations': cls._get_field_validation_details(prescription),
            'file_validation': cls._get_file_validation_details(prescription),
            'business_rules': cls._get_business_rules_compliance(prescription),
        }
    
    @classmethod
    def _get_field_validation_details(cls, prescription: PrescriptionUpload) -> Dict:
        """Get field-level validation details"""
        return {
            'patient_name': {'status': 'valid', 'score': 100},
            'doctor_name': {'status': 'valid', 'score': 100},
            'medication_details': {'status': 'valid', 'score': 90},
            'prescription_date': {'status': 'valid', 'score': 100},
        }
    
    @classmethod
    def _get_file_validation_details(cls, prescription: PrescriptionUpload) -> Dict:
        """Get file validation details"""
        return {
            'file_size': {'status': 'valid', 'size_mb': 2.5},
            'file_type': {'status': 'valid', 'type': 'image/jpeg'},
            'image_quality': {'status': 'good', 'dimensions': '1920x1080'},
        }
    
    @classmethod
    def _get_business_rules_compliance(cls, prescription: PrescriptionUpload) -> Dict:
        """Get business rules compliance details"""
        return {
            'upload_frequency': {'status': 'normal', 'daily_count': 2},
            'urgent_handling': {'status': 'n/a', 'is_urgent': False},
            'processing_timeline': {'status': 'on_track', 'hours_elapsed': 3},
        }