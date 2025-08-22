# accounts/models.py
import os
import uuid
from PIL import Image
from io import BytesIO
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
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

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'contact']

    def __str__(self):
        return self.email