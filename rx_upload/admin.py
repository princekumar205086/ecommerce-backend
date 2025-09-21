# rx_upload/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import PrescriptionUpload, VerificationActivity, VerifierWorkload, PrescriptionMedication


@admin.register(PrescriptionUpload)
class PrescriptionUploadAdmin(admin.ModelAdmin):
    list_display = [
        'prescription_number', 'customer_name', 'patient_name', 'verification_status',
        'verified_by_name', 'is_urgent', 'uploaded_at', 'processing_time_display'
    ]
    list_filter = [
        'verification_status', 'is_urgent', 'priority_level', 'prescription_type',
        'uploaded_at', 'verification_date'
    ]
    search_fields = [
        'prescription_number', 'customer__full_name', 'customer__email',
        'patient_name', 'doctor_name', 'hospital_clinic'
    ]
    readonly_fields = [
        'id', 'prescription_number', 'uploaded_at', 'updated_at',
        'processing_time', 'can_be_verified', 'is_overdue',
        'prescription_image_preview'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'prescription_number', 'customer', 'prescription_type')
        }),
        ('Patient Details', {
            'fields': ('patient_name', 'patient_age', 'patient_gender')
        }),
        ('Doctor & Hospital', {
            'fields': ('doctor_name', 'doctor_license', 'hospital_clinic')
        }),
        ('Prescription Upload', {
            'fields': ('prescription_image', 'prescription_image_preview', 'original_filename', 'file_size')
        }),
        ('Medical Information', {
            'fields': ('diagnosis', 'medications_prescribed', 'dosage_instructions',
                      'prescription_date', 'prescription_valid_until')
        }),
        ('Verification', {
            'fields': ('verification_status', 'verified_by', 'verification_date',
                      'verification_notes', 'can_be_verified', 'processing_time')
        }),
        ('Communication', {
            'fields': ('customer_notes', 'clarification_requested', 'customer_response')
        }),
        ('Quality Control', {
            'fields': ('image_quality_score', 'legibility_score', 'completeness_score')
        }),
        ('Priority & Contact', {
            'fields': ('is_urgent', 'priority_level', 'customer_phone', 'alternative_contact')
        }),
        ('Timestamps', {
            'fields': ('uploaded_at', 'updated_at', 'is_overdue')
        })
    )
    
    def customer_name(self, obj):
        return obj.customer.full_name
    customer_name.short_description = 'Customer'
    
    def verified_by_name(self, obj):
        return obj.verified_by.full_name if obj.verified_by else '-'
    verified_by_name.short_description = 'Verified By'
    
    def processing_time_display(self, obj):
        time = obj.processing_time
        if time < 1:
            return f"{int(time * 60)} mins"
        return f"{time:.1f} hrs"
    processing_time_display.short_description = 'Processing Time'
    
    def prescription_image_preview(self, obj):
        if obj.prescription_image:
            return format_html(
                '<img src="{}" width="200" height="150" style="object-fit: contain;" />',
                obj.prescription_image
            )
        return "No image"
    prescription_image_preview.short_description = 'Image Preview'
    
    actions = ['mark_urgent', 'mark_not_urgent', 'assign_to_me']
    
    def mark_urgent(self, request, queryset):
        updated = queryset.update(is_urgent=True)
        self.message_user(request, f'{updated} prescriptions marked as urgent.')
    mark_urgent.short_description = 'Mark selected prescriptions as urgent'
    
    def mark_not_urgent(self, request, queryset):
        updated = queryset.update(is_urgent=False)
        self.message_user(request, f'{updated} prescriptions marked as not urgent.')
    mark_not_urgent.short_description = 'Mark selected prescriptions as not urgent'
    
    def assign_to_me(self, request, queryset):
        if request.user.role == 'rx_verifier':
            updated = 0
            for prescription in queryset.filter(verification_status='pending'):
                success, message = prescription.assign_to_verifier(request.user)
                if success:
                    updated += 1
            self.message_user(request, f'{updated} prescriptions assigned to you.')
        else:
            self.message_user(request, 'Only RX verifiers can assign prescriptions to themselves.', level='error')
    assign_to_me.short_description = 'Assign selected prescriptions to me'


@admin.register(VerificationActivity)
class VerificationActivityAdmin(admin.ModelAdmin):
    list_display = ['prescription_number', 'verifier_name', 'action', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['prescription__prescription_number', 'verifier__full_name', 'description']
    readonly_fields = ['prescription_number', 'verifier_name', 'timestamp']
    
    def prescription_number(self, obj):
        return obj.prescription.prescription_number
    prescription_number.short_description = 'Prescription'
    
    def verifier_name(self, obj):
        return obj.verifier.full_name if obj.verifier else 'System'
    verifier_name.short_description = 'Verifier'


@admin.register(VerifierWorkload)
class VerifierWorkloadAdmin(admin.ModelAdmin):
    list_display = [
        'verifier_name', 'pending_count', 'in_review_count', 'total_verified',
        'approval_rate_display', 'is_available', 'can_accept_more', 'last_activity'
    ]
    list_filter = ['is_available', 'last_activity']
    search_fields = ['verifier__full_name', 'verifier__email']
    readonly_fields = [
        'verifier_name', 'pending_count', 'in_review_count', 'approval_rate',
        'can_accept_more', 'last_activity'
    ]
    
    fieldsets = (
        ('Verifier Information', {
            'fields': ('verifier', 'verifier_name')
        }),
        ('Current Workload', {
            'fields': ('pending_count', 'in_review_count', 'is_available', 'can_accept_more')
        }),
        ('Performance Metrics', {
            'fields': ('total_verified', 'total_approved', 'total_rejected',
                      'average_processing_time', 'approval_rate')
        }),
        ('Quality Metrics', {
            'fields': ('accuracy_score', 'customer_satisfaction')
        }),
        ('Capacity Settings', {
            'fields': ('max_daily_capacity', 'current_daily_count')
        }),
        ('Activity', {
            'fields': ('last_activity',)
        })
    )
    
    def verifier_name(self, obj):
        return obj.verifier.full_name
    verifier_name.short_description = 'Verifier'
    
    def approval_rate_display(self, obj):
        return f"{obj.approval_rate}%"
    approval_rate_display.short_description = 'Approval Rate'
    
    actions = ['update_workloads', 'set_available', 'set_unavailable']
    
    def update_workloads(self, request, queryset):
        for workload in queryset:
            workload.update_workload()
        self.message_user(request, f'{queryset.count()} workloads updated.')
    update_workloads.short_description = 'Update selected workloads'
    
    def set_available(self, request, queryset):
        updated = queryset.update(is_available=True)
        self.message_user(request, f'{updated} verifiers set as available.')
    set_available.short_description = 'Set selected verifiers as available'
    
    def set_unavailable(self, request, queryset):
        updated = queryset.update(is_available=False)
        self.message_user(request, f'{updated} verifiers set as unavailable.')
    set_unavailable.short_description = 'Set selected verifiers as unavailable'


@admin.register(PrescriptionMedication)
class PrescriptionMedicationAdmin(admin.ModelAdmin):
    list_display = [
        'medication_name', 'prescription_number', 'dosage', 'frequency',
        'is_verified', 'verification_status'
    ]
    list_filter = ['is_verified']
    search_fields = ['medication_name', 'prescription__prescription_number']
    
    def prescription_number(self, obj):
        return obj.prescription.prescription_number
    prescription_number.short_description = 'Prescription'
    
    def verification_status(self, obj):
        if obj.is_verified:
            return format_html('<span style="color: green;">✓ Verified</span>')
        else:
            return format_html('<span style="color: orange;">⏳ Pending</span>')
    verification_status.short_description = 'Status'
