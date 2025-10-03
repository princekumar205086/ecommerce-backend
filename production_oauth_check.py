#!/usr/bin/env python3
'''
Production Environment Check for Google OAuth
Run this on your production server to verify configuration
'''

import os
import sys

def main():
    print("🔍 Production Google OAuth Configuration Check")
    print("="*50)
    
    # Check environment variables
    client_id = os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY')
    client_secret = os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET')
    
    print(f"Client ID: {client_id}")
    print(f"Client Secret: {'***' + client_secret[-4:] if client_secret else 'NOT SET'}")
    
    if not client_id:
        print("❌ CRITICAL: SOCIAL_AUTH_GOOGLE_OAUTH2_KEY not set")
        sys.exit(1)
    
    if not client_secret:
        print("⚠️  WARNING: SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET not set")
    
    print("✅ Google OAuth configuration looks good")
    
    # Test import
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        print("✅ Google OAuth libraries are installed")
    except ImportError as e:
        print(f"❌ Google OAuth libraries missing: {e}")
        print("   Run: pip install google-auth google-auth-oauthlib")
        sys.exit(1)

if __name__ == "__main__":
    main()
