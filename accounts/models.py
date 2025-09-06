# accounts/models.py
import os
import uuid
import random
from datetime import timedelta
from PIL import Image
from io import BytesIO
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.conf import settings
from imagekitio import ImageKit
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize ImageKit
imagekit = ImageKit(
    private_key=os.environ.get('IMAGEKIT_PRIVATE_KEY'),
    public_key=os.environ.get('IMAGEKIT_PUBLIC_KEY'),
    url_endpoint=os.environ.get('IMAGEKIT_URL_ENDPOINT')
)

def upload_to_imagekit(file_bytes, filename, folder="uploads"):
    """
    Universal ImageKit upload function
    Used by all apps for consistent image handling
    Fixed to use base64 encoding for proper image uploads
    """
    try:
        import base64
        
        # Validate image using PIL
        try:
            img = Image.open(BytesIO(file_bytes))
            img.verify()
        except Exception as e:
            raise ValueError(f"Invalid image file: {str(e)}")
        
        # Ensure proper file extension
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            base_name = os.path.splitext(filename)[0]
            filename = f"{base_name}.jpg"
        
        # Create full path with folder
        full_path = f"{folder}/{filename}" if folder else filename
        
        # Convert to base64 with proper MIME type
        if ext in ['.png']:
            mime_type = "image/png"
        elif ext in ['.gif']:
            mime_type = "image/gif"
        elif ext in ['.webp']:
            mime_type = "image/webp"
        else:
            mime_type = "image/jpeg"
        
        # Encode to base64
        img_b64 = base64.b64encode(file_bytes).decode('utf-8')
        data_url = f"data:{mime_type};base64,{img_b64}"
        
        # Upload to ImageKit using base64 data URL
        upload_response = imagekit.upload_file(
            file=data_url,
            file_name=full_path
        )
        
        # Extract URL from response
        if hasattr(upload_response, 'url') and upload_response.url:
            return upload_response.url
        elif hasattr(upload_response, 'response') and upload_response.response:
            if isinstance(upload_response.response, dict):
                return upload_response.response.get('url')
        
        return None
        
    except Exception as e:
        print(f"❌ ImageKit upload error: {e}")
        return None

class ImageKitField(models.CharField):
    """
    Custom field for storing ImageKit URLs
    Similar to the Puja app implementation
    """
    description = _("ImageKit URL field")
    
    def __init__(self, verbose_name=None, **kwargs):
        kwargs.setdefault('max_length', 500)
        kwargs.setdefault('blank', True)
        kwargs.setdefault('null', True)
        super().__init__(verbose_name, **kwargs)

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        extra_fields.setdefault('role', 'user')  # Default role
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields['role'] = 'admin'
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    USER_ROLES = (
        ('user', 'User'),
        ('supplier', 'Supplier'),
        ('admin', 'Admin'),
    )
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100)
    contact = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=20, choices=USER_ROLES, default='user')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    
    # Email verification fields
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(blank=True, null=True)
    
    # Address fields for future use and COD support
    address_line_1 = models.CharField(max_length=255, blank=True, null=True)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default='India')
    
    # MedixMall mode preference
    medixmall_mode = models.BooleanField(
        default=False,
        help_text="When enabled, user only sees medicine products (MedixMall mode)"
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'contact']

    def __str__(self):
        return self.email
    
    @property
    def has_address(self):
        """Check if user has a complete address"""
        return all([
            self.address_line_1,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ])
    
    def get_full_address(self):
        """Get formatted address string"""
        address_parts = [
            self.address_line_1,
            self.address_line_2,
            self.city,
            f"{self.state} {self.postal_code}",
            self.country
        ]
        return ", ".join(filter(None, address_parts))
    
    def update_address(self, address_data):
        """Update user address from address data"""
        self.address_line_1 = address_data.get('address_line_1', self.address_line_1)
        self.address_line_2 = address_data.get('address_line_2', self.address_line_2)
        self.city = address_data.get('city', self.city)
        self.state = address_data.get('state', self.state)
        self.postal_code = address_data.get('postal_code', self.postal_code)
        self.country = address_data.get('country', self.country)
        self.save()
    
    def generate_email_verification_token(self):
        """Generate email verification token"""
        self.email_verification_token = str(uuid.uuid4())
        self.email_verification_sent_at = timezone.now()
        self.save()
        return self.email_verification_token
    
    def send_verification_email(self):
        """Send OTP-based email verification (no links)"""
        # Create or get existing email verification OTP
        from .models import OTP
        
        # Clean up old verification OTPs
        OTP.objects.filter(
            user=self,
            otp_type='email_verification',
            is_verified=False
        ).delete()
        
        # Create new OTP for email verification
        otp = OTP.objects.create(
            user=self,
            otp_type='email_verification',
            email=self.email
        )
        otp_code = otp.generate_otp()
        
        subject = 'Verify Your Email - MedixMall'
        message = f"""
Hi {self.full_name},

Thank you for registering with MedixMall!

Your email verification code is: {otp_code}

Please enter this 6-digit code to verify your email address.

This code will expire in 10 minutes.

If you did not create this account, please ignore this email.

Best regards,
MedixMall Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.email],
                fail_silently=False,
            )
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"✅ Verification OTP email sent successfully to {self.email}")
            return True, "Verification OTP email sent successfully"
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Failed to send verification OTP email to {self.email}: {str(e)}")
            return False, f"Failed to send verification email: {str(e)}"

    def send_welcome_email(self):
        """Send professional welcome notification email"""
        subject = '🎉 Welcome to MedixMall - Your Account is Ready!'
        message = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #2c5282; margin-bottom: 10px;">Welcome to MedixMall!</h1>
            <p style="color: #666; font-size: 18px;">Your trusted online pharmacy</p>
        </div>
        
        <div style="background-color: #f7fafc; padding: 25px; border-radius: 8px; margin-bottom: 25px;">
            <h2 style="color: #2c5282; margin-bottom: 15px;">Hello {self.full_name}! 👋</h2>
            <p>Thank you for joining MedixMall! We're thrilled to have you as part of our community.</p>
            
            <div style="background-color: white; padding: 15px; border-radius: 6px; margin: 20px 0;">
                <h3 style="color: #2c5282; margin-bottom: 10px;">Your Account Details:</h3>
                <p><strong>Email:</strong> {self.email}</p>
                <p><strong>Name:</strong> {self.full_name}</p>
                <p><strong>Contact:</strong> {self.contact}</p>
                <p><strong>Registration Date:</strong> {self.date_joined.strftime('%B %d, %Y')}</p>
            </div>
        </div>
        
        <div style="margin-bottom: 25px;">
            <h3 style="color: #2c5282;">What's Next?</h3>
            <ul style="color: #666;">
                <li>✅ Verify your email address using the OTP we've sent</li>
                <li>🛒 Browse our wide range of medicines and healthcare products</li>
                <li>📱 Download our mobile app for convenient shopping</li>
                <li>💊 Set up medication reminders and refill alerts</li>
                <li>🚚 Enjoy fast and secure delivery to your doorstep</li>
            </ul>
        </div>
        
        <div style="background-color: #e6fffa; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
            <h3 style="color: #2c5282; margin-bottom: 10px;">🎁 Special Welcome Offer!</h3>
            <p>Use code <strong style="color: #e53e3e; font-size: 18px;">WELCOME10</strong> and get 10% off on your first order!</p>
            <p style="font-size: 14px; color: #666;">*Valid for 30 days from registration</p>
        </div>
        
        <div style="text-align: center; margin-bottom: 25px;">
            <a href="https://backend.okpuja.in" style="background-color: #2c5282; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Start Shopping Now</a>
        </div>
        
        <div style="border-top: 1px solid #e2e8f0; padding-top: 20px; margin-top: 30px;">
            <h3 style="color: #2c5282;">Need Help?</h3>
            <p>Our customer support team is here to help you 24/7:</p>
            <ul style="color: #666;">
                <li>📧 Email: support@medixmall.com</li>
                <li>📞 Phone: +91 8002-8002-80</li>
                <li>💬 Live Chat: Available on our website</li>
            </ul>
        </div>
        
        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0; color: #666; font-size: 14px;">
            <p>Thank you for choosing MedixMall!</p>
            <p>Best regards,<br>The MedixMall Team</p>
            <p style="margin-top: 15px;">
                <a href="https://backend.okpuja.in" style="color: #2c5282;">Visit Website</a> | 
                <a href="mailto:support@medixmall.com" style="color: #2c5282;">Contact Support</a>
            </p>
        </div>
    </div>
</body>
</html>
        """
        
        # Plain text version for email clients that don't support HTML
        plain_message = f"""
Welcome to MedixMall!

Hello {self.full_name}!

Thank you for joining MedixMall! We're thrilled to have you as part of our community.

Your Account Details:
- Email: {self.email}
- Name: {self.full_name}
- Contact: {self.contact}
- Registration Date: {self.date_joined.strftime('%B %d, %Y')}

What's Next?
- Verify your email address using the OTP we've sent
- Browse our wide range of medicines and healthcare products
- Download our mobile app for convenient shopping
- Set up medication reminders and refill alerts
- Enjoy fast and secure delivery to your doorstep

Special Welcome Offer!
Use code WELCOME10 and get 10% off on your first order!
*Valid for 30 days from registration

Need Help?
Our customer support team is here to help you 24/7:
- Email: support@medixmall.com
- Phone: +91 8002-8002-80
- Live Chat: Available on our website

Thank you for choosing MedixMall!

Best regards,
The MedixMall Team

Visit Website: https://backend.okpuja.in
Contact Support: support@medixmall.com
        """
        
        try:
            from django.core.mail import EmailMultiAlternatives
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[self.email]
            )
            email.attach_alternative(message, "text/html")
            email.send()
            
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"✅ Welcome email sent successfully to {self.email}")
            return True, "Welcome email sent successfully"
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Failed to send welcome email to {self.email}: {str(e)}")
            return False, f"Failed to send welcome email: {str(e)}"


class OTP(models.Model):
    """Model to handle OTP for email and SMS verification"""
    OTP_TYPES = (
        ('email_verification', 'Email Verification'),
        ('sms_verification', 'SMS Verification'),
        ('password_reset', 'Password Reset'),
        ('login_verification', 'Login Verification'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp_type = models.CharField(max_length=20, choices=OTP_TYPES)
    otp_code = models.CharField(max_length=6)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.pk:  # Only set expiry on creation
            self.expires_at = timezone.now() + timedelta(minutes=10)  # 10 minutes expiry
        super().save(*args, **kwargs)
    
    def generate_otp(self):
        """Generate a 6-digit OTP"""
        self.otp_code = str(random.randint(100000, 999999))
        self.save()
        return self.otp_code
    
    def is_expired(self):
        """Check if OTP is expired"""
        return timezone.now() > self.expires_at
    
    def is_max_attempts_reached(self):
        """Check if maximum attempts reached"""
        return self.attempts >= self.max_attempts
    
    def can_resend(self):
        """Check if OTP can be resent (after 1 minute)"""
        if self.is_verified:
            return False, "OTP already verified"
        
        time_since_creation = timezone.now() - self.created_at
        if time_since_creation < timedelta(minutes=1):
            remaining_seconds = 60 - time_since_creation.total_seconds()
            return False, f"Please wait {int(remaining_seconds)} seconds before requesting new OTP"
        
        return True, "Can resend OTP"
    
    def verify_otp(self, provided_otp):
        """Verify provided OTP"""
        self.attempts += 1
        self.save()
        
        if self.is_expired():
            return False, "OTP has expired"
        
        if self.is_max_attempts_reached():
            return False, "Maximum attempts reached"
        
        if self.otp_code == provided_otp and not self.is_verified:
            self.is_verified = True
            self.save()
            return True, "OTP verified successfully"
        
        return False, "Invalid OTP"
    
    def send_email_otp(self):
        """Send OTP via email"""
        if not self.email:
            self.email = self.user.email
            self.save()
        
        subject = f'Your OTP - {self.get_otp_type_display()}'
        message = f"""
Hi {self.user.full_name},

Your OTP for {self.get_otp_type_display().lower()} is: {self.otp_code}

This OTP will expire in 10 minutes.

If you did not request this OTP, please ignore this email.

Best regards,
MedixMall Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.email],
                fail_silently=False,
            )
            print(f"✅ OTP email sent successfully to {self.email}")
            return True, "OTP email sent successfully"
        except Exception as e:
            print(f"❌ Failed to send OTP email to {self.email}: {str(e)}")
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"OTP email sending failed for {self.email}: {str(e)}")
            return False, f"Failed to send OTP email: {str(e)}"
    
    def send_sms_otp(self):
        """Send OTP via SMS using Twilio"""
        from django.conf import settings
        from twilio.rest import Client
        
        try:
            if not self.phone:
                self.phone = self.user.contact
                self.save()
            
            # Initialize Twilio client
            client = Client(
                settings.TWILIO_ACCOUNT_SID, 
                settings.TWILIO_AUTH_TOKEN
            )
            
            message_body = f'Your MedixMall OTP is: {self.otp_code}. Valid for 10 minutes.'
            
            message = client.messages.create(
                body=message_body,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=self.phone
            )
            
            return True, "SMS sent successfully"
            
        except Exception as e:
            return False, f"SMS sending failed: {str(e)}"


class PasswordResetToken(models.Model):
    """Model for password reset tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.pk:  # Only set expiry on creation
            self.expires_at = timezone.now() + timedelta(hours=1)  # 1 hour expiry
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if token is expired"""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if token is valid (not used and not expired)"""
        return not self.is_used and not self.is_expired()
    
    @classmethod
    def generate_for_user(cls, user):
        """Generate a new password reset token for user"""
        # Invalidate existing tokens
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Create new token
        token = str(uuid.uuid4())
        reset_token = cls.objects.create(user=user, token=token)
        return reset_token
    
    def send_reset_email(self):
        """Send password reset email"""
        subject = 'Password Reset - MedixMall'
        message = f"""
Hi {self.user.full_name},

You have requested a password reset for your MedixMall account.

Click the link below to reset your password:
https://backend.okpuja.in/api/accounts/reset-password/{self.token}/

This link will expire in 1 hour.

If you did not request this password reset, please ignore this email.

Best regards,
MedixMall Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.user.email],
                fail_silently=False,
            )
            print(f"✅ Password reset email sent successfully to {self.user.email}")
            return True, f"Password reset email sent successfully to {self.user.email}"
        except Exception as e:
            print(f"❌ Failed to send password reset email to {self.user.email}: {str(e)}")
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Password reset email sending failed for {self.user.email}: {str(e)}")
            return False, f"Failed to send password reset email: {str(e)}"