# rx_upload/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .verifier_account_views import (
    CreateVerifierAccountView, VerifierAccountListView, 
    SendCredentialReminderView, VerifierAccountDetailView,
    VerifierAccountStatsView, test_verifier_email_notification
)
from . import customer_views
from . import admin_views

app_name = 'rx_upload'

urlpatterns = [
    # Customer prescription order flow endpoints
    path('customer/upload/', customer_views.upload_prescription, name='customer_upload_prescription'),
    path('customer/<uuid:prescription_id>/patient-info/', customer_views.add_patient_information, name='customer_add_patient_info'),
    path('customer/addresses/', customer_views.get_delivery_addresses, name='customer_get_addresses'),
    path('customer/delivery-options/', customer_views.get_delivery_options, name='customer_delivery_options'),
    path('customer/<uuid:prescription_id>/submit/', customer_views.submit_prescription_order, name='customer_submit_order'),
    path('customer/<uuid:prescription_id>/summary/', customer_views.get_prescription_order_summary, name='customer_order_summary'),
    path('customer/my-prescriptions/', customer_views.get_my_prescriptions, name='customer_my_prescriptions'),
    
    # Authentication endpoints (for RX verifiers)
    path('auth/login/', views.rx_verifier_login, name='rx_verifier_login'),
    path('auth/logout/', views.rx_verifier_logout, name='rx_verifier_logout'),
    path('auth/profile/', views.rx_verifier_profile, name='rx_verifier_profile'),
    
    # Prescription management
    path('prescriptions/', views.PrescriptionUploadListCreateView.as_view(), name='prescription_list_create'),
    path('prescriptions/<uuid:pk>/', views.PrescriptionUploadDetailView.as_view(), name='prescription_detail'),
    
    # Verification actions
    path('prescriptions/<uuid:prescription_id>/assign/', views.assign_prescription, name='assign_prescription'),
    path('prescriptions/<uuid:prescription_id>/approve/', views.approve_prescription, name='approve_prescription'),
    path('prescriptions/<uuid:prescription_id>/reject/', views.reject_prescription, name='reject_prescription'),
    path('prescriptions/<uuid:prescription_id>/clarification/', views.request_clarification, name='request_clarification'),
    
    # Order integration
    path('prescriptions/<uuid:prescription_id>/create-order/', views.create_order_from_prescription, name='create_order_from_prescription'),
    path('prescriptions/<uuid:prescription_id>/orders/', views.get_prescription_orders, name='get_prescription_orders'),
    
    # Dashboard and analytics
    path('dashboard/', views.verification_dashboard, name='verification_dashboard'),
    path('pending/', views.pending_prescriptions, name='pending_prescriptions'),
    
    # Workload management
    path('workloads/', views.verifier_workloads, name='verifier_workloads'),
    path('availability/', views.update_availability, name='update_availability'),
    
    # Admin - Verifier Account Management
    path('admin/verifiers/create/', CreateVerifierAccountView.as_view(), name='create_verifier_account'),
    path('admin/verifiers/', VerifierAccountListView.as_view(), name='verifier_account_list'),
    path('admin/verifiers/<int:verifier_id>/', VerifierAccountDetailView.as_view(), name='verifier_account_detail'),
    path('admin/verifiers/send-reminder/', SendCredentialReminderView.as_view(), name='send_credential_reminder'),
    path('admin/verifiers/statistics/', VerifierAccountStatsView.as_view(), name='verifier_account_stats'),
    
    # Admin - Dashboard & Analytics
    path('admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin/reports/performance/', admin_views.admin_performance_report, name='admin_performance_report'),
    
    # Admin - Prescription Management
    path('admin/prescriptions/', admin_views.admin_list_prescriptions, name='admin_list_prescriptions'),
    path('admin/prescriptions/<uuid:prescription_id>/assign/', admin_views.admin_assign_prescription, name='admin_assign_prescription'),
    path('admin/prescriptions/<uuid:prescription_id>/reassign/', admin_views.admin_reassign_prescription, name='admin_reassign_prescription'),
    path('admin/prescriptions/bulk-assign/', admin_views.admin_bulk_assign, name='admin_bulk_assign'),
    
    # Admin - Verifier Management
    path('admin/verifiers-management/', admin_views.admin_list_verifiers, name='admin_list_verifiers'),
    path('admin/verifiers-management/<int:verifier_id>/status/', admin_views.admin_update_verifier_status, name='admin_update_verifier_status'),
    
    # Testing endpoints
    path('admin/test/email-notification/', test_verifier_email_notification, name='test_verifier_email'),
]