#!/usr/bin/env python
"""
Quick Endpoint Validation Script for MedixMall Accounts API
Run this script to validate key endpoints are working correctly.
"""
import requests
import json
import time
from datetime import datetime

class AccountsAPITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
    
    def test_endpoint(self, method, endpoint, data=None, headers=None, expected_status=200, description=""):
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers, params=data)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            success = response.status_code == expected_status
            
            result = {
                'endpoint': endpoint,
                'method': method.upper(),
                'description': description,
                'expected_status': expected_status,
                'actual_status': response.status_code,
                'success': success,
                'response_time': response.elapsed.total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
            
            self.results.append(result)
            
            status_icon = "✅" if success else "❌"
            print(f"{status_icon} {method.upper()} {endpoint} - {description}")
            print(f"   Status: {response.status_code} (expected {expected_status})")
            print(f"   Time: {response.elapsed.total_seconds():.3f}s")
            
            if not success:
                print(f"   Error: {response.text[:200]}")
            
            print()
            
            return response
            
        except Exception as e:
            result = {
                'endpoint': endpoint,
                'method': method.upper(),
                'description': description,
                'expected_status': expected_status,
                'actual_status': 'ERROR',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
            self.results.append(result)
            print(f"❌ {method.upper()} {endpoint} - {description}")
            print(f"   ERROR: {str(e)}")
            print()
            
            return None
    
    def run_basic_tests(self):
        """Run basic endpoint validation tests"""
        print("🚀 Starting MedixMall Accounts API Validation Tests...")
        print("=" * 60)
        
        # Test 1: Health Check (Home endpoint)
        self.test_endpoint('GET', '/', 
                          description="API Health Check",
                          expected_status=200)
        
        # Test 2: User Registration
        registration_data = {
            "email": "test@medixmall.com",
            "full_name": "Test User",
            "contact": "9876543210",
            "password": "TestPass123!",
            "password2": "TestPass123!"
        }
        
        response = self.test_endpoint('POST', '/api/accounts/register/', 
                                     data=registration_data,
                                     description="User Registration",
                                     expected_status=201)
        
        # Test 3: Duplicate Registration (should fail)
        self.test_endpoint('POST', '/api/accounts/register/', 
                          data=registration_data,
                          description="Duplicate Registration (should fail)",
                          expected_status=400)
        
        # Test 4: Login with unverified email (should send OTP)
        login_data = {
            "email": "test@medixmall.com",
            "password": "TestPass123!"
        }
        
        self.test_endpoint('POST', '/api/accounts/login/', 
                          data=login_data,
                          description="Login with unverified email (should send OTP)",
                          expected_status=403)
        
        # Test 5: Supplier Request
        supplier_request_data = {
            "email": "supplier@medixmall.com",
            "full_name": "Test Supplier",
            "contact": "9876543211",
            "password": "SupplierPass123!",
            "password2": "SupplierPass123!",
            "company_name": "Test Medical Supplies",
            "company_address": "123 Test Street",
            "gst_number": "22AAAAA0000A1Z5",
            "pan_number": "ABCDE1234F",
            "product_categories": "Medical Equipment"
        }
        
        self.test_endpoint('POST', '/api/accounts/supplier/request/', 
                          data=supplier_request_data,
                          description="Supplier Request Submission",
                          expected_status=201)
        
        # Test 6: Check Supplier Request Status
        self.test_endpoint('GET', '/api/accounts/supplier/request/status/', 
                          data={"email": "supplier@medixmall.com"},
                          description="Check Supplier Request Status",
                          expected_status=200)
        
        # Test 7: Password Reset Request
        password_reset_data = {
            "email": "test@medixmall.com"
        }
        
        self.test_endpoint('POST', '/api/accounts/password/reset-request/', 
                          data=password_reset_data,
                          description="Password Reset Request",
                          expected_status=200)
        
        # Test 8: Profile Access (should fail - no auth)
        self.test_endpoint('GET', '/api/accounts/me/', 
                          description="Profile Access (no auth - should fail)",
                          expected_status=401)
        
        # Test 9: Invalid Google Auth Token
        google_auth_data = {
            "id_token": "invalid_token",
            "role": "user"
        }
        
        self.test_endpoint('POST', '/api/accounts/login/google/', 
                          data=google_auth_data,
                          description="Google Auth with invalid token (should fail)",
                          expected_status=400)
        
        # Test 10: API Documentation
        self.test_endpoint('GET', '/swagger/', 
                          description="API Documentation Access",
                          expected_status=200)
        
        print("🏁 Test Suite Completed!")
        print("=" * 60)
        
        # Generate Summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - successful_tests
        
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        avg_response_time = sum(r.get('response_time', 0) for r in self.results if r.get('response_time')) / total_tests
        
        summary = f"""
📊 TEST SUMMARY REPORT
========================

🎯 Overall Results:
   Total Tests: {total_tests}
   ✅ Passed: {successful_tests}
   ❌ Failed: {failed_tests}
   📈 Success Rate: {success_rate:.1f}%
   ⏱️  Avg Response Time: {avg_response_time:.3f}s

🔍 Test Details:
"""
        
        for i, result in enumerate(self.results, 1):
            status_icon = "✅" if result['success'] else "❌"
            summary += f"   {i:2d}. {status_icon} {result['method']} {result['endpoint']}\n"
            summary += f"       {result['description']}\n"
            if not result['success']:
                error_info = result.get('error', f"Status {result['actual_status']}")
                summary += f"       Error: {error_info}\n"
        
        summary += f"""
🏥 API Status: {'🟢 HEALTHY' if success_rate >= 80 else '🟡 WARNING' if success_rate >= 60 else '🔴 CRITICAL'}

📝 Recommendations:
   - Ensure database migrations are applied
   - Check email configuration for OTP features
   - Verify Google OAuth credentials if using social login
   - Monitor failed endpoints for configuration issues

Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        print(summary)
        
        # Save report to file
        with open('accounts_api_validation_report.txt', 'w') as f:
            f.write(summary)
            f.write("\n\nDetailed Results:\n")
            f.write(json.dumps(self.results, indent=2))
        
        print(f"📄 Detailed report saved to: accounts_api_validation_report.txt")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MedixMall Accounts API Validation")
    parser.add_argument('--url', default='http://localhost:8000', 
                       help='Base URL of the API (default: http://localhost:8000)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    tester = AccountsAPITester(base_url=args.url)
    tester.run_basic_tests()