"""
Enterprise-Level Search and Filter Testing Suite
==============================================

This script comprehensively tests the search and filter functionality of the ecommerce backend API
to identify performance issues and ensure enterprise-grade quality.

Test Categories:
1. Search Functionality Testing
2. Filter Functionality Testing 
3. Performance and Load Testing
4. Edge Case Testing
5. Security Testing
6. Response Validation

Author: Enterprise Testing Suite
Date: 2025-10-06
"""

import requests
import json
import time
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode, urljoin
import statistics
import random
import string
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import sys
import os


@dataclass
class TestResult:
    """Data class to store test results"""
    test_name: str
    endpoint: str
    method: str
    status_code: int
    response_time: float
    success: bool
    error_message: str = ""
    payload: dict = None
    response_data: dict = None


class EnterpriseSearchFilterTester:
    """
    Enterprise-level testing suite for search and filter functionality
    """
    
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip('/')
        self.test_results = []
        self.performance_metrics = {}
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Enterprise-Test-Suite/1.0'
        })
        
        # Test data - Include both private and public endpoints
        self.endpoints = {
            'products': '/api/products/',
            'categories': '/api/products/categories/',
            'brands': '/api/products/brands/',
            'variants': '/api/products/variants/',
            'reviews': '/api/products/reviews/',
            'attributes': '/api/products/attributes/',
            'attribute_values': '/api/products/attribute-values/',
            
            # Public endpoints for enterprise testing
            'public_products': '/api/public/products/products/',
            'public_categories': '/api/public/products/categories/',
            'public_brands': '/api/public/products/brands/',
            'public_search': '/api/public/products/search/',
            'public_featured': '/api/public/products/featured/',
        }
        
        # Authentication tokens (will be set during authentication)
        self.admin_token = None
        self.supplier_token = None
        self.user_token = None
        
    def log_result(self, result: TestResult):
        """Log test result"""
        self.test_results.append(result)
        status = "✅ PASS" if result.success else "❌ FAIL"
        print(f"[{status}] {result.test_name} - {result.response_time:.3f}s")
        if not result.success and result.error_message:
            print(f"    Error: {result.error_message}")
    
    def make_request(self, method: str, endpoint: str, params: dict = None, 
                    data: dict = None, auth_token: str = None) -> TestResult:
        """Make HTTP request and return test result"""
        url = urljoin(self.base_url, endpoint)
        headers = self.session.headers.copy()
        
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'
        
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, headers=headers, timeout=30)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, params=params, headers=headers, timeout=30)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, params=params, headers=headers, timeout=30)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=params, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response_time = time.time() - start_time
            
            # Try to parse JSON response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"raw_response": response.text}
            
            return TestResult(
                test_name="",
                endpoint=endpoint,
                method=method.upper(),
                status_code=response.status_code,
                response_time=response_time,
                success=200 <= response.status_code < 300,
                error_message="" if 200 <= response.status_code < 300 else f"HTTP {response.status_code}",
                payload=data or params,
                response_data=response_data
            )
        
        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            return TestResult(
                test_name="",
                endpoint=endpoint,
                method=method.upper(),
                status_code=0,
                response_time=response_time,
                success=False,
                error_message=str(e),
                payload=data or params,
                response_data={}
            )
    
    def test_basic_connectivity(self):
        """Test basic API connectivity"""
        print("\n🔍 Testing Basic API Connectivity...")
        
        for name, endpoint in self.endpoints.items():
            result = self.make_request('GET', endpoint)
            result.test_name = f"Basic connectivity - {name}"
            self.log_result(result)
    
    def test_search_functionality(self):
        """Test search functionality across all endpoints"""
        print("\n🔍 Testing Search Functionality...")
        
        search_terms = [
            "medicine",
            "equipment", 
            "test",
            "paracetamol",
            "surgical",
            "diagnostic",
            "antibiotics",
            "stethoscope",
            "medical",
            "health"
        ]
        
        search_endpoints = ['products', 'categories', 'brands', 'public_products', 'public_categories', 'public_brands']
        
        for endpoint_name in search_endpoints:
            endpoint = self.endpoints[endpoint_name]
            
            for search_term in search_terms:
                # Test basic search
                params = {'search': search_term}
                result = self.make_request('GET', endpoint, params=params)
                result.test_name = f"Search '{search_term}' in {endpoint_name}"
                self.log_result(result)
                
                # Test case insensitive search
                params = {'search': search_term.upper()}
                result = self.make_request('GET', endpoint, params=params)
                result.test_name = f"Case insensitive search '{search_term.upper()}' in {endpoint_name}"
                self.log_result(result)
                
                # Test partial search
                if len(search_term) > 3:
                    partial = search_term[:3]
                    params = {'search': partial}
                    result = self.make_request('GET', endpoint, params=params)
                    result.test_name = f"Partial search '{partial}' in {endpoint_name}"
                    self.log_result(result)
        
        # Test enterprise-level search via public search endpoint
        print("\n🔍 Testing Enterprise Search Features...")
        
        enterprise_search_tests = [
            # Basic query search
            {'q': 'medicine'},
            {'q': 'paracetamol tablet'},
            {'q': 'stethoscope medical equipment'},
            
            # Multi-parameter searches
            {'q': 'medicine', 'product_type': 'medicine'},
            {'q': 'equipment', 'product_type': 'equipment'},
            {'q': 'diagnostic', 'product_type': 'pathology'},
            
            # Price range searches
            {'q': 'medicine', 'min_price': '10', 'max_price': '100'},
            {'q': 'equipment', 'min_price': '100'},
            {'max_price': '500'},
            
            # Sorting tests
            {'q': 'medicine', 'sort_by': 'price_low'},
            {'q': 'medicine', 'sort_by': 'price_high'},
            {'q': 'medicine', 'sort_by': 'name_asc'},
            {'q': 'medicine', 'sort_by': 'name_desc'},
            {'q': 'medicine', 'sort_by': 'newest'},
            {'q': 'medicine', 'sort_by': 'oldest'},
            {'q': 'medicine', 'sort_by': 'relevance'},
            
            # Pagination with search
            {'q': 'medicine', 'page': '1'},
            {'q': 'medicine', 'page': '2'},
            
            # Empty search query
            {'q': ''},
            
            # Complex multi-word searches
            {'q': 'pain relief medicine tablet'},
            {'q': 'blood pressure monitor equipment'},
        ]
        
        for search_params in enterprise_search_tests:
            result = self.make_request('GET', self.endpoints['public_search'], params=search_params)
            result.test_name = f"Enterprise search: {search_params}"
            self.log_result(result)
    
    def test_filter_functionality(self):
        """Test filter functionality"""
        print("\n🔍 Testing Filter Functionality...")
        
        # Test product filters (private API)
        product_filters = [
            {'product_type': 'medicine'},
            {'product_type': 'equipment'},
            {'product_type': 'pathology'},
            {'status': 'published'},
            {'status': 'approved'},
            {'is_publish': 'true'},
            {'is_publish': 'false'},
        ]
        
        for filter_params in product_filters:
            result = self.make_request('GET', self.endpoints['products'], params=filter_params)
            result.test_name = f"Filter products by {filter_params}"
            self.log_result(result)
        
        # Test public product filters
        public_product_filters = [
            {'product_type': 'medicine'},
            {'product_type': 'equipment'},
            {'product_type': 'pathology'},
            {'ordering': 'price'},
            {'ordering': '-price'},
            {'ordering': 'created_at'},
            {'ordering': '-created_at'},
            {'ordering': 'name'},
            {'ordering': '-name'},
        ]
        
        for filter_params in public_product_filters:
            result = self.make_request('GET', self.endpoints['public_products'], params=filter_params)
            result.test_name = f"Filter public products by {filter_params}"
            self.log_result(result)
        
        # Test review filters
        review_filters = [
            {'rating': '5'},
            {'rating': '4'},
            {'rating': '3'},
            {'rating': '2'},
            {'rating': '1'},
        ]
        
        for filter_params in review_filters:
            result = self.make_request('GET', self.endpoints['reviews'], params=filter_params)
            result.test_name = f"Filter reviews by {filter_params}"
            self.log_result(result)
        
        # Test attribute value filters
        result = self.make_request('GET', self.endpoints['attribute_values'])
        if result.success and result.response_data.get('results'):
            # Get first attribute if available
            attributes = result.response_data['results']
            if attributes:
                first_attr = attributes[0]
                if 'attribute' in first_attr:
                    attr_filter = {'attribute': first_attr['attribute']}
                    result = self.make_request('GET', self.endpoints['attribute_values'], params=attr_filter)
                    result.test_name = f"Filter attribute values by attribute {first_attr['attribute']}"
                    self.log_result(result)
                    
        # Test featured products endpoint
        result = self.make_request('GET', self.endpoints['public_featured'])
        result.test_name = "Featured products endpoint"
        self.log_result(result)
    
    def test_combined_search_and_filter(self):
        """Test combination of search and filter parameters"""
        print("\n🔍 Testing Combined Search and Filter...")
        
        combined_tests = [
            {
                'endpoint': 'products',
                'params': {'search': 'medicine', 'product_type': 'medicine'}
            },
            {
                'endpoint': 'products', 
                'params': {'search': 'equipment', 'product_type': 'equipment', 'is_publish': 'true'}
            },
            {
                'endpoint': 'products',
                'params': {'search': 'test', 'status': 'published'}
            },
            {
                'endpoint': 'categories',
                'params': {'search': 'medical', 'page': '1'}
            },
            {
                'endpoint': 'brands',
                'params': {'search': 'brand'}
            }
        ]
        
        for test in combined_tests:
            endpoint = self.endpoints[test['endpoint']]
            result = self.make_request('GET', endpoint, params=test['params'])
            result.test_name = f"Combined search+filter: {test['params']}"
            self.log_result(result)
    
    def test_ordering_functionality(self):
        """Test ordering functionality"""
        print("\n🔍 Testing Ordering Functionality...")
        
        ordering_tests = [
            {'endpoint': 'products', 'params': {'ordering': 'price'}},
            {'endpoint': 'products', 'params': {'ordering': '-price'}},
            {'endpoint': 'products', 'params': {'ordering': 'created_at'}},
            {'endpoint': 'products', 'params': {'ordering': '-created_at'}},
            {'endpoint': 'products', 'params': {'ordering': 'name'}},
            {'endpoint': 'products', 'params': {'ordering': '-name'}},
        ]
        
        for test in ordering_tests:
            endpoint = self.endpoints[test['endpoint']]
            result = self.make_request('GET', endpoint, params=test['params'])
            result.test_name = f"Ordering: {test['params']}"
            self.log_result(result)
    
    def test_pagination(self):
        """Test pagination functionality"""
        print("\n🔍 Testing Pagination...")
        
        pagination_tests = [
            {'page': '1'},
            {'page': '2'},
            {'page': '1', 'page_size': '5'},
            {'page': '1', 'page_size': '10'},
            {'page': '1', 'page_size': '50'},
            {'page': '1', 'page_size': '100'},
        ]
        
        for params in pagination_tests:
            result = self.make_request('GET', self.endpoints['products'], params=params)
            result.test_name = f"Pagination: {params}"
            self.log_result(result)
    
    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        print("\n🔍 Testing Edge Cases...")
        
        edge_cases = [
            # Empty search
            {'endpoint': 'products', 'params': {'search': ''}},
            
            # Very long search terms
            {'endpoint': 'products', 'params': {'search': 'a' * 1000}},
            
            # Special characters in search
            {'endpoint': 'products', 'params': {'search': '!@#$%^&*()'}},
            
            # SQL injection attempts
            {'endpoint': 'products', 'params': {'search': "'; DROP TABLE products; --"}},
            
            # Invalid filter values
            {'endpoint': 'products', 'params': {'product_type': 'invalid_type'}},
            
            # Invalid pagination
            {'endpoint': 'products', 'params': {'page': '0'}},
            {'endpoint': 'products', 'params': {'page': '-1'}},
            {'endpoint': 'products', 'params': {'page': 'invalid'}},
            {'endpoint': 'products', 'params': {'page_size': '0'}},
            {'endpoint': 'products', 'params': {'page_size': '-1'}},
            {'endpoint': 'products', 'params': {'page_size': '10000'}},
            
            # Invalid ordering
            {'endpoint': 'products', 'params': {'ordering': 'invalid_field'}},
            
            # Unicode search terms
            {'endpoint': 'products', 'params': {'search': '医药用品'}},
            {'endpoint': 'products', 'params': {'search': 'मेडिसिन'}},
            
            # Very large page numbers
            {'endpoint': 'products', 'params': {'page': '999999'}},
        ]
        
        for test in edge_cases:
            endpoint = self.endpoints[test['endpoint']]
            result = self.make_request('GET', endpoint, params=test['params'])
            result.test_name = f"Edge case: {test['params']}"
            # Edge cases might legitimately fail, so we track them but don't fail the test
            self.log_result(result)
    
    def test_performance_load(self):
        """Test performance under load"""
        print("\n🔍 Testing Performance Under Load...")
        
        # Sequential performance test
        start_time = time.time()
        response_times = []
        
        for i in range(50):  # 50 sequential requests
            result = self.make_request('GET', self.endpoints['products'], 
                                     params={'search': f'test{i % 10}'})
            response_times.append(result.response_time)
            
            result.test_name = f"Sequential load test {i+1}/50"
            self.log_result(result)
        
        total_time = time.time() - start_time
        
        # Calculate performance metrics
        self.performance_metrics['sequential_total_time'] = total_time
        self.performance_metrics['sequential_avg_response_time'] = statistics.mean(response_times)
        self.performance_metrics['sequential_median_response_time'] = statistics.median(response_times)
        self.performance_metrics['sequential_max_response_time'] = max(response_times)
        self.performance_metrics['sequential_min_response_time'] = min(response_times)
        
        print(f"Sequential Performance Metrics:")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Avg response: {self.performance_metrics['sequential_avg_response_time']:.3f}s")
        print(f"  Median response: {self.performance_metrics['sequential_median_response_time']:.3f}s")
        print(f"  Max response: {self.performance_metrics['sequential_max_response_time']:.3f}s")
        print(f"  Min response: {self.performance_metrics['sequential_min_response_time']:.3f}s")
    
    def test_concurrent_load(self):
        """Test concurrent load performance"""
        print("\n🔍 Testing Concurrent Load Performance...")
        
        def make_concurrent_request(i):
            return self.make_request('GET', self.endpoints['products'], 
                                   params={'search': f'concurrent{i % 10}'})
        
        start_time = time.time()
        
        # Use ThreadPoolExecutor for concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_concurrent_request, i) for i in range(20)]
            results = [future.result() for future in futures]
        
        total_time = time.time() - start_time
        response_times = [r.response_time for r in results]
        
        # Log individual results
        for i, result in enumerate(results):
            result.test_name = f"Concurrent load test {i+1}/20"
            self.log_result(result)
        
        # Calculate concurrent performance metrics
        self.performance_metrics['concurrent_total_time'] = total_time
        self.performance_metrics['concurrent_avg_response_time'] = statistics.mean(response_times)
        self.performance_metrics['concurrent_median_response_time'] = statistics.median(response_times)
        self.performance_metrics['concurrent_max_response_time'] = max(response_times)
        self.performance_metrics['concurrent_min_response_time'] = min(response_times)
        
        print(f"Concurrent Performance Metrics:")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Avg response: {self.performance_metrics['concurrent_avg_response_time']:.3f}s")
        print(f"  Median response: {self.performance_metrics['concurrent_median_response_time']:.3f}s")
        print(f"  Max response: {self.performance_metrics['concurrent_max_response_time']:.3f}s")
        print(f"  Min response: {self.performance_metrics['concurrent_min_response_time']:.3f}s")
    
    def test_data_consistency(self):
        """Test data consistency in responses"""
        print("\n🔍 Testing Data Consistency...")
        
        # Test that search results are consistent
        for _ in range(5):
            result1 = self.make_request('GET', self.endpoints['products'], 
                                      params={'search': 'medicine'})
            result2 = self.make_request('GET', self.endpoints['products'], 
                                      params={'search': 'medicine'})
            
            consistent = (result1.response_data.get('count') == 
                         result2.response_data.get('count'))
            
            test_result = TestResult(
                test_name="Data consistency check",
                endpoint=self.endpoints['products'],
                method='GET',
                status_code=200 if consistent else 500,
                response_time=0,
                success=consistent,
                error_message="Inconsistent results" if not consistent else ""
            )
            self.log_result(test_result)
    
    def test_response_structure(self):
        """Test response structure validation"""
        print("\n🔍 Testing Response Structure...")
        
        # Expected response structure for products
        expected_product_fields = {
            'count', 'next', 'previous', 'results'
        }
        
        expected_product_item_fields = {
            'id', 'name', 'slug', 'sku', 'brand', 'category', 
            'description', 'image', 'created_by', 'created_at', 
            'updated_at', 'is_publish', 'status', 'product_type', 
            'price', 'stock', 'specifications', 'tags'
        }
        
        result = self.make_request('GET', self.endpoints['products'], params={'page': '1'})
        
        if result.success and result.response_data:
            # Check top-level structure
            actual_fields = set(result.response_data.keys())
            missing_fields = expected_product_fields - actual_fields
            extra_fields = actual_fields - expected_product_fields
            
            structure_valid = len(missing_fields) == 0
            
            test_result = TestResult(
                test_name="Response structure validation - top level",
                endpoint=self.endpoints['products'],
                method='GET',
                status_code=200 if structure_valid else 422,
                response_time=0,
                success=structure_valid,
                error_message=f"Missing: {missing_fields}, Extra: {extra_fields}" if not structure_valid else ""
            )
            self.log_result(test_result)
            
            # Check product item structure
            if 'results' in result.response_data and result.response_data['results']:
                first_product = result.response_data['results'][0]
                actual_item_fields = set(first_product.keys())
                missing_item_fields = expected_product_item_fields - actual_item_fields
                
                item_structure_valid = len(missing_item_fields) == 0
                
                test_result = TestResult(
                    test_name="Response structure validation - product item",
                    endpoint=self.endpoints['products'],
                    method='GET',
                    status_code=200 if item_structure_valid else 422,
                    response_time=0,
                    success=item_structure_valid,
                    error_message=f"Missing item fields: {missing_item_fields}" if not item_structure_valid else ""
                )
                self.log_result(test_result)
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("ENTERPRISE SEARCH & FILTER TEST REPORT")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 SUMMARY")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.2f}%")
        
        print(f"\n⚡ PERFORMANCE METRICS")
        if self.performance_metrics:
            for metric, value in self.performance_metrics.items():
                print(f"  {metric}: {value:.3f}s")
        
        # Failed tests summary
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS")
            for result in self.test_results:
                if not result.success:
                    print(f"  {result.test_name}: {result.error_message}")
        
        # Response time analysis
        response_times = [r.response_time for r in self.test_results if r.success]
        if response_times:
            print(f"\n⏱️ RESPONSE TIME ANALYSIS")
            print(f"  Average: {statistics.mean(response_times):.3f}s")
            print(f"  Median: {statistics.median(response_times):.3f}s")
            print(f"  Max: {max(response_times):.3f}s")
            print(f"  Min: {min(response_times):.3f}s")
            
            # Enterprise-level benchmarks
            print(f"\n🏢 ENTERPRISE BENCHMARK ANALYSIS")
            fast_responses = sum(1 for t in response_times if t < 0.5)
            medium_responses = sum(1 for t in response_times if 0.5 <= t < 2.0)
            slow_responses = sum(1 for t in response_times if t >= 2.0)
            
            print(f"  Fast (<0.5s): {fast_responses} ({fast_responses/len(response_times)*100:.1f}%)")
            print(f"  Medium (0.5-2s): {medium_responses} ({medium_responses/len(response_times)*100:.1f}%)")
            print(f"  Slow (>2s): {slow_responses} ({slow_responses/len(response_times)*100:.1f}%)")
            
            if slow_responses > 0:
                print(f"  ⚠️ WARNING: {slow_responses} responses were slower than 2s (enterprise threshold)")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        
        if success_rate < 95:
            print("  🔴 CRITICAL: Success rate below 95% - immediate attention required")
        elif success_rate < 99:
            print("  🟡 WARNING: Success rate below 99% - optimization needed")
        else:
            print("  🟢 EXCELLENT: Success rate meets enterprise standards")
        
        if response_times and statistics.mean(response_times) > 1.0:
            print("  🔴 CRITICAL: Average response time > 1s - performance optimization required")
        elif response_times and statistics.mean(response_times) > 0.5:
            print("  🟡 WARNING: Average response time > 0.5s - consider optimization")
        else:
            print("  🟢 EXCELLENT: Response times meet enterprise standards")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'performance_metrics': self.performance_metrics,
            'enterprise_ready': success_rate >= 99 and (not response_times or statistics.mean(response_times) <= 0.5)
        }
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Enterprise Search & Filter Test Suite")
        print(f"Base URL: {self.base_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all test suites
        self.test_basic_connectivity()
        self.test_search_functionality()
        self.test_filter_functionality()
        self.test_combined_search_and_filter()
        self.test_ordering_functionality()
        self.test_pagination()
        self.test_edge_cases()
        self.test_performance_load()
        self.test_concurrent_load()
        self.test_data_consistency()
        self.test_response_structure()
        
        # Generate final report
        return self.generate_report()


def main():
    """Main function to run the test suite"""
    # You can modify the base URL as needed
    base_url = "http://127.0.0.1:8000"
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    tester = EnterpriseSearchFilterTester(base_url)
    report = tester.run_all_tests()
    
    # Exit with appropriate code
    if report['enterprise_ready']:
        print("\n🎉 ENTERPRISE READY: All tests passed with enterprise-grade performance!")
        sys.exit(0)
    else:
        print("\n⚠️ NOT ENTERPRISE READY: Optimization required before production deployment")
        sys.exit(1)


if __name__ == "__main__":
    main()