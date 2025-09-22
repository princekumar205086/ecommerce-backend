# Admin Verifier Management System with Email Notifications

import logging
import uuid
import secrets
from typing import Dict, Optional
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from rest_framework import serializers
from rx_upload.models import VerifierWorkload, VerifierProfile

logger = logging.getLogger(__name__)
User = get_user_model()


class VerifierAccountCreationSerializer(serializers.Serializer):
    """Serializer for creating verifier accounts by admin"""
    
    email = serializers.EmailField(
        help_text="Email address for the new verifier account"
    )
    full_name = serializers.CharField(
        max_length=255,
        help_text="Full name of the verifier"
    )
    phone_number = serializers.CharField(
        max_length=20,
        required=False,
        help_text="Phone number of the verifier"
    )
    license_number = serializers.CharField(
        max_length=50,
        required=False,
        help_text="Professional license number"
    )
    specialization = serializers.CharField(
        max_length=100,
        required=False,
        help_text="Medical specialization or expertise area"
    )
    max_daily_capacity = serializers.IntegerField(
        default=20,
        min_value=1,
        max_value=100,
        help_text="Maximum daily prescription verification capacity"
    )
    send_welcome_email = serializers.BooleanField(
        default=True,
        help_text="Send welcome email with credentials"
    )
    department = serializers.CharField(
        max_length=100,
        required=False,
        help_text="Department or team assignment"
    )
    notes = serializers.CharField(
        max_length=500,
        required=False,
        help_text="Additional notes about the verifier"
    )
    
    def validate_email(self, value):
        """Validate email uniqueness"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists")
        return value
    
    def validate_license_number(self, value):
        """Validate license number format if provided"""
        if value:
            # Basic format validation for license numbers (can be customized)
            if len(value) < 5:
                raise serializers.ValidationError("License number must be at least 5 characters")
        return value
    
    def create(self, validated_data):
        """Create verifier account with workload setup and email notification"""
        try:
            with transaction.atomic():
                # Generate secure password
                temporary_password = self._generate_secure_password()
                
                # Create user account
                user = User.objects.create_user(
                    email=validated_data['email'],
                    password=temporary_password,
                    full_name=validated_data['full_name'],
                    role='rx_verifier',
                    contact=validated_data.get('phone_number', ''),
                    is_active=True,
                    email_verified=True  # Admin-created accounts are pre-verified
                )
                
                # Create VerifierProfile for additional fields
                verifier_profile = VerifierProfile.objects.create(
                    user=user,
                    specialization=validated_data.get('specialization', ''),
                    license_number=validated_data.get('license_number', ''),
                    verification_level=validated_data.get('verification_level', 'junior'),
                    max_daily_prescriptions=validated_data.get('max_daily_prescriptions', 50),
                    is_available=True
                )
                
                user.save()
                
                # Create verifier workload
                workload = VerifierWorkload.objects.create(
                    verifier=user,
                    max_daily_capacity=validated_data.get('max_daily_capacity', 20),
                    is_available=True
                )
                
                # Send welcome email if requested
                if validated_data.get('send_welcome_email', True):
                    email_sent = self._send_welcome_email(
                        user, 
                        temporary_password,
                        validated_data
                    )
                else:
                    email_sent = False
                
                logger.info(f"Verifier account created successfully: {user.email}")
                
                return {
                    'user': user,
                    'workload': workload,
                    'temporary_password': temporary_password,
                    'email_sent': email_sent,
                    'creation_timestamp': timezone.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to create verifier account: {e}")
            raise serializers.ValidationError(f"Account creation failed: {str(e)}")
    
    def _generate_secure_password(self) -> str:
        """Generate a secure temporary password"""
        # Generate a secure password with letters, numbers, and symbols
        password_length = 12
        password = secrets.token_urlsafe(password_length)[:password_length]
        
        # Ensure password has required complexity
        if not any(c.isupper() for c in password):
            password = password[0].upper() + password[1:]
        if not any(c.islower() for c in password):
            password = password[:-1] + 'a'
        if not any(c.isdigit() for c in password):
            password = password[:-1] + '1'
        
        return password
    
    def _send_welcome_email(self, user: User, password: str, validated_data: Dict) -> bool:
        """Send welcome email with credentials and setup instructions"""
        try:
            # Email subject
            subject = f"Welcome to RX Verification System - Your Account is Ready"
            
            # Email context
            context = {
                'user': user,
                'full_name': user.full_name or user.email,
                'email': user.email,
                'temporary_password': password,
                'login_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/rx-verifier/login",
                'system_name': 'RX Verification System',
                'support_email': getattr(settings, 'SUPPORT_EMAIL', getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@example.com')),
                'creation_date': timezone.now().strftime('%B %d, %Y'),
                'specialization': validated_data.get('specialization', ''),
                'department': validated_data.get('department', ''),
                'max_daily_capacity': validated_data.get('max_daily_capacity', 20),
                'platform_features': [
                    'Prescription verification and approval',
                    'Real-time workload management',
                    'Performance analytics and reporting',
                    'Secure file handling with ImageKit',
                    'Mobile-responsive interface',
                ],
                'security_guidelines': [
                    'Change your password immediately after first login',
                    'Use strong, unique passwords',
                    'Enable two-factor authentication if available',
                    'Log out completely when finished',
                    'Report any suspicious activities immediately',
                ],
                'next_steps': [
                    'Log in using your temporary credentials',
                    'Complete your profile setup',
                    'Review system guidelines and policies',
                    'Update your password and security settings',
                    'Familiarize yourself with the verification workflow',
                ]
            }
            
            # Render email templates
            html_content = self._render_welcome_email_html(context)
            text_content = self._render_welcome_email_text(context)
            
            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
                headers={'X-Priority': '1'}  # High priority
            )
            
            # Attach HTML version
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            email.send()
            
            logger.info(f"Welcome email sent successfully to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {user.email}: {e}")
            return False
    
    def _render_welcome_email_html(self, context: Dict) -> str:
        """Render HTML welcome email template"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to RX Verification System</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                .content { background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }
                .credentials-box { background: #e3f2fd; padding: 20px; border-left: 4px solid #2196f3; margin: 20px 0; border-radius: 5px; }
                .feature-list { background: white; padding: 20px; border-radius: 5px; margin: 15px 0; }
                .feature-list ul { margin: 0; padding-left: 20px; }
                .feature-list li { margin: 5px 0; }
                .warning-box { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 15px 0; }
                .footer { text-align: center; margin: 30px 0; color: #666; font-size: 14px; }
                .button { display: inline-block; background: #4CAF50; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; margin: 10px 0; }
                .security-highlight { color: #d32f2f; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏥 Welcome to {{ system_name }}</h1>
                <p>Your RX Verifier account has been created successfully</p>
            </div>
            
            <div class="content">
                <h2>Hello {{ full_name }},</h2>
                
                <p>Welcome to the RX Verification System! Your administrator has created your account and you're now ready to start verifying prescriptions. This platform provides a secure, efficient way to manage prescription verifications with advanced features and analytics.</p>
                
                <div class="credentials-box">
                    <h3>🔐 Your Login Credentials</h3>
                    <p><strong>Email:</strong> {{ email }}</p>
                    <p><strong>Temporary Password:</strong> <code style="background: #f1f5f9; padding: 5px 10px; border-radius: 3px; font-family: monospace;">{{ temporary_password }}</code></p>
                    <p><strong>Login URL:</strong> <a href="{{ login_url }}">{{ login_url }}</a></p>
                </div>
                
                <div class="warning-box">
                    <p class="security-highlight">⚠️ IMPORTANT SECURITY NOTICE:</p>
                    <p>Please change your password immediately after your first login. This temporary password should only be used for initial access.</p>
                </div>
                
                {% if specialization or department %}
                <div class="feature-list">
                    <h3>📋 Your Profile Information</h3>
                    {% if specialization %}<p><strong>Specialization:</strong> {{ specialization }}</p>{% endif %}
                    {% if department %}<p><strong>Department:</strong> {{ department }}</p>{% endif %}
                    <p><strong>Daily Capacity:</strong> {{ max_daily_capacity }} prescriptions</p>
                    <p><strong>Account Created:</strong> {{ creation_date }}</p>
                </div>
                {% endif %}
                
                <div class="feature-list">
                    <h3>🚀 Platform Features</h3>
                    <ul>
                        {% for feature in platform_features %}
                        <li>{{ feature }}</li>
                        {% endfor %}
                    </ul>
                </div>
                
                <div class="feature-list">
                    <h3>🔒 Security Guidelines</h3>
                    <ul>
                        {% for guideline in security_guidelines %}
                        <li>{{ guideline }}</li>
                        {% endfor %}
                    </ul>
                </div>
                
                <div class="feature-list">
                    <h3>📝 Next Steps</h3>
                    <ol>
                        {% for step in next_steps %}
                        <li>{{ step }}</li>
                        {% endfor %}
                    </ol>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{ login_url }}" class="button">Login to Your Account</a>
                </div>
                
                <p>If you have any questions or need assistance, please don't hesitate to contact our support team at <a href="mailto:{{ support_email }}">{{ support_email }}</a>.</p>
                
                <p>Thank you for joining our team!</p>
                
                <p>Best regards,<br>
                RX Verification System Team</p>
            </div>
            
            <div class="footer">
                <p>This email was sent to {{ email }} on {{ creation_date }}</p>
                <p>© 2024 RX Verification System. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        # Simple template rendering (replace with Django template engine in production)
        for key, value in context.items():
            if isinstance(value, list):
                # Handle list rendering for features, guidelines, etc.
                if key == 'platform_features':
                    features_html = ''.join([f'<li>{feature}</li>' for feature in value])
                    html_template = html_template.replace('{% for feature in platform_features %}<li>{{ feature }}</li>{% endfor %}', features_html)
                elif key == 'security_guidelines':
                    guidelines_html = ''.join([f'<li>{guideline}</li>' for guideline in value])
                    html_template = html_template.replace('{% for guideline in security_guidelines %}<li>{{ guideline }}</li>{% endfor %}', guidelines_html)
                elif key == 'next_steps':
                    steps_html = ''.join([f'<li>{step}</li>' for step in value])
                    html_template = html_template.replace('{% for step in next_steps %}<li>{{ step }}</li>{% endfor %}', steps_html)
            else:
                # Handle simple variable replacement
                html_template = html_template.replace('{{ ' + key + ' }}', str(value))
        
        # Handle conditional blocks
        if context.get('specialization') or context.get('department'):
            profile_section = """
            <div class="feature-list">
                <h3>📋 Your Profile Information</h3>
                """ + (f"<p><strong>Specialization:</strong> {context.get('specialization')}</p>" if context.get('specialization') else "") + """
                """ + (f"<p><strong>Department:</strong> {context.get('department')}</p>" if context.get('department') else "") + f"""
                <p><strong>Daily Capacity:</strong> {context.get('max_daily_capacity')} prescriptions</p>
                <p><strong>Account Created:</strong> {context.get('creation_date')}</p>
            </div>
            """
            html_template = html_template.replace('{% if specialization or department %}', '').replace('{% endif %}', '').replace('{% if specialization %}', '').replace('{% if department %}', '').replace('{% endif %}', '')
        else:
            # Remove the profile section if no specialization or department
            start_marker = '{% if specialization or department %}'
            end_marker = '{% endif %}'
            start_idx = html_template.find(start_marker)
            end_idx = html_template.find(end_marker, start_idx) + len(end_marker)
            if start_idx != -1 and end_idx != -1:
                html_template = html_template[:start_idx] + html_template[end_idx:]
        
        return html_template
    
    def _render_welcome_email_text(self, context: Dict) -> str:
        """Render plain text welcome email"""
        text_content = f"""
Welcome to {context['system_name']}!

Hello {context['full_name']},

Your RX Verifier account has been created successfully. You can now access the platform to start verifying prescriptions.

LOGIN CREDENTIALS:
==================
Email: {context['email']}
Temporary Password: {context['temporary_password']}
Login URL: {context['login_url']}

IMPORTANT SECURITY NOTICE:
=========================
Please change your password immediately after your first login. This temporary password should only be used for initial access.

YOUR PROFILE:
============
"""
        
        if context.get('specialization'):
            text_content += f"Specialization: {context['specialization']}\n"
        if context.get('department'):
            text_content += f"Department: {context['department']}\n"
        
        text_content += f"""Daily Capacity: {context['max_daily_capacity']} prescriptions
Account Created: {context['creation_date']}

PLATFORM FEATURES:
==================
"""
        
        for i, feature in enumerate(context['platform_features'], 1):
            text_content += f"{i}. {feature}\n"
        
        text_content += """
SECURITY GUIDELINES:
===================
"""
        
        for i, guideline in enumerate(context['security_guidelines'], 1):
            text_content += f"{i}. {guideline}\n"
        
        text_content += """
NEXT STEPS:
===========
"""
        
        for i, step in enumerate(context['next_steps'], 1):
            text_content += f"{i}. {step}\n"
        
        text_content += f"""
If you have any questions or need assistance, please contact our support team at {context['support_email']}.

Thank you for joining our team!

Best regards,
RX Verification System Team

---
This email was sent to {context['email']} on {context['creation_date']}
© 2024 RX Verification System. All rights reserved.
        """
        
        return text_content.strip()


class VerifierAccountManager:
    """Manager for verifier account operations"""
    
    @staticmethod
    def create_verifier_account(admin_user: User, account_data: Dict) -> Dict:
        """Create verifier account with full setup and notifications"""
        if admin_user.role != 'admin':
            raise PermissionError("Only administrators can create verifier accounts")
        
        serializer = VerifierAccountCreationSerializer(data=account_data)
        
        if serializer.is_valid():
            result = serializer.save()
            
            # Log the account creation
            logger.info(
                f"Verifier account created by admin {admin_user.email} "
                f"for {result['user'].email} at {result['creation_timestamp']}"
            )
            
            return {
                'success': True,
                'verifier': result['user'],
                'workload': result['workload'],
                'email_sent': result['email_sent'],
                'message': f"Verifier account created successfully for {result['user'].email}",
                'login_credentials': {
                    'email': result['user'].email,
                    'temporary_password': result['temporary_password']
                } if not result['email_sent'] else None
            }
        else:
            return {
                'success': False,
                'errors': serializer.errors,
                'message': "Account creation failed due to validation errors"
            }
    
    @staticmethod
    def send_credential_reminder(verifier_email: str, admin_user: User) -> Dict:
        """Send credential reminder to verifier"""
        if admin_user.role != 'admin':
            raise PermissionError("Only administrators can send credential reminders")
        
        try:
            verifier = User.objects.get(email=verifier_email, role='rx_verifier')
            
            # Generate new temporary password
            new_password = secrets.token_urlsafe(12)[:12]
            verifier.set_password(new_password)
            verifier.save()
            
            # Send reminder email (simplified version)
            subject = "RX Verification System - Password Reset"
            message = f"""
Hello {verifier.full_name},

Your administrator has reset your password for the RX Verification System.

New Temporary Password: {new_password}
Login URL: {getattr(settings, 'FRONTEND_URL', '')}/rx-verifier/login

Please change this password immediately after logging in.

Best regards,
RX Verification System Team
            """
            
            from django.core.mail import send_mail
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [verifier.email],
                fail_silently=False
            )
            
            logger.info(f"Credential reminder sent to {verifier_email} by admin {admin_user.email}")
            
            return {
                'success': True,
                'message': f"Credential reminder sent to {verifier_email}",
                'new_password': new_password
            }
            
        except User.DoesNotExist:
            return {
                'success': False,
                'message': f"Verifier with email {verifier_email} not found"
            }
        except Exception as e:
            logger.error(f"Failed to send credential reminder: {e}")
            return {
                'success': False,
                'message': f"Failed to send credential reminder: {str(e)}"
            }
    
    @staticmethod
    def get_verifier_account_stats() -> Dict:
        """Get statistics about verifier accounts"""
        total_verifiers = User.objects.filter(role='rx_verifier').count()
        active_verifiers = User.objects.filter(role='rx_verifier', is_active=True).count()
        available_verifiers = VerifierWorkload.objects.filter(is_available=True).count()
        
        return {
            'total_verifiers': total_verifiers,
            'active_verifiers': active_verifiers,
            'available_verifiers': available_verifiers,
            'inactive_verifiers': total_verifiers - active_verifiers,
            'utilization_rate': round((available_verifiers / max(total_verifiers, 1)) * 100, 2)
        }