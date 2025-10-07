#!/usr/bin/env python3
"""
API Response Inspector
Inspects the actual response structure of public APIs
"""

import requests
import json

def inspect_api_responses():
    base_url = 'http://127.0.0.1:8000'
    
    print("🔍 Inspecting API Response Structures...")
    print("=" * 60)
    
    endpoints = [
        ('/api/public/products/categories/', 'Product Categories'),
        ('/api/public/products/brands/', 'Brands'),
        ('/api/public/products/products/', 'Products'),
        ('/api/public/products/search/', 'Product Search'),
        ('/api/cms/pages/', 'CMS Pages'),
        ('/api/cms/blog/categories/', 'Blog Categories'),
        ('/api/cms/blog/tags/', 'Blog Tags'),
    ]
    
    for endpoint, name in endpoints:
        print(f"\n📋 {name} ({endpoint})")
        print("-" * 40)
        
        try:
            response = requests.get(f"{base_url}{endpoint}")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"Response Type: {type(data)}")
                    
                    if isinstance(data, dict):
                        print(f"Dict Keys: {list(data.keys())}")
                        if 'results' in data:
                            print(f"Results Type: {type(data['results'])}")
                            print(f"Results Count: {len(data['results'])}")
                        if 'count' in data:
                            print(f"Total Count: {data['count']}")
                    elif isinstance(data, list):
                        print(f"List Length: {len(data)}")
                        if data:
                            print(f"First Item Type: {type(data[0])}")
                            print(f"First Item Keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not a dict'}")
                    
                    # Print first few characters for debugging
                    response_text = json.dumps(data, indent=2)[:500]
                    print(f"Response Preview: {response_text}...")
                    
                except json.JSONDecodeError:
                    print(f"Response Text: {response.text[:200]}...")
            else:
                print(f"Error Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"Error: {str(e)}")
    
    # Test swagger with better error handling
    print(f"\n📋 Swagger Documentation")
    print("-" * 40)
    try:
        swagger_response = requests.get(f"{base_url}/swagger.json")
        print(f"Status: {swagger_response.status_code}")
        if swagger_response.status_code == 200:
            if swagger_response.text.strip():
                swagger_data = swagger_response.json()
                print(f"✅ Swagger JSON is valid")
                print(f"API Title: {swagger_data.get('info', {}).get('title', 'Unknown')}")
            else:
                print("❌ Empty response")
        else:
            print(f"❌ Error: {swagger_response.text[:200]}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    inspect_api_responses()