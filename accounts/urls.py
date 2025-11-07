# accounts/urls.py
from django.urls import path
from .views import (
    RegisterView, EmailCheckView, LoginView, LogoutView, ProfileView, UserListView, UserAddressView, 
    SaveAddressFromCheckoutView, MedixMallModeToggleView, CustomTokenRefreshView,
    EmailVerificationView, ResendVerificationView, OTPRequestView, OTPVerificationView,
    PasswordResetRequestView, PasswordResetConfirmView, ChangePasswordView,
    OTPLoginRequestView, OTPLoginVerifyView, LoginChoiceView, ResendOTPView,
    SupplierDutyStatusView, SupplierDutyToggleView,
    SupplierRequestView, SupplierRequestStatusView, AdminSupplierRequestListView, AdminSupplierRequestActionView,
    GoogleAuthView, RateLimitStatusView
)
from .admin_views import (
    AdminUserListView, AdminUserDetailView, AdminUserCreateView,
    AdminUserUpdateView, AdminUserDeleteView, AdminUserRoleChangeView,
    AdminUserStatusChangeView, AdminBulkUserActionView, AdminUserStatisticsView,
    AdminAuditLogListView, AdminUserExportView, AdminRXVerifierCreateView,
    AdminCheckEmailAvailabilityView,
    AdminUserSearchView
)

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('register/<str:role>/', RegisterView.as_view(), name='register-with-role'),
    path('check-email/', EmailCheckView.as_view(), name='check_email'),
    path('login/', LoginView.as_view(), name='login'),
    path('login/choice/', LoginChoiceView.as_view(), name='login_choice'),  # New unified login
    path('login/google/', GoogleAuthView.as_view(), name='google_auth'),  # Google Social Login
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh_custom'),
    
    # Profile & User Management
    path('me/', ProfileView.as_view(), name='profile'),
    path('list/', UserListView.as_view(), name='user_list'),
    path('address/', UserAddressView.as_view(), name='user_address'),
    path('address/save-from-checkout/', SaveAddressFromCheckoutView.as_view(), name='save_address_from_checkout'),
    path('medixmall-mode/', MedixMallModeToggleView.as_view(), name='medixmall_mode_toggle'),
    
    # Session Management & Rate Limiting
    path('rate-limit/status/', RateLimitStatusView.as_view(), name='rate_limit_status'),
    
    # Email Verification (OTP-based)
    path('verify-email/', EmailVerificationView.as_view(), name='verify_email_otp'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend_verification'),
    
    # OTP Verification
    path('otp/request/', OTPRequestView.as_view(), name='otp_request'),
    path('otp/verify/', OTPVerificationView.as_view(), name='otp_verify'),
    path('otp/resend/', ResendOTPView.as_view(), name='resend_otp'),
    
    # OTP Login System
    path('login/otp/request/', OTPLoginRequestView.as_view(), name='otp_login_request'),
    path('login/otp/verify/', OTPLoginVerifyView.as_view(), name='otp_login_verify'),
    
    # Password Management
    path('password/reset-request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password/reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password/change/', ChangePasswordView.as_view(), name='change_password'),
    
    # Supplier Duty Management
    path('supplier/duty/status/', SupplierDutyStatusView.as_view(), name='supplier_duty_status'),
    path('supplier/duty/toggle/', SupplierDutyToggleView.as_view(), name='supplier_duty_toggle'),
    
    # Supplier Request System
    path('supplier/request/', SupplierRequestView.as_view(), name='supplier_request'),
    path('supplier/request/status/', SupplierRequestStatusView.as_view(), name='supplier_request_status'),
    
    # Admin - Supplier Request Management
    path('admin/supplier/requests/', AdminSupplierRequestListView.as_view(), name='admin_supplier_requests'),
    path('admin/supplier/requests/<int:request_id>/action/', AdminSupplierRequestActionView.as_view(), name='admin_supplier_request_action'),
    
    # Admin - User Management
    path('admin/users/', AdminUserListView.as_view(), name='admin_user_list'),
    path('admin/users/search/', AdminUserSearchView.as_view(), name='admin_user_search'),
    path('admin/users/export/', AdminUserExportView.as_view(), name='admin_user_export'),
    path('admin/users/bulk-action/', AdminBulkUserActionView.as_view(), name='admin_bulk_user_action'),
    path('admin/users/create/', AdminUserCreateView.as_view(), name='admin_user_create'),
    path('admin/users/<int:id>/', AdminUserDetailView.as_view(), name='admin_user_detail'),
    path('admin/users/<int:id>/update/', AdminUserUpdateView.as_view(), name='admin_user_update'),
    path('admin/users/<int:id>/delete/', AdminUserDeleteView.as_view(), name='admin_user_delete'),
    path('admin/users/<int:user_id>/change-role/', AdminUserRoleChangeView.as_view(), name='admin_user_change_role'),
    path('admin/users/<int:user_id>/change-status/', AdminUserStatusChangeView.as_view(), name='admin_user_change_status'),
    
    # Admin - RX Verifier Management
    path('admin/rx-verifiers/check-email/', AdminCheckEmailAvailabilityView.as_view(), name='admin_check_email_availability'),
    path('admin/rx-verifiers/create/', AdminRXVerifierCreateView.as_view(), name='admin_rx_verifier_create'),
    
    # Admin - Analytics & Audit
    path('admin/statistics/', AdminUserStatisticsView.as_view(), name='admin_user_statistics'),
    path('admin/audit-logs/', AdminAuditLogListView.as_view(), name='admin_audit_logs'),
]