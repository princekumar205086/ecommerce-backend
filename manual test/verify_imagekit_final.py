#!/usr/bin/env python3
"""
Final Verification Test for Fixed ImageKit URLs
Tests API endpoints to ensure all images are properly displayed
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

class ImageKitVerificationTester:
    def __init__(self):
        self.admin_token = None
        self.test_results = []
        
    def login_admin(self):
        """Login as admin to access all endpoints"""
        response = requests.post(f"{BASE_URL}/api/accounts/login/", json={
            "email": "admin@example.com",
            "password": "Admin@123"
        })
        if response.status_code == 200:
            self.admin_token = response.json()['access']
            print("✅ Admin authenticated successfully")
            return True
        else:
            print(f"❌ Admin login failed: {response.text}")
            return False
    
    def test_products_api(self):
        """Test products API endpoints for ImageKit URLs"""
        print("\n📦 TESTING PRODUCTS API")
        print("=" * 30)
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test products list
        response = requests.get(f"{BASE_URL}/api/products/products/", headers=headers)
        
        if response.status_code == 200:
            products = response.json()
            
            if isinstance(products, dict) and 'results' in products:
                products = products['results']
            
            imagekit_count = 0
            broken_count = 0
            
            print(f"📊 Found {len(products)} products")
            
            for product in products[:5]:  # Test first 5 products
                product_name = product.get('name', 'Unknown')
                image_url = product.get('image', '')
                
                print(f"\n🔍 Testing: {product_name}")
                print(f"   Image URL: {image_url[:60]}...")
                
                if 'imagekit.io' in image_url:
                    # Test if URL is accessible
                    try:
                        img_response = requests.head(image_url, timeout=5)
                        if img_response.status_code == 200:
                            print(f"   ✅ ImageKit URL accessible")
                            imagekit_count += 1
                        else:
                            print(f"   ❌ ImageKit URL not accessible ({img_response.status_code})")
                            broken_count += 1
                    except Exception as e:
                        print(f"   ❌ URL test failed: {e}")
                        broken_count += 1
                else:
                    print(f"   ⚠️ Not an ImageKit URL")
                    broken_count += 1
            
            self.test_results.append({
                'endpoint': 'Products API',
                'total': len(products),
                'imagekit_working': imagekit_count,
                'broken': broken_count
            })
            
        else:
            print(f"❌ Products API failed: {response.status_code}")
    
    def test_categories_api(self):
        """Test categories API endpoints for ImageKit URLs"""
        print("\n🏷️ TESTING CATEGORIES API")
        print("=" * 30)
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test categories list
        response = requests.get(f"{BASE_URL}/api/products/categories/", headers=headers)
        
        if response.status_code == 200:
            categories = response.json()
            
            if isinstance(categories, dict) and 'results' in categories:
                categories = categories['results']
            
            imagekit_count = 0
            broken_count = 0
            
            print(f"📊 Found {len(categories)} categories")
            
            for category in categories[:5]:  # Test first 5 categories
                category_name = category.get('name', 'Unknown')
                icon_url = category.get('icon', '')
                
                print(f"\n🔍 Testing: {category_name}")
                print(f"   Icon URL: {icon_url[:60]}..." if icon_url else "   No icon")
                
                if icon_url and 'imagekit.io' in icon_url:
                    # Test if URL is accessible
                    try:
                        img_response = requests.head(icon_url, timeout=5)
                        if img_response.status_code == 200:
                            print(f"   ✅ ImageKit URL accessible")
                            imagekit_count += 1
                        else:
                            print(f"   ❌ ImageKit URL not accessible ({img_response.status_code})")
                            broken_count += 1
                    except Exception as e:
                        print(f"   ❌ URL test failed: {e}")
                        broken_count += 1
                elif icon_url:
                    print(f"   ⚠️ Not an ImageKit URL")
                    broken_count += 1
                else:
                    print(f"   ℹ️ No icon set")
            
            self.test_results.append({
                'endpoint': 'Categories API',
                'total': len(categories),
                'imagekit_working': imagekit_count,
                'broken': broken_count
            })
            
        else:
            print(f"❌ Categories API failed: {response.status_code}")
    
    def test_brands_api(self):
        """Test brands API endpoints for ImageKit URLs"""
        print("\n🏭 TESTING BRANDS API")
        print("=" * 25)
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test brands list
        response = requests.get(f"{BASE_URL}/api/products/brands/", headers=headers)
        
        if response.status_code == 200:
            brands = response.json()
            
            if isinstance(brands, dict) and 'results' in brands:
                brands = brands['results']
            
            imagekit_count = 0
            broken_count = 0
            
            print(f"📊 Found {len(brands)} brands")
            
            for brand in brands[:5]:  # Test first 5 brands
                brand_name = brand.get('name', 'Unknown')
                image_url = brand.get('image', '')
                
                print(f"\n🔍 Testing: {brand_name}")
                print(f"   Image URL: {image_url[:60]}..." if image_url else "   No image")
                
                if image_url and 'imagekit.io' in image_url:
                    # Test if URL is accessible
                    try:
                        img_response = requests.head(image_url, timeout=5)
                        if img_response.status_code == 200:
                            print(f"   ✅ ImageKit URL accessible")
                            imagekit_count += 1
                        else:
                            print(f"   ❌ ImageKit URL not accessible ({img_response.status_code})")
                            broken_count += 1
                    except Exception as e:
                        print(f"   ❌ URL test failed: {e}")
                        broken_count += 1
                elif image_url:
                    print(f"   ⚠️ Not an ImageKit URL")
                    broken_count += 1
                else:
                    print(f"   ℹ️ No image set")
            
            self.test_results.append({
                'endpoint': 'Brands API',
                'total': len(brands),
                'imagekit_working': imagekit_count,
                'broken': broken_count
            })
            
        else:
            print(f"❌ Brands API failed: {response.status_code}")
    
    def test_public_endpoints(self):
        """Test public endpoints (no authentication)"""
        print("\n🌐 TESTING PUBLIC ENDPOINTS")
        print("=" * 30)
        
        # Test public products
        response = requests.get(f"{BASE_URL}/api/products/products/")
        
        if response.status_code == 200:
            print("✅ Public products endpoint working")
            
            products = response.json()
            if isinstance(products, dict) and 'results' in products:
                products = products['results']
            
            if products:
                sample_product = products[0]
                product_name = sample_product.get('name', 'Unknown')
                image_url = sample_product.get('image', '')
                
                print(f"📦 Sample public product: {product_name}")
                print(f"   Image URL: {image_url}")
                
                if 'imagekit.io' in image_url:
                    print(f"   ✅ Public product has ImageKit URL")
                else:
                    print(f"   ❌ Public product missing ImageKit URL")
        else:
            print(f"❌ Public products endpoint failed: {response.status_code}")
        
        # Test public categories
        response = requests.get(f"{BASE_URL}/api/products/categories/")
        
        if response.status_code == 200:
            print("✅ Public categories endpoint working")
        else:
            print(f"❌ Public categories endpoint failed: {response.status_code}")
    
    def show_summary(self):
        """Show comprehensive test summary"""
        print("\n" + "=" * 50)
        print("📊 IMAGEKIT VERIFICATION SUMMARY")
        print("=" * 50)
        
        total_working = 0
        total_broken = 0
        total_items = 0
        
        for result in self.test_results:
            endpoint = result['endpoint']
            working = result['imagekit_working']
            broken = result['broken']
            total = result['total']
            
            total_working += working
            total_broken += broken
            total_items += total
            
            success_rate = (working / (working + broken) * 100) if (working + broken) > 0 else 0
            
            print(f"\n🔍 {endpoint}:")
            print(f"   Total items: {total}")
            print(f"   ✅ Working ImageKit URLs: {working}")
            print(f"   ❌ Broken/Missing URLs: {broken}")
            print(f"   📈 Success rate: {success_rate:.1f}%")
        
        overall_success = (total_working / (total_working + total_broken) * 100) if (total_working + total_broken) > 0 else 0
        
        print(f"\n🎯 OVERALL RESULTS:")
        print(f"   📦 Total items tested: {total_items}")
        print(f"   ✅ Working ImageKit URLs: {total_working}")
        print(f"   ❌ Broken/Missing URLs: {total_broken}")
        print(f"   📈 Overall success rate: {overall_success:.1f}%")
        
        if overall_success >= 90:
            print(f"\n🎉 EXCELLENT! ImageKit integration is working perfectly!")
        elif overall_success >= 70:
            print(f"\n✅ GOOD! Most images are working correctly")
        else:
            print(f"\n⚠️ NEEDS IMPROVEMENT: Some images still need fixing")
        
        return overall_success
    
    def run_complete_verification(self):
        """Run complete verification process"""
        print("🚀 STARTING IMAGEKIT VERIFICATION TEST")
        print("=" * 50)
        print(f"🕒 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Login
        if not self.login_admin():
            print("❌ Cannot proceed without admin access")
            return
        
        # Test all endpoints
        self.test_products_api()
        self.test_categories_api()
        self.test_brands_api()
        self.test_public_endpoints()
        
        # Show summary
        success_rate = self.show_summary()
        
        print(f"\n🌐 BROWSER TEST URLS:")
        print(f"   Products: {BASE_URL}/api/products/products/")
        print(f"   Categories: {BASE_URL}/api/products/categories/")
        print(f"   Brands: {BASE_URL}/api/products/brands/")
        
        return success_rate


def main():
    tester = ImageKitVerificationTester()
    success_rate = tester.run_complete_verification()
    
    if success_rate >= 90:
        print(f"\n✅ MISSION ACCOMPLISHED: ImageKit images are now working correctly!")
    else:
        print(f"\n⚠️ Some issues remain - check the summary above for details")


if __name__ == "__main__":
    main()