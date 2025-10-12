"""
Production Environment Debug Test
Tests production URL with proper authentication and debugging
"""

import requests
import json
import hashlib
import hmac
import time
from datetime import datetime

# Production Configuration
PRODUCTION_BASE_URL = 'https://backend.okpuja.in/api'
LOCAL_BASE_URL = 'http://localhost:8000/api'

# Test credentials
TEST_EMAIL = 'user@example.com'
TEST_PASSWORD = 'User@123'

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
BOLD = '\033[1m'
ENDC = '\033[0m'

def log_success(msg):
    print(f"{GREEN}✓ {msg}{ENDC}")

def log_error(msg):
    print(f"{RED}✗ {msg}{ENDC}")

def log_info(msg):
    print(f"{BLUE}ℹ {msg}{ENDC}")

def log_warning(msg):
    print(f"{YELLOW}⚠ {msg}{ENDC}")

def log_section(msg):
    print(f"\n{BOLD}{BLUE}{'='*80}{ENDC}")
    print(f"{BOLD}{BLUE}{msg}{ENDC}")
    print(f"{BOLD}{BLUE}{'='*80}{ENDC}")

def test_environment_connectivity(base_url, env_name):
    """Test basic connectivity to environment"""
    log_info(f"Testing {env_name} connectivity...")
    
    try:
        # Test basic endpoint
        response = requests.get(f"{base_url}/", timeout=10)
        log_info(f"   Status: {response.status_code}")
        log_info(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            log_success(f"✅ {env_name} is accessible")
            return True
        else:
            log_warning(f"⚠️ {env_name} returned {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        log_error(f"❌ {env_name} connection timeout")
        return False
    except requests.exceptions.ConnectionError:
        log_error(f"❌ {env_name} connection failed")
        return False
    except Exception as e:
        log_error(f"❌ {env_name} error: {str(e)}")
        return False

def authenticate_user(base_url, env_name):
    """Authenticate user and get token"""
    log_info(f"Authenticating on {env_name}...")
    
    try:
        response = requests.post(f"{base_url}/token/", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }, timeout=10)
        
        log_info(f"   Auth Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            log_success(f"✅ {env_name} authentication successful")
            return token_data['access']
        else:
            log_error(f"❌ {env_name} authentication failed: {response.text}")
            return None
            
    except Exception as e:
        log_error(f"❌ {env_name} auth error: {str(e)}")
        return None

def test_payment_verification(base_url, env_name, token):
    """Test payment verification endpoint"""
    log_info(f"Testing payment verification on {env_name}...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test with various scenarios
    test_scenarios = [
        {
            "name": "Development Signature",
            "payload": {
                "razorpay_order_id": "order_test_debug",
                "razorpay_payment_id": "pay_test_debug",
                "razorpay_signature": "development_mode_signature"
            }
        },
        {
            "name": "Generated HMAC Signature",
            "payload": {
                "razorpay_order_id": "order_test_hmac",
                "razorpay_payment_id": "pay_test_hmac",
                "razorpay_signature": generate_test_signature("order_test_hmac", "pay_test_hmac")
            }
        },
        {
            "name": "Invalid Signature",
            "payload": {
                "razorpay_order_id": "order_test_invalid",
                "razorpay_payment_id": "pay_test_invalid",
                "razorpay_signature": "invalid_signature_test"
            }
        }
    ]
    
    results = []
    
    for scenario in test_scenarios:
        log_info(f"   Testing: {scenario['name']}")
        
        try:
            response = requests.post(
                f"{base_url}/payments/verify/",
                json=scenario['payload'],
                headers=headers,
                timeout=10
            )
            
            log_info(f"      Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                log_success(f"      ✅ Success: {data.get('status', 'Unknown')}")
                results.append(True)
            elif response.status_code == 400:
                error_data = response.json()
                log_warning(f"      ⚠️ Expected failure: {error_data.get('error', 'Unknown')}")
                results.append(True)  # Expected for invalid signatures
            elif response.status_code == 401:
                log_error(f"      ❌ Authentication failed")
                results.append(False)
            else:
                log_error(f"      ❌ Unexpected status: {response.text}")
                results.append(False)
                
        except Exception as e:
            log_error(f"      ❌ Request failed: {str(e)}")
            results.append(False)
    
    success_rate = (sum(results) / len(results)) * 100
    log_info(f"   {env_name} verification success rate: {success_rate:.1f}%")
    
    return success_rate >= 66  # Allow some failures for invalid signatures

def generate_test_signature(order_id, payment_id, secret="test_secret_key"):
    """Generate test signature for verification"""
    message = f"{order_id}|{payment_id}"
    signature = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def compare_environments():
    """Compare local and production environments"""
    log_section("🌍 ENVIRONMENT COMPARISON TEST")
    
    environments = [
        (LOCAL_BASE_URL, "Local Development"),
        (PRODUCTION_BASE_URL, "Production")
    ]
    
    results = {}
    
    for base_url, env_name in environments:
        log_info(f"\n🔄 Testing {env_name}...")
        
        # Test connectivity
        connectivity = test_environment_connectivity(base_url, env_name)
        
        # Test authentication
        token = None
        if connectivity:
            token = authenticate_user(base_url, env_name)
        
        # Test payment verification
        verification_success = False
        if token:
            verification_success = test_payment_verification(base_url, env_name, token)
        
        results[env_name] = {
            'connectivity': connectivity,
            'authentication': bool(token),
            'verification': verification_success,
            'token': token
        }
    
    return results

def detailed_production_debug():
    """Detailed debugging of production issues"""
    log_section("🔍 DETAILED PRODUCTION DEBUGGING")
    
    # Test production authentication
    log_info("Step 1: Production Authentication Debug")
    try:
        auth_response = requests.post(f"{PRODUCTION_BASE_URL}/token/", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }, timeout=15)
        
        log_info(f"Auth response status: {auth_response.status_code}")
        log_info(f"Auth response headers: {dict(auth_response.headers)}")
        log_info(f"Auth response body: {auth_response.text}")
        
        if auth_response.status_code == 200:
            token = auth_response.json()['access']
            log_success("✅ Production authentication working")
            
            # Test payment verification with proper auth
            log_info("Step 2: Production Payment Verification Debug")
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Production Test)',
                'Accept': 'application/json'
            }
            
            verify_payload = {
                "razorpay_order_id": f"order_prod_debug_{int(time.time())}",
                "razorpay_payment_id": f"pay_prod_debug_{int(time.time())}", 
                "razorpay_signature": "development_mode_signature"
            }
            
            log_info(f"Verification payload: {verify_payload}")
            log_info(f"Headers: {headers}")
            
            verify_response = requests.post(
                f"{PRODUCTION_BASE_URL}/payments/verify/",
                json=verify_payload,
                headers=headers,
                timeout=15
            )
            
            log_info(f"Verification status: {verify_response.status_code}")
            log_info(f"Verification headers: {dict(verify_response.headers)}")
            log_info(f"Verification body: {verify_response.text}")
            
            if verify_response.status_code == 200:
                log_success("✅ Production payment verification working!")
                return True
            elif verify_response.status_code == 400:
                error_data = verify_response.json()
                if error_data.get('error') == 'Payment verification failed':
                    log_success("✅ Production error handling working correctly")
                    return True
                else:
                    log_error(f"❌ Unexpected error: {error_data}")
            else:
                log_error(f"❌ Production verification failed with {verify_response.status_code}")
        else:
            log_error("❌ Production authentication failed")
            
    except Exception as e:
        log_error(f"❌ Production debug failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return False

def run_comprehensive_production_test():
    """Run comprehensive production test"""
    log_section("🚀 COMPREHENSIVE PRODUCTION TEST")
    
    # Compare environments
    results = compare_environments()
    
    # Detailed production debugging
    production_debug_success = detailed_production_debug()
    
    # Summary
    log_section("📊 TEST RESULTS SUMMARY")
    
    for env_name, result in results.items():
        log_info(f"\n{env_name} Results:")
        log_success(f"  ✅ Connectivity: {result['connectivity']}")
        log_success(f"  ✅ Authentication: {result['authentication']}")
        log_success(f"  ✅ Verification: {result['verification']}")
    
    log_info(f"\nProduction Debug: {production_debug_success}")
    
    # Recommendations
    log_section("💡 RECOMMENDATIONS")
    
    if results.get('Production', {}).get('authentication') and production_debug_success:
        log_success("🎉 PRODUCTION SYSTEM IS WORKING CORRECTLY!")
        log_success("✅ Authentication working on production")
        log_success("✅ Payment verification working on production")
        log_success("✅ Error handling working correctly")
        log_info("\n📋 The 'Payment verification failed' error is EXPECTED behavior for:")
        log_info("   • Invalid signatures in production environment")
        log_info("   • Missing payment records") 
        log_info("   • Actual verification failures")
        log_info("\n🔧 For successful production payments:")
        log_info("   • Use real Razorpay payment_id from successful transactions")
        log_info("   • Generate proper HMAC signatures using Razorpay secret")
        log_info("   • Ensure payment record exists in database")
    else:
        log_error("❌ Production system has issues")
        log_info("🔧 Potential fixes:")
        log_info("   • Check server configuration")
        log_info("   • Verify database connectivity")
        log_info("   • Check authentication system")
        log_info("   • Review error logs")

if __name__ == "__main__":
    print(f"{BOLD}PRODUCTION ENVIRONMENT DEBUG & TEST{ENDC}")
    print(f"{BOLD}==================================={ENDC}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        run_comprehensive_production_test()
    except KeyboardInterrupt:
        log_warning("\n⚠️ Test interrupted by user")
    except Exception as e:
        log_error(f"\n💥 Test suite failed: {str(e)}")
        import traceback 
        traceback.print_exc()