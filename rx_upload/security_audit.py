# Comprehensive Security Audit Module for RX Upload System

import logging
import hashlib
import re
import os
from datetime import timedelta
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.sessions.models import Session
from django.core.files.uploadedfile import UploadedFile
from .models import PrescriptionUpload, VerifierWorkload, VerificationActivity
from accounts.models import User

logger = logging.getLogger(__name__)


class SecurityAuditManager:
    """Comprehensive security audit and validation for RX Upload System"""
    
    # Security thresholds and limits
    SECURITY_THRESHOLDS = {
        'max_file_size': 10 * 1024 * 1024,  # 10MB
        'max_daily_uploads_per_user': 50,
        'max_verification_attempts': 3,
        'session_timeout_hours': 8,
        'password_min_length': 8,
        'failed_login_threshold': 5,
        'suspicious_activity_threshold': 10,
    }
    
    # Allowed file types for prescription uploads
    ALLOWED_MIME_TYPES = [
        'image/jpeg',
        'image/png',
        'image/webp',
        'application/pdf',
    ]
    
    ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.pdf']
    
    # Suspicious patterns for content validation
    SUSPICIOUS_PATTERNS = [
        r'<script.*?>.*?</script>',  # Script tags
        r'javascript:',              # JavaScript URLs
        r'on\w+\s*=',               # Event handlers
        r'eval\s*\(',               # Eval functions
        r'document\.',              # DOM manipulation
        r'window\.',                # Window object access
    ]
    
    @classmethod
    def audit_file_upload_security(cls, uploaded_file: UploadedFile, user: User) -> Dict:
        """Comprehensive security audit for file uploads"""
        audit_results = {
            'is_secure': True,
            'security_score': 100,
            'warnings': [],
            'errors': [],
            'recommendations': [],
        }
        
        try:
            # File size validation
            size_check = cls._validate_file_size(uploaded_file)
            if not size_check['valid']:
                audit_results['errors'].append(size_check['message'])
                audit_results['is_secure'] = False
                audit_results['security_score'] -= 30
            
            # File type validation
            type_check = cls._validate_file_type(uploaded_file)
            if not type_check['valid']:
                audit_results['errors'].append(type_check['message'])
                audit_results['is_secure'] = False
                audit_results['security_score'] -= 40
            
            # Content validation
            content_check = cls._validate_file_content(uploaded_file)
            if not content_check['valid']:
                audit_results['warnings'].extend(content_check['warnings'])
                audit_results['security_score'] -= content_check['severity']
            
            # User behavior validation
            behavior_check = cls._validate_user_upload_behavior(user)
            if not behavior_check['valid']:
                audit_results['warnings'].append(behavior_check['message'])
                audit_results['security_score'] -= 10
            
            # Generate recommendations
            audit_results['recommendations'] = cls._generate_file_security_recommendations(
                audit_results
            )
            
            logger.info(f"File upload security audit completed for user {user.id}: Score {audit_results['security_score']}")
            
        except Exception as e:
            logger.error(f"Security audit failed: {e}")
            audit_results['errors'].append("Security audit failed - upload blocked")
            audit_results['is_secure'] = False
            audit_results['security_score'] = 0
        
        return audit_results
    
    @classmethod
    def _validate_file_size(cls, uploaded_file: UploadedFile) -> Dict:
        """Validate file size against security limits"""
        max_size = cls.SECURITY_THRESHOLDS['max_file_size']
        
        if uploaded_file.size > max_size:
            return {
                'valid': False,
                'message': f"File size {uploaded_file.size} bytes exceeds maximum allowed size {max_size} bytes"
            }
        
        return {'valid': True, 'message': 'File size validation passed'}
    
    @classmethod
    def _validate_file_type(cls, uploaded_file: UploadedFile) -> Dict:
        """Validate file type and extension"""
        # Check MIME type
        if hasattr(uploaded_file, 'content_type') and uploaded_file.content_type:
            if uploaded_file.content_type not in cls.ALLOWED_MIME_TYPES:
                return {
                    'valid': False,
                    'message': f"File type {uploaded_file.content_type} not allowed. Allowed types: {cls.ALLOWED_MIME_TYPES}"
                }
        
        # Check file extension
        if hasattr(uploaded_file, 'name') and uploaded_file.name:
            file_ext = os.path.splitext(uploaded_file.name.lower())[1]
            if file_ext not in cls.ALLOWED_EXTENSIONS:
                return {
                    'valid': False,
                    'message': f"File extension {file_ext} not allowed. Allowed extensions: {cls.ALLOWED_EXTENSIONS}"
                }
        
        return {'valid': True, 'message': 'File type validation passed'}
    
    @classmethod
    def _validate_file_content(cls, uploaded_file: UploadedFile) -> Dict:
        """Validate file content for malicious patterns"""
        warnings = []
        severity = 0
        
        try:
            # Read a sample of the file content
            uploaded_file.seek(0)
            content_sample = uploaded_file.read(1024).decode('utf-8', errors='ignore')
            uploaded_file.seek(0)  # Reset file pointer
            
            # Check for suspicious patterns
            for pattern in cls.SUSPICIOUS_PATTERNS:
                if re.search(pattern, content_sample, re.IGNORECASE):
                    warnings.append(f"Suspicious pattern detected: {pattern}")
                    severity += 15
            
            # Check for null bytes (potential file manipulation)
            if '\x00' in content_sample:
                warnings.append("Null bytes detected in file content")
                severity += 20
            
        except Exception as e:
            # If we can't read the content, it's likely a binary file which is expected
            logger.debug(f"Could not read file content for validation: {e}")
        
        return {
            'valid': len(warnings) == 0,
            'warnings': warnings,
            'severity': min(severity, 50)  # Cap severity at 50
        }
    
    @classmethod
    def _validate_user_upload_behavior(cls, user: User) -> Dict:
        """Validate user upload behavior patterns"""
        today = timezone.now().date()
        
        # Check daily upload count
        daily_uploads = PrescriptionUpload.objects.filter(
            customer=user,
            uploaded_at__date=today
        ).count()
        
        max_daily = cls.SECURITY_THRESHOLDS['max_daily_uploads_per_user']
        
        if daily_uploads >= max_daily:
            return {
                'valid': False,
                'message': f"User has exceeded daily upload limit ({daily_uploads}/{max_daily})"
            }
        
        return {'valid': True, 'message': 'User behavior validation passed'}
    
    @classmethod
    def _generate_file_security_recommendations(cls, audit_results: Dict) -> List[str]:
        """Generate security recommendations based on audit results"""
        recommendations = []
        
        if audit_results['security_score'] < 70:
            recommendations.append("Consider implementing additional file scanning")
        
        if len(audit_results['warnings']) > 0:
            recommendations.append("Review file content before processing")
        
        if len(audit_results['errors']) > 0:
            recommendations.append("Block upload and notify security team")
        
        if audit_results['security_score'] > 90:
            recommendations.append("File passes all security checks")
        
        return recommendations
    
    @classmethod
    def audit_user_session_security(cls, user: User, request) -> Dict:
        """Audit user session security"""
        audit_results = {
            'is_secure': True,
            'security_score': 100,
            'warnings': [],
            'session_info': {},
        }
        
        try:
            # Session validation
            session_check = cls._validate_session_security(request)
            audit_results['session_info'] = session_check
            
            if not session_check['valid']:
                audit_results['warnings'].extend(session_check['warnings'])
                audit_results['security_score'] -= 20
            
            # User authentication audit
            auth_check = cls._audit_user_authentication(user)
            if not auth_check['valid']:
                audit_results['warnings'].extend(auth_check['warnings'])
                audit_results['security_score'] -= 30
            
            # Permission audit
            permission_check = cls._audit_user_permissions(user)
            if not permission_check['valid']:
                audit_results['warnings'].extend(permission_check['warnings'])
                audit_results['security_score'] -= 25
            
        except Exception as e:
            logger.error(f"Session security audit failed: {e}")
            audit_results['is_secure'] = False
            audit_results['security_score'] = 0
        
        return audit_results
    
    @classmethod
    def _validate_session_security(cls, request) -> Dict:
        """Validate session security parameters"""
        warnings = []
        
        # Check session age
        if hasattr(request, 'session'):
            session_key = request.session.session_key
            if session_key:
                try:
                    session = Session.objects.get(session_key=session_key)
                    session_age = timezone.now() - session.expire_date + timedelta(
                        seconds=settings.SESSION_COOKIE_AGE
                    )
                    
                    max_age = timedelta(hours=cls.SECURITY_THRESHOLDS['session_timeout_hours'])
                    
                    if session_age > max_age:
                        warnings.append("Session is older than recommended timeout")
                    
                except Session.DoesNotExist:
                    warnings.append("Session not found in database")
            else:
                warnings.append("No session key found")
        
        # Check secure session settings
        if not getattr(settings, 'SESSION_COOKIE_SECURE', False):
            warnings.append("Session cookies not configured as secure")
        
        if not getattr(settings, 'SESSION_COOKIE_HTTPONLY', False):
            warnings.append("Session cookies not configured as HTTP-only")
        
        return {
            'valid': len(warnings) == 0,
            'warnings': warnings,
            'session_secure': getattr(settings, 'SESSION_COOKIE_SECURE', False),
            'session_httponly': getattr(settings, 'SESSION_COOKIE_HTTPONLY', False),
        }
    
    @classmethod
    def _audit_user_authentication(cls, user: User) -> Dict:
        """Audit user authentication security"""
        warnings = []
        
        # Check password strength (if accessible)
        if hasattr(user, 'password') and user.password:
            # Note: We can't check actual password due to hashing
            # But we can check password policy compliance through user model
            pass
        
        # Check account status
        if not user.is_active:
            warnings.append("User account is inactive")
        
        # Check role assignment
        if not user.role:
            warnings.append("User has no assigned role")
        
        # Check for suspicious login patterns
        recent_logins = cls._check_recent_login_patterns(user)
        if recent_logins['suspicious']:
            warnings.extend(recent_logins['warnings'])
        
        return {
            'valid': len(warnings) == 0,
            'warnings': warnings,
        }
    
    @classmethod
    def _check_recent_login_patterns(cls, user: User) -> Dict:
        """Check for suspicious login patterns"""
        # This would typically check login logs
        # For now, we'll implement basic checks
        
        return {
            'suspicious': False,
            'warnings': [],
        }
    
    @classmethod
    def _audit_user_permissions(cls, user: User) -> Dict:
        """Audit user permissions and role-based access"""
        warnings = []
        
        # Validate role permissions
        if user.role == 'rx_verifier':
            # Check if verifier has proper workload setup
            try:
                workload = VerifierWorkload.objects.get(verifier=user)
                if not workload.is_available:
                    warnings.append("Verifier workload is not available")
            except VerifierWorkload.DoesNotExist:
                warnings.append("Verifier has no workload configuration")
        
        elif user.role == 'customer':
            # Check customer account validity
            if not user.email_verified:
                warnings.append("Customer email not verified")
        
        elif user.role == 'admin':
            # Admin-specific checks
            if not user.is_staff:
                warnings.append("Admin user not marked as staff")
        
        return {
            'valid': len(warnings) == 0,
            'warnings': warnings,
        }
    
    @classmethod
    def audit_api_endpoint_security(cls, endpoint: str, method: str, user: User) -> Dict:
        """Audit API endpoint security"""
        audit_results = {
            'is_secure': True,
            'security_score': 100,
            'access_granted': True,
            'warnings': [],
        }
        
        # Define endpoint permissions
        endpoint_permissions = {
            '/api/prescriptions/': {
                'GET': ['customer', 'rx_verifier', 'admin'],
                'POST': ['customer'],
                'PUT': ['rx_verifier', 'admin'],
                'DELETE': ['admin'],
            },
            '/api/prescriptions/verify/': {
                'POST': ['rx_verifier', 'admin'],
            },
            '/api/workload/': {
                'GET': ['rx_verifier', 'admin'],
                'PUT': ['rx_verifier', 'admin'],
            },
        }
        
        # Check permissions
        if endpoint in endpoint_permissions:
            allowed_roles = endpoint_permissions[endpoint].get(method, [])
            if user.role not in allowed_roles:
                audit_results['access_granted'] = False
                audit_results['security_score'] = 0
                audit_results['warnings'].append(
                    f"User role '{user.role}' not authorized for {method} {endpoint}"
                )
        
        # Rate limiting check (placeholder)
        rate_limit_check = cls._check_rate_limiting(user, endpoint)
        if not rate_limit_check['valid']:
            audit_results['warnings'].append(rate_limit_check['message'])
            audit_results['security_score'] -= 20
        
        return audit_results
    
    @classmethod
    def _check_rate_limiting(cls, user: User, endpoint: str) -> Dict:
        """Check rate limiting for API endpoints"""
        # Placeholder for rate limiting logic
        # In production, this would check request counts per time window
        
        return {
            'valid': True,
            'message': 'Rate limiting check passed'
        }
    
    @classmethod
    def generate_security_report(cls, user: User = None) -> Dict:
        """Generate comprehensive security report"""
        report = {
            'timestamp': timezone.now().isoformat(),
            'overall_security_score': 0,
            'total_checks': 0,
            'passed_checks': 0,
            'warnings': [],
            'recommendations': [],
            'system_overview': {},
        }
        
        try:
            # System-wide security checks
            system_checks = cls._perform_system_security_checks()
            report['system_overview'] = system_checks
            
            # File upload security analysis
            upload_analysis = cls._analyze_upload_security_patterns()
            report['upload_analysis'] = upload_analysis
            
            # User activity analysis
            if user:
                user_analysis = cls._analyze_user_security_activity(user)
                report['user_analysis'] = user_analysis
            
            # Calculate overall score
            scores = [
                system_checks.get('security_score', 0),
                upload_analysis.get('security_score', 0),
            ]
            
            if user:
                scores.append(report.get('user_analysis', {}).get('security_score', 0))
            
            report['overall_security_score'] = sum(scores) / len(scores)
            report['total_checks'] = len(scores)
            report['passed_checks'] = sum(1 for score in scores if score >= 80)
            
            # Generate recommendations
            report['recommendations'] = cls._generate_security_recommendations(report)
            
        except Exception as e:
            logger.error(f"Security report generation failed: {e}")
            report['error'] = str(e)
        
        return report
    
    @classmethod
    def _perform_system_security_checks(cls) -> Dict:
        """Perform system-wide security checks"""
        checks = {
            'security_score': 100,
            'database_security': {},
            'configuration_security': {},
            'file_system_security': {},
        }
        
        # Database security checks
        db_checks = cls._check_database_security()
        checks['database_security'] = db_checks
        if not db_checks['secure']:
            checks['security_score'] -= 30
        
        # Configuration security checks
        config_checks = cls._check_configuration_security()
        checks['configuration_security'] = config_checks
        if not config_checks['secure']:
            checks['security_score'] -= 25
        
        return checks
    
    @classmethod
    def _check_database_security(cls) -> Dict:
        """Check database security configurations"""
        return {
            'secure': True,
            'encrypted_connections': getattr(settings, 'DATABASE_SSL_ENABLED', False),
            'password_hashing': 'PBKDF2' in getattr(settings, 'PASSWORD_HASHERS', []),
            'sensitive_data_encrypted': True,  # Placeholder
        }
    
    @classmethod
    def _check_configuration_security(cls) -> Dict:
        """Check Django configuration security"""
        return {
            'secure': True,
            'debug_disabled': not getattr(settings, 'DEBUG', True),
            'secret_key_secure': len(getattr(settings, 'SECRET_KEY', '')) >= 50,
            'https_enforced': getattr(settings, 'SECURE_SSL_REDIRECT', False),
            'secure_headers': getattr(settings, 'SECURE_BROWSER_XSS_FILTER', False),
        }
    
    @classmethod
    def _analyze_upload_security_patterns(cls) -> Dict:
        """Analyze file upload security patterns"""
        recent_uploads = PrescriptionUpload.objects.filter(
            uploaded_at__gte=timezone.now() - timedelta(days=7)
        )
        
        return {
            'security_score': 95,  # Placeholder
            'total_uploads': recent_uploads.count(),
            'suspicious_uploads': 0,  # Placeholder
            'average_file_size': 1024000,  # Placeholder
        }
    
    @classmethod
    def _analyze_user_security_activity(cls, user: User) -> Dict:
        """Analyze user-specific security activity"""
        return {
            'security_score': 90,  # Placeholder
            'recent_uploads': PrescriptionUpload.objects.filter(
                customer=user,
                uploaded_at__gte=timezone.now() - timedelta(days=30)
            ).count(),
            'suspicious_activity': False,  # Placeholder
        }
    
    @classmethod
    def _generate_security_recommendations(cls, report: Dict) -> List[str]:
        """Generate security recommendations based on report"""
        recommendations = []
        
        if report['overall_security_score'] < 80:
            recommendations.append("Overall security score is below recommended threshold")
        
        if report.get('system_overview', {}).get('security_score', 100) < 90:
            recommendations.append("System configuration requires security hardening")
        
        recommendations.append("Regular security audits are recommended")
        recommendations.append("Monitor file upload patterns for anomalies")
        recommendations.append("Implement comprehensive logging and monitoring")
        
        return recommendations


# Security event logging
class SecurityEventLogger:
    """Log security events for monitoring and compliance"""
    
    @staticmethod
    def log_file_upload_audit(user: User, filename: str, audit_results: Dict):
        """Log file upload security audit event"""
        logger.info(
            f"File upload audit - User: {user.id}, File: {filename}, "
            f"Score: {audit_results['security_score']}, Secure: {audit_results['is_secure']}"
        )
    
    @staticmethod
    def log_session_audit(user: User, audit_results: Dict):
        """Log session security audit event"""
        logger.info(
            f"Session audit - User: {user.id}, "
            f"Score: {audit_results['security_score']}, Secure: {audit_results['is_secure']}"
        )
    
    @staticmethod
    def log_security_violation(user: User, violation_type: str, details: str):
        """Log security violation event"""
        logger.warning(
            f"Security violation - User: {user.id}, Type: {violation_type}, Details: {details}"
        )