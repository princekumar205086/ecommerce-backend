# accounts/validators.py
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class EnhancedPasswordValidator:
    """
    Enterprise-level password validation
    """
    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError(
                _("Password must be at least 8 characters long."),
                code='password_too_short',
            )
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("Password must contain at least one uppercase letter."),
                code='password_no_upper',
            )
        
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _("Password must contain at least one lowercase letter."),
                code='password_no_lower',
            )
        
        if not re.search(r'[0-9]', password):
            raise ValidationError(
                _("Password must contain at least one digit."),
                code='password_no_digit',
            )
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                _("Password must contain at least one special character."),
                code='password_no_special',
            )
        
        # Check for common patterns
        common_patterns = [
            r'123456', r'password', r'qwerty', r'abc123',
            r'admin', r'root', r'user'
        ]
        
        for pattern in common_patterns:
            if re.search(pattern, password.lower()):
                raise ValidationError(
                    _("Password contains common patterns that are not secure."),
                    code='password_too_common',
                )

    def get_help_text(self):
        return _(
            "Your password must contain at least 8 characters with uppercase, "
            "lowercase, digit and special character."
        )


def validate_indian_phone_number(value):
    """
    Validate Indian phone number format
    """
    if not value:
        return
    
    # Remove spaces and common prefixes
    cleaned = re.sub(r'[\s\-\(\)]', '', str(value))
    
    # Check for Indian phone number patterns
    patterns = [
        r'^91[6-9]\d{9}$',  # With country code
        r'^[6-9]\d{9}$',    # Without country code
    ]
    
    valid = any(re.match(pattern, cleaned) for pattern in patterns)
    
    if not valid:
        raise ValidationError(
            _('Enter a valid Indian phone number (10 digits starting with 6-9).'),
            code='invalid_phone',
        )


def validate_gst_number(value):
    """
    Validate Indian GST number format
    """
    if not value:
        return
    
    # GST format: 22AAAAA0000A1Z5
    gst_pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    
    if not re.match(gst_pattern, value.upper()):
        raise ValidationError(
            _('Enter a valid GST number (15 characters in format: 22AAAAA0000A1Z5).'),
            code='invalid_gst',
        )


def validate_pan_number(value):
    """
    Validate Indian PAN number format
    """
    if not value:
        return
    
    # PAN format: AAAAA9999A
    pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    
    if not re.match(pan_pattern, value.upper()):
        raise ValidationError(
            _('Enter a valid PAN number (10 characters in format: AAAAA9999A).'),
            code='invalid_pan',
        )


def validate_email_domain(value):
    """
    Validate email domain against blacklist
    """
    if not value:
        return
    
    # Blacklisted domains (temporary/disposable emails)
    blacklisted_domains = [
        '10minutemail.com', 'guerrillamail.com', 'mailinator.com',
        'tempmail.org', 'yopmail.com', 'temp-mail.org'
    ]
    
    domain = value.split('@')[-1].lower()
    
    if domain in blacklisted_domains:
        raise ValidationError(
            _('Please use a valid email address. Temporary email addresses are not allowed.'),
            code='disposable_email',
        )


def validate_business_name(value):
    """
    Validate business/company name
    """
    if not value:
        return
    
    # Check minimum length
    if len(value.strip()) < 2:
        raise ValidationError(
            _('Company name must be at least 2 characters long.'),
            code='name_too_short',
        )
    
    # Check for valid characters
    if not re.match(r'^[a-zA-Z0-9\s\.\-\&\']+$', value):
        raise ValidationError(
            _('Company name contains invalid characters.'),
            code='invalid_characters',
        )


def validate_postal_code(value):
    """
    Validate Indian postal code
    """
    if not value:
        return
    
    # Indian PIN code format: 6 digits
    if not re.match(r'^[1-9][0-9]{5}$', str(value)):
        raise ValidationError(
            _('Enter a valid Indian postal code (6 digits, not starting with 0).'),
            code='invalid_postal_code',
        )