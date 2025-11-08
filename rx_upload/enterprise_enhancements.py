# rx_upload/enterprise_enhancements.py
"""
Enterprise-Level Enhancements for RX Upload System
- Enhanced logging
- Error tracking
- Performance monitoring
- Security enhancements
- Audit trails
"""

import logging
import time
import functools
from decimal import Decimal
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


# ==========================================
# PERFORMANCE MONITORING DECORATOR
# ==========================================

def monitor_performance(func_name=None):
    """
    Decorator to monitor function performance
    Logs execution time and potential bottlenecks
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            function_name = func_name or func.__name__
            
            try:
                result = func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000  # Convert to ms
                
                # Log if execution time exceeds threshold (500ms)
                if execution_time > 500:
                    logger.warning(
                        f"⚠️ Performance: {function_name} took {execution_time:.2f}ms"
                    )
                else:
                    logger.info(
                        f"✓ Performance: {function_name} completed in {execution_time:.2f}ms"
                    )
                
                return result
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                logger.error(
                    f"✗ Error in {function_name} after {execution_time:.2f}ms: {str(e)}"
                )
                raise
                
        return wrapper
    return decorator


# ==========================================
# ENHANCED ERROR HANDLER
# ==========================================

class RXErrorHandler:
    """Centralized error handling for RX upload system"""
    
    @staticmethod
    def handle_prescription_error(error, prescription_id=None, context=None):
        """Handle prescription-related errors"""
        error_code = f"RX_ERROR_{int(time.time())}"
        
        logger.error(
            f"Prescription Error [{error_code}]",
            extra={
                'error_code': error_code,
                'prescription_id': str(prescription_id) if prescription_id else None,
                'error_message': str(error),
                'context': context or {}
            }
        )
        
        return {
            'success': False,
            'error_code': error_code,
            'message': 'An error occurred processing your prescription',
            'details': str(error) if settings.DEBUG else None
        }
    
    @staticmethod
    def handle_verification_error(error, verifier_id=None, prescription_id=None):
        """Handle verification-related errors"""
        error_code = f"VER_ERROR_{int(time.time())}"
        
        logger.error(
            f"Verification Error [{error_code}]",
            extra={
                'error_code': error_code,
                'verifier_id': verifier_id,
                'prescription_id': str(prescription_id) if prescription_id else None,
                'error_message': str(error)
            }
        )
        
        return {
            'success': False,
            'error_code': error_code,
            'message': 'Verification failed. Please try again.',
            'details': str(error) if settings.DEBUG else None
        }
    
    @staticmethod
    def handle_order_error(error, prescription_id=None, customer_id=None):
        """Handle order creation errors"""
        error_code = f"ORDER_ERROR_{int(time.time())}"
        
        logger.error(
            f"Order Creation Error [{error_code}]",
            extra={
                'error_code': error_code,
                'prescription_id': str(prescription_id) if prescription_id else None,
                'customer_id': customer_id,
                'error_message': str(error)
            }
        )
        
        return {
            'success': False,
            'error_code': error_code,
            'message': 'Order creation failed. Please contact support.',
            'details': str(error) if settings.DEBUG else None
        }


# ==========================================
# VALIDATION UTILITIES
# ==========================================

class RXValidator:
    """Enhanced validation for RX upload system"""
    
    @staticmethod
    def validate_prescription_data(data):
        """
        Validate prescription upload data
        Returns: (is_valid: bool, errors: dict)
        """
        errors = {}
        
        # Required fields
        required_fields = ['patient_name', 'prescription_type']
        for field in required_fields:
            if not data.get(field):
                errors[field] = f"{field} is required"
        
        # Patient age validation
        if data.get('patient_age'):
            try:
                age = int(data['patient_age'])
                if age < 0 or age > 150:
                    errors['patient_age'] = "Invalid age"
            except (ValueError, TypeError):
                errors['patient_age'] = "Age must be a number"
        
        # Phone number validation
        if data.get('customer_phone'):
            phone = str(data['customer_phone']).strip()
            if not phone.isdigit() or len(phone) not in [10, 11, 12]:
                errors['customer_phone'] = "Invalid phone number format"
        
        # Priority level validation
        if data.get('priority_level'):
            try:
                priority = int(data['priority_level'])
                if priority not in [1, 2, 3, 4]:
                    errors['priority_level'] = "Priority must be 1-4"
            except (ValueError, TypeError):
                errors['priority_level'] = "Invalid priority level"
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_medications_data(medications_data):
        """
        Validate medications data for order creation
        Returns: (is_valid: bool, errors: list)
        """
        errors = []
        
        if not medications_data or not isinstance(medications_data, list):
            return False, ["Medications data must be a non-empty list"]
        
        for idx, med in enumerate(medications_data):
            if not isinstance(med, dict):
                errors.append(f"Medication {idx+1}: Must be an object")
                continue
            
            # Required fields
            if not med.get('product_id'):
                errors.append(f"Medication {idx+1}: product_id is required")
            
            if not med.get('medication_name'):
                errors.append(f"Medication {idx+1}: medication_name is required")
            
            # Quantity validation
            quantity = med.get('quantity', 1)
            try:
                quantity = int(quantity)
                if quantity < 1 or quantity > 100:
                    errors.append(f"Medication {idx+1}: quantity must be between 1 and 100")
            except (ValueError, TypeError):
                errors.append(f"Medication {idx+1}: invalid quantity")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_verifier_notes(notes, action_type='approve'):
        """
        Validate verifier notes
        Returns: (is_valid: bool, error_message: str or None)
        """
        if action_type == 'reject' and not notes:
            return False, "Rejection reason is required"
        
        if action_type == 'clarification' and not notes:
            return False, "Clarification message is required"
        
        if notes and len(notes) > 2000:
            return False, "Notes cannot exceed 2000 characters"
        
        return True, None


# ==========================================
# AUDIT TRAIL LOGGER
# ==========================================

class RXAuditLogger:
    """Enhanced audit logging for compliance"""
    
    @staticmethod
    def log_prescription_action(prescription, action, user, details=None):
        """Log prescription actions for audit trail"""
        from .models import VerificationActivity
        
        try:
            # Create activity log
            activity = VerificationActivity.objects.create(
                prescription=prescription,
                verifier=user if user.role == 'rx_verifier' else None,
                action=action,
                description=details or f"{action.title()} by {user.full_name}"
            )
            
            # Also log to system logger
            logger.info(
                f"Prescription Action",
                extra={
                    'prescription_id': str(prescription.id),
                    'prescription_number': prescription.prescription_number,
                    'action': action,
                    'user_id': user.id,
                    'user_email': user.email,
                    'timestamp': timezone.now().isoformat(),
                    'details': details
                }
            )
            
            return activity
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
            return None
    
    @staticmethod
    def log_order_creation(order, prescription, user):
        """Log order creation from prescription"""
        logger.info(
            f"Order Created from Prescription",
            extra={
                'order_id': order.id,
                'order_number': order.order_number,
                'prescription_id': str(prescription.id),
                'prescription_number': prescription.prescription_number,
                'customer_id': user.id,
                'customer_email': user.email,
                'order_total': float(order.total),
                'timestamp': timezone.now().isoformat()
            }
        )


# ==========================================
# CACHING UTILITIES
# ==========================================

class RXCacheManager:
    """Manage caching for RX system"""
    
    CACHE_TIMEOUT = 300  # 5 minutes
    
    @staticmethod
    def get_verifier_stats_cache_key(verifier_id):
        """Get cache key for verifier stats"""
        return f"rx_verifier_stats_{verifier_id}"
    
    @staticmethod
    def get_dashboard_cache_key(user_role, verifier_id=None):
        """Get cache key for dashboard stats"""
        if verifier_id:
            return f"rx_dashboard_{user_role}_{verifier_id}"
        return f"rx_dashboard_{user_role}"
    
    @staticmethod
    def cache_verifier_stats(verifier_id, stats):
        """Cache verifier statistics"""
        cache_key = RXCacheManager.get_verifier_stats_cache_key(verifier_id)
        cache.set(cache_key, stats, RXCacheManager.CACHE_TIMEOUT)
    
    @staticmethod
    def get_cached_verifier_stats(verifier_id):
        """Get cached verifier statistics"""
        cache_key = RXCacheManager.get_verifier_stats_cache_key(verifier_id)
        return cache.get(cache_key)
    
    @staticmethod
    def invalidate_verifier_cache(verifier_id):
        """Invalidate verifier cache"""
        cache_key = RXCacheManager.get_verifier_stats_cache_key(verifier_id)
        cache.delete(cache_key)
    
    @staticmethod
    def cache_dashboard_stats(user_role, stats, verifier_id=None):
        """Cache dashboard statistics"""
        cache_key = RXCacheManager.get_dashboard_cache_key(user_role, verifier_id)
        cache.set(cache_key, stats, RXCacheManager.CACHE_TIMEOUT)
    
    @staticmethod
    def get_cached_dashboard_stats(user_role, verifier_id=None):
        """Get cached dashboard statistics"""
        cache_key = RXCacheManager.get_dashboard_cache_key(user_role, verifier_id)
        return cache.get(cache_key)


# ==========================================
# SECURITY ENHANCEMENTS
# ==========================================

class RXSecurityManager:
    """Security enhancements for RX system"""
    
    @staticmethod
    def verify_prescription_access(prescription, user):
        """
        Verify if user has access to prescription
        Returns: (has_access: bool, reason: str or None)
        """
        # Admin and RX verifiers have full access
        if user.role in ['admin', 'rx_verifier']:
            return True, None
        
        # Customers can only access their own prescriptions
        if user.role == 'user' and prescription.customer == user:
            return True, None
        
        return False, "Access denied"
    
    @staticmethod
    def verify_verification_permission(user):
        """
        Verify if user can perform verification actions
        Returns: (has_permission: bool, reason: str or None)
        """
        if user.role == 'rx_verifier' and user.is_active:
            return True, None
        
        if user.role == 'admin':
            return True, None
        
        return False, "RX verifier role required"
    
    @staticmethod
    def sanitize_prescription_data(data):
        """Sanitize prescription data to prevent injection attacks"""
        import bleach
        
        text_fields = ['patient_name', 'doctor_name', 'hospital_clinic', 
                      'diagnosis', 'medications_prescribed', 'customer_notes']
        
        sanitized_data = data.copy()
        for field in text_fields:
            if field in sanitized_data and sanitized_data[field]:
                # Remove any HTML tags and scripts
                sanitized_data[field] = bleach.clean(
                    str(sanitized_data[field]),
                    tags=[],
                    strip=True
                )
        
        return sanitized_data


# ==========================================
# RATE LIMITING
# ==========================================

class RXRateLimiter:
    """Rate limiting for RX operations"""
    
    @staticmethod
    def check_prescription_upload_limit(user_id):
        """
        Check if user has exceeded prescription upload limit
        Returns: (allowed: bool, retry_after: int or None)
        """
        cache_key = f"rx_upload_limit_{user_id}"
        upload_count = cache.get(cache_key, 0)
        
        MAX_UPLOADS_PER_HOUR = 10
        
        if upload_count >= MAX_UPLOADS_PER_HOUR:
            return False, 3600  # Retry after 1 hour
        
        # Increment counter
        cache.set(cache_key, upload_count + 1, 3600)
        return True, None
    
    @staticmethod
    def check_verification_action_limit(verifier_id):
        """
        Check if verifier has exceeded action limit
        Returns: (allowed: bool, retry_after: int or None)
        """
        cache_key = f"rx_verification_limit_{verifier_id}"
        action_count = cache.get(cache_key, 0)
        
        MAX_ACTIONS_PER_MINUTE = 30
        
        if action_count >= MAX_ACTIONS_PER_MINUTE:
            return False, 60  # Retry after 1 minute
        
        # Increment counter
        cache.set(cache_key, action_count + 1, 60)
        return True, None


# ==========================================
# DATA EXPORT UTILITIES
# ==========================================

class RXDataExporter:
    """Export RX data for reporting and compliance"""
    
    @staticmethod
    def export_prescription_report(start_date, end_date, format='csv'):
        """Export prescription report"""
        from .models import PrescriptionUpload
        import csv
        from io import StringIO
        
        prescriptions = PrescriptionUpload.objects.filter(
            uploaded_at__range=[start_date, end_date]
        ).select_related('customer', 'verified_by')
        
        if format == 'csv':
            output = StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                'Prescription Number', 'Upload Date', 'Customer', 'Status',
                'Verified By', 'Verification Date', 'Processing Time (hours)'
            ])
            
            # Data
            for rx in prescriptions:
                writer.writerow([
                    rx.prescription_number,
                    rx.uploaded_at.strftime('%Y-%m-%d %H:%M'),
                    rx.customer.full_name,
                    rx.verification_status,
                    rx.verified_by.full_name if rx.verified_by else 'N/A',
                    rx.verification_date.strftime('%Y-%m-%d %H:%M') if rx.verification_date else 'N/A',
                    rx.processing_time
                ])
            
            return output.getvalue()
        
        return None
