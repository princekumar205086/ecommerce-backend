# accounts/utils.py
import hashlib
import hmac
import secrets
import string
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
import logging

logger = logging.getLogger('accounts.utils')

def generate_secure_token(length=32):
    """Generate cryptographically secure random token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_otp(length=6):
    """Generate numeric OTP"""
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def hash_sensitive_data(data, salt=None):
    """Hash sensitive data with salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    
    combined = f"{data}{salt}".encode('utf-8')
    hashed = hashlib.sha256(combined).hexdigest()
    return f"{salt}:{hashed}"


def verify_sensitive_data(data, stored_hash):
    """Verify sensitive data against stored hash"""
    try:
        salt, hash_value = stored_hash.split(':', 1)
        combined = f"{data}{salt}".encode('utf-8')
        computed_hash = hashlib.sha256(combined).hexdigest()
        return hmac.compare_digest(hash_value, computed_hash)
    except (ValueError, AttributeError):
        return False


def create_audit_log(user, action, resource, details=None, ip_address=None):
    """Create audit log entry"""
    from .models import AuditLog
    
    try:
        AuditLog.objects.create(
            user=user,
            action=action,
            resource=resource,
            details=details or {},
            ip_address=ip_address,
            timestamp=timezone.now()
        )
    except Exception as e:
        logger.error(f"Failed to create audit log: {str(e)}")


def get_client_ip(request):
    """Extract client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def is_suspicious_activity(user, action, ip_address=None):
    """Detect suspicious user activity"""
    cache_key = f"activity:{user.id}:{action}"
    recent_attempts = cache.get(cache_key, 0)
    
    # Define thresholds for different actions
    thresholds = {
        'login_attempt': 5,
        'otp_request': 3,
        'password_reset': 3,
        'profile_update': 10
    }
    
    threshold = thresholds.get(action, 5)
    
    if recent_attempts >= threshold:
        logger.warning(
            f"SUSPICIOUS_ACTIVITY: User {user.email} exceeded {action} threshold "
            f"({recent_attempts}/{threshold}) from IP {ip_address}"
        )
        return True
    
    # Increment counter
    cache.set(cache_key, recent_attempts + 1, 3600)  # 1 hour window
    return False


def clean_phone_number(phone):
    """Clean and validate phone number"""
    if not phone:
        return None
    
    # Remove all non-digits
    cleaned = ''.join(filter(str.isdigit, phone))
    
    # Handle Indian phone numbers
    if len(cleaned) == 10 and cleaned[0] in '6789':
        return f"+91{cleaned}"
    elif len(cleaned) == 12 and cleaned.startswith('91'):
        return f"+{cleaned}"
    elif len(cleaned) == 13 and cleaned.startswith('91'):
        return f"+91{cleaned[2:]}"
    
    return cleaned if len(cleaned) >= 10 else None


def validate_file_upload(file, allowed_types=None, max_size_mb=5):
    """Validate file upload"""
    allowed_types = allowed_types or ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']
    max_size = max_size_mb * 1024 * 1024  # Convert to bytes
    
    errors = []
    
    if file.size > max_size:
        errors.append(f"File size exceeds {max_size_mb}MB limit")
    
    if file.content_type not in allowed_types:
        errors.append(f"File type not allowed. Allowed types: {', '.join(allowed_types)}")
    
    # Check for malicious content
    if hasattr(file, 'read'):
        file.seek(0)
        content = file.read(1024)  # Read first 1KB
        file.seek(0)  # Reset file pointer
        
        # Basic malware signature detection
        malicious_signatures = [b'<?php', b'<script', b'javascript:']
        for signature in malicious_signatures:
            if signature in content.lower():
                errors.append("File contains potentially malicious content")
                break
    
    return errors


def mask_sensitive_data(data, mask_char='*', visible_chars=3):
    """Mask sensitive data for logging"""
    if not data or len(data) <= visible_chars:
        return mask_char * len(data) if data else ''
    
    return data[:visible_chars] + mask_char * (len(data) - visible_chars)


def generate_username_from_email(email):
    """Generate username from email"""
    base_username = email.split('@')[0].lower()
    # Remove special characters
    username = ''.join(c for c in base_username if c.isalnum() or c in '-_')
    return username[:30]  # Limit length


def calculate_password_strength(password):
    """Calculate password strength score (0-100)"""
    score = 0
    
    # Length score
    if len(password) >= 8:
        score += 20
    if len(password) >= 12:
        score += 10
    
    # Character variety
    if any(c.islower() for c in password):
        score += 15
    if any(c.isupper() for c in password):
        score += 15
    if any(c.isdigit() for c in password):
        score += 15
    if any(c in '!@#$%^&*(),.?":{}|<>' for c in password):
        score += 25
    
    return min(score, 100)


def get_password_strength_label(score):
    """Get password strength label"""
    if score < 30:
        return 'Weak'
    elif score < 60:
        return 'Fair'
    elif score < 80:
        return 'Good'
    else:
        return 'Strong'


def send_admin_notification(subject, message, level='info'):
    """Send notification to admin users"""
    from django.core.mail import send_mail
    from .models import User
    
    try:
        admin_emails = list(
            User.objects.filter(
                role='admin', 
                is_active=True
            ).values_list('email', flat=True)
        )
        
        if admin_emails:
            send_mail(
                subject=f"[MedixMall Admin] {subject}",
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=admin_emails,
                fail_silently=True
            )
            
        logger.info(f"Admin notification sent: {subject}")
    except Exception as e:
        logger.error(f"Failed to send admin notification: {str(e)}")


def check_account_security(user):
    """Comprehensive account security check"""
    security_issues = []
    
    # Check password age (if we track it)
    if hasattr(user, 'password_changed_at'):
        if user.password_changed_at:
            days_since_change = (timezone.now() - user.password_changed_at).days
            if days_since_change > 90:
                security_issues.append('Password not changed in 90+ days')
    
    # Check for suspicious activity
    cache_key = f"failed_logins:{user.email}"
    failed_attempts = cache.get(cache_key, 0)
    if failed_attempts > 3:
        security_issues.append(f'Multiple failed login attempts ({failed_attempts})')
    
    # Check email verification
    if not user.email_verified:
        security_issues.append('Email not verified')
    
    # Check for incomplete profile
    if not user.contact:
        security_issues.append('Contact number not provided')
    
    return {
        'is_secure': len(security_issues) == 0,
        'issues': security_issues,
        'score': max(0, 100 - (len(security_issues) * 20))
    }