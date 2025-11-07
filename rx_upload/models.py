# rx_upload/models.py
import os
import uuid
from datetime import datetime
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from accounts.models import ImageKitField, upload_to_imagekit
from io import BytesIO

User = get_user_model()


class PrescriptionUpload(models.Model):
    """Model for storing prescription uploads from customers"""
    VERIFICATION_STATUS = (
        ('pending', 'Pending Verification'),
        ('in_review', 'In Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('clarification_needed', 'Clarification Needed'),
    )
    
    PRESCRIPTION_TYPE = (
        ('image', 'Image Upload'),
        ('pdf', 'PDF Document'),
        ('camera', 'Camera Capture'),
    )
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prescription_uploads')
    prescription_number = models.CharField(max_length=50, unique=True, blank=True)
    
    # Prescription Details
    doctor_name = models.CharField(max_length=200, blank=True, null=True)
    doctor_license = models.CharField(max_length=100, blank=True, null=True)
    hospital_clinic = models.CharField(max_length=200, blank=True, null=True)
    patient_name = models.CharField(max_length=200, blank=True, null=True)
    patient_age = models.PositiveIntegerField(blank=True, null=True)
    patient_gender = models.CharField(
        max_length=10,
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        blank=True,
        null=True
    )
    
    # Upload Information
    prescription_type = models.CharField(max_length=20, choices=PRESCRIPTION_TYPE, default='image')
    prescription_image = ImageKitField(verbose_name="Prescription Image", blank=True, null=True)
    prescription_file_url = models.URLField(blank=True, null=True)  # For external file storage
    original_filename = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.PositiveIntegerField(blank=True, null=True, help_text="File size in bytes")
    
    # Medical Information
    diagnosis = models.TextField(blank=True, null=True, help_text="Medical diagnosis from prescription")
    medications_prescribed = models.TextField(blank=True, null=True, help_text="List of prescribed medications")
    dosage_instructions = models.TextField(blank=True, null=True, help_text="Dosage and usage instructions")
    prescription_date = models.DateField(blank=True, null=True)
    prescription_valid_until = models.DateField(blank=True, null=True)
    
    # Verification Status
    verification_status = models.CharField(max_length=25, choices=VERIFICATION_STATUS, default='pending')
    verified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='verified_prescriptions',
        limit_choices_to={'role': 'rx_verifier'}
    )
    verification_date = models.DateTimeField(blank=True, null=True)
    verification_notes = models.TextField(blank=True, null=True, help_text="Notes from verifier")
    
    # Customer Communication
    customer_notes = models.TextField(blank=True, null=True, help_text="Additional notes from customer")
    clarification_requested = models.TextField(blank=True, null=True, help_text="Clarification requested from customer")
    customer_response = models.TextField(blank=True, null=True, help_text="Customer response to clarification")
    
    # Quality Control
    image_quality_score = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True, help_text="Image quality score (0-10)")
    legibility_score = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True, help_text="Text legibility score (0-10)")
    completeness_score = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True, help_text="Information completeness score (0-10)")
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Priority and Urgency
    is_urgent = models.BooleanField(default=False, help_text="Mark as urgent for priority verification")
    priority_level = models.PositiveIntegerField(
        default=3,
        choices=[(1, 'Low'), (2, 'Medium'), (3, 'High'), (4, 'Critical')],
        help_text="Verification priority level"
    )
    
    # Contact Information
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    alternative_contact = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['verification_status']),
            models.Index(fields=['uploaded_at']),
            models.Index(fields=['customer']),
            models.Index(fields=['verified_by']),
            models.Index(fields=['is_urgent', '-uploaded_at']),
        ]
    
    def __str__(self):
        return f"Prescription {self.prescription_number} - {self.customer.full_name}"
    
    def save(self, *args, **kwargs):
        if not self.prescription_number:
            self.prescription_number = self.generate_prescription_number()
        super().save(*args, **kwargs)
    
    def generate_prescription_number(self):
        """Generate unique prescription number"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = str(uuid.uuid4())[:8].upper()
        return f"RX{timestamp}{random_suffix}"
    
    def upload_prescription_to_imagekit(self, file_data, filename):
        """Upload prescription image to ImageKit"""
        try:
            if isinstance(file_data, (bytes, bytearray)):
                file_bytes = file_data
            else:
                # If it's a file object, read the content
                file_bytes = file_data.read()
            
            # Create folder structure for prescriptions
            folder = f"prescriptions/{self.customer.id}/{datetime.now().strftime('%Y/%m')}"
            
            # Upload to ImageKit
            url = upload_to_imagekit(file_bytes, filename, folder)
            
            if url:
                self.prescription_image = url
                self.original_filename = filename
                self.file_size = len(file_bytes)
                self.save()
                return True, url
            else:
                return False, "Failed to upload to ImageKit"
                
        except Exception as e:
            return False, f"Upload error: {str(e)}"
    
    @property
    def can_be_verified(self):
        """Check if prescription can be verified"""
        return self.verification_status in ['pending', 'clarification_needed']
    
    @property
    def is_overdue(self):
        """Check if verification is overdue (more than 24 hours)"""
        if self.verification_status in ['approved', 'rejected']:
            return False
        
        time_diff = timezone.now() - self.uploaded_at
        return time_diff.total_seconds() > 86400  # 24 hours
    
    @property
    def processing_time(self):
        """Get processing time in hours"""
        if self.verification_date:
            time_diff = self.verification_date - self.uploaded_at
            return round(time_diff.total_seconds() / 3600, 2)
        else:
            time_diff = timezone.now() - self.uploaded_at
            return round(time_diff.total_seconds() / 3600, 2)
    
    def assign_to_verifier(self, verifier):
        """Assign prescription to a verifier"""
        if verifier.role != 'rx_verifier':
            return False, "User is not an RX verifier"
        
        self.verified_by = verifier
        self.verification_status = 'in_review'
        self.save()
        return True, f"Assigned to {verifier.full_name}"
    
    def approve_prescription(self, verifier, notes=""):
        """Approve prescription"""
        if verifier.role != 'rx_verifier':
            return False, "Only RX verifiers can approve prescriptions"
        
        self.verification_status = 'approved'
        self.verified_by = verifier
        self.verification_date = timezone.now()
        self.verification_notes = notes
        self.save()
        
        # Update verifier workload
        if hasattr(verifier, 'workload_stats'):
            workload = verifier.workload_stats
            workload.total_verified += 1
            workload.total_approved += 1
            workload.save()
        
        # Send notification to customer
        self.send_verification_notification()
        
        return True, "Prescription approved successfully"
    
    def reject_prescription(self, verifier, notes=""):
        """Reject prescription"""
        if verifier.role != 'rx_verifier':
            return False, "Only RX verifiers can reject prescriptions"
        
        self.verification_status = 'rejected'
        self.verified_by = verifier
        self.verification_date = timezone.now()
        self.verification_notes = notes
        self.save()
        
        # Update verifier workload
        if hasattr(verifier, 'workload_stats'):
            workload = verifier.workload_stats
            workload.total_verified += 1
            workload.total_rejected += 1
            workload.save()
        
        # Send notification to customer
        self.send_verification_notification()
        
        return True, "Prescription rejected"
    
    def request_clarification(self, verifier, clarification_message):
        """Request clarification from customer"""
        if verifier.role != 'rx_verifier':
            return False, "Only RX verifiers can request clarification"
        
        self.verification_status = 'clarification_needed'
        self.verified_by = verifier
        self.clarification_requested = clarification_message
        self.verification_date = timezone.now()
        self.save()
        
        # Send clarification request to customer
        self.send_clarification_request()
        
        return True, "Clarification requested from customer"
    
    def send_verification_notification(self):
        """Send verification status notification to customer"""
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = f"Prescription Verification Update - {self.prescription_number}"
        
        if self.verification_status == 'approved':
            message = f"""
Dear {self.customer.full_name},

Your prescription (#{self.prescription_number}) has been approved by our medical team.

Status: ✅ APPROVED
Verified by: {self.verified_by.full_name}
Verification Date: {self.verification_date.strftime('%B %d, %Y at %I:%M %p')}

You can now proceed with your medication order.

{f'Verifier Notes: {self.verification_notes}' if self.verification_notes else ''}

Thank you for choosing MedixMall!

Best regards,
MedixMall Medical Team
            """
        else:  # rejected
            message = f"""
Dear {self.customer.full_name},

Unfortunately, your prescription (#{self.prescription_number}) could not be approved.

Status: ❌ REJECTED
Verified by: {self.verified_by.full_name}
Verification Date: {self.verification_date.strftime('%B %d, %Y at %I:%M %p')}

Reason: {self.verification_notes or 'Please contact our support team for details.'}

You may upload a new, clearer prescription or contact our support team.

Support: rx-support@medixmall.com
Phone: +91 8002-8002-80

Best regards,
MedixMall Medical Team
            """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.customer.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Failed to send verification notification: {str(e)}")
            return False
    
    def send_clarification_request(self):
        """Send clarification request to customer"""
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = f"Clarification Needed - Prescription {self.prescription_number}"
        message = f"""
Dear {self.customer.full_name},

Our medical team needs additional clarification for your prescription (#{self.prescription_number}).

Status: ⏳ CLARIFICATION NEEDED
Reviewed by: {self.verified_by.full_name}

Request:
{self.clarification_requested}

Please provide the requested information by:
1. Replying to this email with details
2. Calling our support: +91 8002-8002-80
3. Uploading additional documents if needed

We'll review your response and update the verification status accordingly.

Thank you for your cooperation!

Best regards,
MedixMall Medical Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.customer.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Failed to send clarification request: {str(e)}")
            return False


class VerifierProfile(models.Model):
    """Extended profile for RX verifiers"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verifier_profile')
    
    # Professional Information
    specialization = models.CharField(max_length=100, blank=True, null=True, 
                                    help_text="Medical specialization (e.g., General Medicine, Cardiology)")
    license_number = models.CharField(max_length=50, unique=True, 
                                    help_text="Medical license number")
    verification_level = models.CharField(max_length=20, 
                                        choices=[
                                            ('junior', 'Junior Verifier'),
                                            ('senior', 'Senior Verifier'),
                                            ('specialist', 'Specialist Verifier'),
                                            ('supervisor', 'Supervisor')
                                        ], 
                                        default='junior')
    
    # Workload Settings
    max_daily_prescriptions = models.PositiveIntegerField(default=50, 
                                                        help_text="Maximum prescriptions per day")
    is_available = models.BooleanField(default=True, 
                                     help_text="Available for new assignments")
    
    # Performance Metrics
    performance_rating = models.DecimalField(max_digits=3, decimal_places=2, 
                                           default=0.0, 
                                           help_text="Overall performance rating (0-10)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Verifier Profile"
        verbose_name_plural = "Verifier Profiles"
    
    def __str__(self):
        return f"{self.user.full_name} - {self.specialization}"
    
    @property
    def full_name(self):
        return self.user.full_name or self.user.email


class VerificationActivity(models.Model):
    """Track verification activities and changes"""
    prescription = models.ForeignKey(PrescriptionUpload, on_delete=models.CASCADE, related_name='activities')
    verifier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50, choices=[
        ('created', 'Prescription Created'),
        ('assigned', 'Assigned to Verifier'),
        ('reviewed', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('clarification_requested', 'Clarification Requested'),
        ('clarification_received', 'Clarification Received'),
        ('notes_updated', 'Notes Updated'),
    ])
    description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.prescription.prescription_number} - {self.action} ({self.timestamp})"


class VerifierWorkload(models.Model):
    """Track verifier workload and performance"""
    verifier = models.OneToOneField(User, on_delete=models.CASCADE, related_name='workload_stats')
    
    # Current workload
    pending_count = models.PositiveIntegerField(default=0)
    in_review_count = models.PositiveIntegerField(default=0)
    
    # Performance metrics
    total_verified = models.PositiveIntegerField(default=0)
    total_approved = models.PositiveIntegerField(default=0)
    total_rejected = models.PositiveIntegerField(default=0)
    average_processing_time = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="In hours")
    
    # Quality metrics
    accuracy_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0, help_text="Accuracy percentage")
    customer_satisfaction = models.DecimalField(max_digits=3, decimal_places=2, default=0.0, help_text="Satisfaction score")
    
    # Availability
    is_available = models.BooleanField(default=True)
    max_daily_capacity = models.PositiveIntegerField(default=50, help_text="Maximum prescriptions per day")
    current_daily_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Verifier Workload"
        verbose_name_plural = "Verifier Workloads"
    
    def __str__(self):
        return f"{self.verifier.full_name} - Workload Stats"
    
    @property
    def approval_rate(self):
        """Calculate approval rate percentage"""
        if self.total_verified == 0:
            return 0
        return round((self.total_approved / self.total_verified) * 100, 2)
    
    @property
    def can_accept_more(self):
        """Check if verifier can accept more prescriptions"""
        return (self.is_available and 
                self.current_daily_count < self.max_daily_capacity and
                (self.pending_count + self.in_review_count) < 20)  # Max 20 active cases
    
    def update_workload(self):
        """Update current workload counts"""
        prescriptions = PrescriptionUpload.objects.filter(verified_by=self.verifier)
        self.pending_count = prescriptions.filter(verification_status='pending').count()
        self.in_review_count = prescriptions.filter(verification_status='in_review').count()
        
        # Update daily count
        today_count = prescriptions.filter(
            verification_date__date=timezone.now().date()
        ).count()
        self.current_daily_count = today_count
        
        self.save()


class PrescriptionMedication(models.Model):
    """Track individual medications from prescriptions"""
    prescription = models.ForeignKey(PrescriptionUpload, on_delete=models.CASCADE, related_name='medications')
    medication_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100, blank=True, null=True)
    frequency = models.CharField(max_length=100, blank=True, null=True)
    duration = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.PositiveIntegerField(blank=True, null=True)
    special_instructions = models.TextField(blank=True, null=True)
    
    # Verification status for individual medication
    is_verified = models.BooleanField(default=False)
    verification_notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['medication_name']
    
    def __str__(self):
        return f"{self.medication_name} - {self.prescription.prescription_number}"


# ==========================================
# SIGNALS - Auto-create VerifierWorkload
# ==========================================
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_verifier_workload(sender, instance, created, **kwargs):
    """
    Automatically create VerifierWorkload when a new RX Verifier user is created
    This ensures all RX verifiers have a workload tracking record
    """
    if created and instance.role == 'rx_verifier':
        try:
            workload, workload_created = VerifierWorkload.objects.get_or_create(
                verifier=instance,
                defaults={
                    'is_available': True,
                    'max_daily_capacity': 50  # Default capacity
                }
            )
            if workload_created:
                logger.info(f"✓ Auto-created VerifierWorkload for {instance.email}")
            else:
                logger.info(f"ℹ VerifierWorkload already exists for {instance.email}")
        except Exception as e:
            logger.error(f"✗ Failed to create VerifierWorkload for {instance.email}: {str(e)}")
