#!/usr/bin/env python3
"""
Simple Public API Test Script
Tests basic public endpoints
"""

import requests
import time

def test_basic_endpoints():
    base_url = 'http://127.0.0.1:8000'
    
    print("🚀 Testing Basic Public Endpoints...")
    print("=" * 50)
    
    endpoints_to_test = [
        '/api/public/products/categories/',
        '/api/public/products/brands/',
        '/api/public/products/products/',
        '/api/public/products/search/',
        '/api/public/products/featured/',
        '/api/cms/pages/',
        '/api/cms/banners/',
        '/api/cms/blog/',
        '/api/cms/faqs/',
        '/api/cms/testimonials/',
        '/swagger/',
        '/redoc/',
    ]
    
    results = {'passed': 0, 'failed': 0}
    
    for endpoint in endpoints_to_test:
        try:
            print(f"Testing: {endpoint}")
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - Status: {response.status_code}")
                results['passed'] += 1
            else:
                print(f"❌ {endpoint} - Status: {response.status_code}")
                results['failed'] += 1
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint} - Error: {str(e)}")
            results['failed'] += 1
        except Exception as e:
            print(f"❌ {endpoint} - Unexpected error: {str(e)}")
            results['failed'] += 1
        
        time.sleep(0.5)  # Small delay between requests
    
    print("\n" + "=" * 50)
    print("📊 RESULTS SUMMARY")
    print("=" * 50)
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    total = results['passed'] + results['failed']
    if total > 0:
        print(f"🎯 Success Rate: {(results['passed']/total*100):.1f}%")

if __name__ == "__main__":
    test_basic_endpoints()