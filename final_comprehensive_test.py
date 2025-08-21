#!/usr/bin/env python3
"""
Final Comprehensive Public API Test
Tests all working public endpoints with actual functionality
"""

import requests
import json
from datetime import datetime

def comprehensive_api_test():
    base_url = 'http://127.0.0.1:8000'
    
    print("🚀 FINAL COMPREHENSIVE PUBLIC API TEST")
    print("=" * 70)
    print(f"📍 Base URL: {base_url}")
    print(f"🕒 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Test Results
    results = {
        'total_tests': 0,
        'passed': 0,
        'failed': 0,
        'endpoints': {}
    }
    
    def test_endpoint(name, url, expected_keys=None, test_params=None):
        """Test an endpoint and return results"""
        results['total_tests'] += 1
        
        try:
            response = requests.get(url, params=test_params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Basic structure validation
                if expected_keys:
                    missing_keys = [key for key in expected_keys if key not in data]
                    if missing_keys:
                        print(f"❌ {name}: Missing keys {missing_keys}")
                        results['failed'] += 1
                        results['endpoints'][name] = {'status': 'FAIL', 'reason': f'Missing keys: {missing_keys}'}
                        return False
                
                print(f"✅ {name}: OK")
                results['passed'] += 1
                
                # Extract useful info
                info = {}
                if isinstance(data, dict):
                    if 'count' in data:
                        info['count'] = data['count']
                    if 'results' in data and isinstance(data['results'], list):
                        info['results_count'] = len(data['results'])
                elif isinstance(data, list):
                    info['list_count'] = len(data)
                
                results['endpoints'][name] = {'status': 'PASS', 'info': info}
                return True
                
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
                results['failed'] += 1
                results['endpoints'][name] = {'status': 'FAIL', 'reason': f'HTTP {response.status_code}'}
                return False
                
        except Exception as e:
            print(f"❌ {name}: {str(e)}")
            results['failed'] += 1
            results['endpoints'][name] = {'status': 'FAIL', 'reason': str(e)}
            return False
    
    # 1. PRODUCT ENDPOINTS
    print("\n🛍️  PRODUCT ENDPOINTS")
    print("-" * 50)
    
    test_endpoint(
        "Product Categories", 
        f"{base_url}/api/public/products/categories/",
        expected_keys=['count', 'results']
    )
    
    test_endpoint(
        "Brands", 
        f"{base_url}/api/public/products/brands/",
        expected_keys=['count', 'results']
    )
    
    test_endpoint(
        "Products List", 
        f"{base_url}/api/public/products/products/",
        expected_keys=['count', 'results']
    )
    
    test_endpoint(
        "Product Search", 
        f"{base_url}/api/public/products/search/",
        expected_keys=['results', 'pagination', 'filters']
    )
    
    test_endpoint(
        "Featured Products", 
        f"{base_url}/api/public/products/featured/",
        expected_keys=['count', 'results']
    )
    
    # Test product detail if products exist
    products_response = requests.get(f"{base_url}/api/public/products/products/")
    if products_response.status_code == 200:
        products_data = products_response.json()
        if products_data.get('results') and len(products_data['results']) > 0:
            product_id = products_data['results'][0]['id']
            test_endpoint(
                "Product Detail", 
                f"{base_url}/api/public/products/products/{product_id}/",
                expected_keys=['id', 'name', 'description', 'price']
            )
            
            # Test category products
            category_id = products_data['results'][0].get('category')
            if category_id:
                test_endpoint(
                    "Products by Category", 
                    f"{base_url}/api/public/products/categories/{category_id}/products/",
                    expected_keys=['count', 'results']
                )
            
            # Test brand products
            brand_id = products_data['results'][0].get('brand')
            if brand_id:
                test_endpoint(
                    "Products by Brand", 
                    f"{base_url}/api/public/products/brands/{brand_id}/products/",
                    expected_keys=['count', 'results']
                )
    
    # 2. CMS ENDPOINTS
    print("\n📄 CMS ENDPOINTS")
    print("-" * 50)
    
    test_endpoint(
        "CMS Pages", 
        f"{base_url}/api/cms/pages/",
        expected_keys=['count', 'results']
    )
    
    test_endpoint(
        "Banners", 
        f"{base_url}/api/cms/banners/",
        expected_keys=['count', 'results']
    )
    
    test_endpoint(
        "Blog Posts", 
        f"{base_url}/api/cms/blog/",
        expected_keys=['count', 'results']
    )
    
    test_endpoint(
        "Blog Categories", 
        f"{base_url}/api/cms/blog/categories/",
        expected_keys=['count', 'results']
    )
    
    test_endpoint(
        "Blog Tags", 
        f"{base_url}/api/cms/blog/tags/",
        expected_keys=['count', 'results']
    )
    
    test_endpoint(
        "FAQs", 
        f"{base_url}/api/cms/faqs/",
        expected_keys=['count', 'results']
    )
    
    test_endpoint(
        "Testimonials", 
        f"{base_url}/api/cms/testimonials/",
        expected_keys=['count', 'results']
    )
    
    # 3. OTHER ENDPOINTS
    print("\n⚙️  OTHER ENDPOINTS")
    print("-" * 50)
    
    # Test analytics tracking
    try:
        track_response = requests.post(f"{base_url}/api/analytics/track/", json={
            'event_type': 'page_view',
            'path': '/test-api',
            'data': {'test': True}
        })
        if track_response.status_code in [200, 201]:
            print("✅ Analytics Tracking: OK")
            results['passed'] += 1
            results['endpoints']['Analytics Tracking'] = {'status': 'PASS'}
        else:
            print(f"❌ Analytics Tracking: HTTP {track_response.status_code}")
            results['failed'] += 1
            results['endpoints']['Analytics Tracking'] = {'status': 'FAIL', 'reason': f'HTTP {track_response.status_code}'}
    except Exception as e:
        print(f"❌ Analytics Tracking: {str(e)}")
        results['failed'] += 1
        results['endpoints']['Analytics Tracking'] = {'status': 'FAIL', 'reason': str(e)}
    
    results['total_tests'] += 1
    
    # Test API Documentation
    try:
        swagger_response = requests.get(f"{base_url}/swagger/")
        if swagger_response.status_code == 200 and 'swagger' in swagger_response.text.lower():
            print("✅ Swagger UI: OK")
            results['passed'] += 1
            results['endpoints']['Swagger UI'] = {'status': 'PASS'}
        else:
            print("❌ Swagger UI: Failed")
            results['failed'] += 1
            results['endpoints']['Swagger UI'] = {'status': 'FAIL'}
    except Exception as e:
        print(f"❌ Swagger UI: {str(e)}")
        results['failed'] += 1
        results['endpoints']['Swagger UI'] = {'status': 'FAIL', 'reason': str(e)}
    
    results['total_tests'] += 1
    
    # Test ReDoc
    try:
        redoc_response = requests.get(f"{base_url}/redoc/")
        if redoc_response.status_code == 200:
            print("✅ ReDoc UI: OK")
            results['passed'] += 1
            results['endpoints']['ReDoc UI'] = {'status': 'PASS'}
        else:
            print("❌ ReDoc UI: Failed")
            results['failed'] += 1
            results['endpoints']['ReDoc UI'] = {'status': 'FAIL'}
    except Exception as e:
        print(f"❌ ReDoc UI: {str(e)}")
        results['failed'] += 1
        results['endpoints']['ReDoc UI'] = {'status': 'FAIL', 'reason': str(e)}
    
    results['total_tests'] += 1
    
    # 4. SEARCH AND FILTER TESTING
    print("\n🔍 SEARCH & FILTER TESTING")
    print("-" * 50)
    
    # Test search with query
    test_endpoint(
        "Search with Query", 
        f"{base_url}/api/public/products/search/",
        expected_keys=['results', 'pagination', 'filters'],
        test_params={'q': 'medicine', 'page_size': 5}
    )
    
    # Test search with filters
    test_endpoint(
        "Search with Filters", 
        f"{base_url}/api/public/products/search/",
        expected_keys=['results', 'pagination', 'filters'],
        test_params={'product_type': 'medicine', 'sort_by': 'price'}
    )
    
    # 5. FINAL RESULTS
    print("\n" + "=" * 70)
    print("📊 FINAL TEST RESULTS")
    print("=" * 70)
    
    success_rate = (results['passed'] / results['total_tests']) * 100 if results['total_tests'] > 0 else 0
    
    print(f"✅ PASSED: {results['passed']}")
    print(f"❌ FAILED: {results['failed']}")
    print(f"📋 TOTAL:  {results['total_tests']}")
    print(f"🎯 SUCCESS RATE: {success_rate:.1f}%")
    
    if results['failed'] > 0:
        print(f"\n❌ FAILED ENDPOINTS:")
        for name, info in results['endpoints'].items():
            if info['status'] == 'FAIL':
                reason = info.get('reason', 'Unknown error')
                print(f"   • {name}: {reason}")
    
    print(f"\n✅ WORKING ENDPOINTS:")
    for name, info in results['endpoints'].items():
        if info['status'] == 'PASS':
            extra_info = ""
            if 'info' in info and info['info']:
                extra_info = " (" + ", ".join([f"{k}: {v}" for k, v in info['info'].items()]) + ")"
            print(f"   • {name}{extra_info}")
    
    # Save results
    with open('final_api_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: final_api_test_results.json")
    
    return results

if __name__ == "__main__":
    comprehensive_api_test()