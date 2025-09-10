from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, OTP, PasswordResetToken

# Register your models here.

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom admin for User model with enhanced features"""
    list_display = ('email', 'full_name', 'contact', 'role', 'email_verified', 'is_active', 'date_joined')
    list_filter = ('role', 'email_verified', 'is_active', 'is_staff', 'is_superuser', 'date_joined', 'medixmall_mode')
    search_fields = ('email', 'full_name', 'contact')
    ordering = ('-date_joined',)

    # Override fieldsets to match our custom User model
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name', 'contact')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Additional Info', {
            'fields': ('role', 'email_verified', 'medixmall_mode')
        }),
        ('Address Information', {
            'fields': ('address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country'),
            'classes': ('collapse',)
        }),
    )

    # Override add_fieldsets for creating new users
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
        ('Personal info', {'fields': ('full_name', 'contact')}),
        ('Additional Info', {
            'fields': ('role', 'email_verified', 'medixmall_mode')
        }),
    )

    readonly_fields = ('date_joined', 'email_verification_sent_at', 'last_login')

    def get_queryset(self, request):
        """Optimize queryset for admin"""
        return super().get_queryset(request).select_related()

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    """Admin for OTP model"""
    list_display = ('user', 'otp_type', 'email', 'phone', 'otp_code', 'is_verified', 'created_at', 'expires_at', 'attempts')
    list_filter = ('otp_type', 'is_verified', 'created_at', 'expires_at')
    search_fields = ('user__email', 'user__full_name', 'email', 'phone', 'otp_code')
    ordering = ('-created_at',)
    readonly_fields = ('otp_code', 'created_at', 'expires_at', 'attempts')

    fieldsets = (
        ('OTP Information', {
            'fields': ('user', 'otp_type', 'otp_code', 'is_verified')
        }),
        ('Contact Details', {
            'fields': ('email', 'phone')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at', 'attempts'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """Disable adding OTPs manually"""
        return False

    def has_change_permission(self, request, obj=None):
        """Allow viewing but limit editing"""
        if obj and obj.is_verified:
            return False  # Don't allow editing verified OTPs
        return super().has_change_permission(request, obj)

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """Admin for Password Reset Token model"""
    list_display = ('user', 'token', 'is_used', 'created_at', 'expires_at')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'user__full_name', 'token')
    ordering = ('-created_at',)
    readonly_fields = ('token', 'created_at', 'expires_at')

    fieldsets = (
        ('Token Information', {
            'fields': ('user', 'token', 'is_used')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """Disable adding tokens manually"""
        return False

    def has_change_permission(self, request, obj=None):
        """Allow viewing but limit editing"""
        if obj and obj.is_used:
            return False  # Don't allow editing used tokens
        return super().has_change_permission(request, obj)
