#!/usr/bin/env python
import os
import django
import sys

# Configure Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.conf import settings
from django.urls import reverse, resolve, get_resolver
from django.test import RequestFactory
from django.http import HttpRequest

def test_django_configuration():
    """Test basic Django configuration"""
    print("=== DJANGO CONFIGURATION TEST ===")
    print(f"DEBUG: {settings.DEBUG}")
    print(f"ROOT_URLCONF: {settings.ROOT_URLCONF}")
    print(f"INSTALLED_APPS includes accounts: {'accounts' in settings.INSTALLED_APPS}")
    print()

def test_url_resolution():
    """Test URL resolution for accounts endpoints"""
    print("=== URL RESOLUTION TEST ===")
    test_urls = [
        'register',
        'login',
        'profile',
        'logout',
    ]
    
    for url_name in test_urls:
        try:
            resolved_url = reverse(url_name)
            print(f"✅ {url_name}: {resolved_url}")
        except Exception as e:
            print(f"❌ {url_name}: ERROR - {e}")
    print()

def test_view_imports():
    """Test importing all views"""
    print("=== VIEW IMPORTS TEST ===")
    try:
        from accounts.views import (
            RegisterView, LoginView, LogoutView, ProfileView, UserListView, 
            UserAddressView, SaveAddressFromCheckoutView, MedixMallModeToggleView, 
            CustomTokenRefreshView, EmailVerificationView, ResendVerificationView, 
            OTPRequestView, OTPVerificationView, PasswordResetRequestView, 
            PasswordResetConfirmView, ChangePasswordView, OTPLoginRequestView, 
            OTPLoginVerifyView, LoginChoiceView, ResendOTPView, SupplierDutyStatusView, 
            SupplierDutyToggleView, SupplierRequestView, SupplierRequestStatusView, 
            AdminSupplierRequestListView, AdminSupplierRequestActionView, GoogleAuthView
        )
        print("✅ All views imported successfully")
    except Exception as e:
        print(f"❌ View import error: {e}")
    print()

def test_url_patterns():
    """Test URL patterns directly"""
    print("=== URL PATTERNS TEST ===")
    try:
        resolver = get_resolver()
        print("Root URL resolver loaded successfully")
        
        # Test specific patterns
        test_paths = [
            '/api/accounts/register/',
            '/api/accounts/login/',
            '/api/accounts/profile/',
        ]
        
        for path in test_paths:
            try:
                match = resolve(path)
                print(f"✅ {path}: {match.view_name} -> {match.func}")
            except Exception as e:
                print(f"❌ {path}: ERROR - {e}")
    except Exception as e:
        print(f"❌ URL resolver error: {e}")
    print()

def test_request_simulation():
    """Simulate a request to test view functionality"""
    print("=== REQUEST SIMULATION TEST ===")
    try:
        from accounts.views import RegisterView
        factory = RequestFactory()
        request = factory.get('/api/accounts/register/')
        
        view = RegisterView()
        response = view.get(request)
        print(f"✅ RegisterView.get() returned: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Request simulation error: {e}")
    print()

if __name__ == '__main__':
    test_django_configuration()
    test_url_resolution()
    test_view_imports()
    test_url_patterns()
    test_request_simulation()
    print("=== DEBUG COMPLETE ===")