# rx_upload/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .verifier_account_views import (
    CreateVerifierAccountView, VerifierAccountListView, 
    SendCredentialReminderView, VerifierAccountDetailView,
    VerifierAccountStatsView, test_verifier_email_notification
)

app_name = 'rx_upload'

urlpatterns = [
    # Authentication endpoints
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
    
    # Testing endpoints
    path('admin/test/email-notification/', test_verifier_email_notification, name='test_verifier_email'),
]