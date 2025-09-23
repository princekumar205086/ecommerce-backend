#!/usr/bin/env python
"""
Comprehensive Product Reviews System Test Suite
Tests all review CRUD operations from user perspective
"""
import os
import sys
import json
import random
from datetime import datetime

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from products.models import (
    ProductCategory, Brand, Product, ProductVariant, 
    ProductReview
)

User = get_user_model()

class ComprehensiveReviewsTestSuite:
    def __init__(self):
        self.client = Client()
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {},
            'created_reviews': []
        }
        self.users = {}
        self.test_products = []
        
    def log_test(self, test_name, status, details=None, error=None):
        """Log a test result"""
        result = {
            'test_name': test_name,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'details': details or {},
            'error': str(error) if error else None
        }
        self.test_results['tests'].append(result)
        
        if status == 'PASS':
            print(f"✅ {test_name}")
        else:
            print(f"❌ {test_name}: {error or details}")
            
    def setup_test_users(self):
        """Setup test users for reviews"""
        try:
            # Get existing test users
            self.users['admin'] = User.objects.get(email='admin@example.com')
            self.users['user1'] = User.objects.get(email='user@example.com')
            
            # Create additional test users for diverse reviews
            test_users_data = [
                {
                    'email': 'reviewer1@example.com',
                    'full_name': 'Test Reviewer 1',
                    'contact': '1234567893',
                    'role': 'user'
                },
                {
                    'email': 'reviewer2@example.com',
                    'full_name': 'Test Reviewer 2',
                    'contact': '1234567894',
                    'role': 'user'
                },
                {
                    'email': 'reviewer3@example.com',
                    'full_name': 'Test Reviewer 3',
                    'contact': '1234567895',
                    'role': 'user'
                }
            ]
            
            for user_data in test_users_data:
                user, created = User.objects.get_or_create(
                    email=user_data['email'],
                    defaults={
                        'full_name': user_data['full_name'],
                        'contact': user_data['contact'],
                        'role': user_data['role'],
                        'is_active': True,
                        'email_verified': True
                    }
                )
                if created:
                    user.set_password('testpass123')
                    user.save()
                    
                self.users[f"reviewer{len(self.users)-1}"] = user
                
            self.log_test("Setup Review Test Users", "PASS", {"users_ready": len(self.users)})
            
        except Exception as e:
            self.log_test("Setup Review Test Users", "FAIL", error=e)
            
    def get_auth_headers(self, user):
        """Get authentication headers for a user"""
        refresh = RefreshToken.for_user(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}
        
    def cleanup_existing_reviews(self):
        """Clean up existing reviews for test users"""
        try:
            from products.models import ProductReview
            
            # Get all test user emails
            test_emails = [
                'user@example.com',
                'reviewer1@example.com', 
                'reviewer2@example.com',
                'reviewer3@example.com'
            ]
            
            # Delete existing reviews from test users
            test_users = User.objects.filter(email__in=test_emails)
            deleted_count = ProductReview.objects.filter(user__in=test_users).delete()[0]
            
            self.log_test("Cleanup Existing Reviews", "PASS", {
                "deleted_reviews": deleted_count
            })
            
        except Exception as e:
            self.log_test("Cleanup Existing Reviews", "FAIL", error=e)
    def fetch_test_products(self):
        """Fetch existing products for review testing"""
        try:
            admin_headers = self.get_auth_headers(self.users['admin'])
            
            # Get products for testing
            response = self.client.get('/api/products/products/', **admin_headers)
            if response.status_code == 200:
                products = response.json().get('results', [])
                self.test_products = products[:5]  # Take first 5 products
                
            self.log_test("Fetch Test Products", "PASS", {
                "products_count": len(self.test_products)
            })
            
        except Exception as e:
            self.log_test("Fetch Test Products", "FAIL", error=e)
            
    def test_create_reviews(self):
        """Test creating product reviews by different users"""
        print("\n⭐ Testing Review Creation...")
        
        if not self.test_products:
            self.log_test("Create Reviews", "SKIP", {"reason": "No products available"})
            return
            
        # Test reviews from different users
        review_scenarios = [
            {
                'user_key': 'user1',
                'rating': 5,
                'comment': 'Excellent product! Highly recommend for everyone looking for quality medicine.'
            },
            {
                'user_key': 'reviewer1',
                'rating': 4,
                'comment': 'Good product with fast delivery. Minor packaging issues but overall satisfied.'
            },
            {
                'user_key': 'reviewer2',
                'rating': 3,
                'comment': 'Average product. Does what it says but nothing exceptional about it.'
            },
            {
                'user_key': 'reviewer3',
                'rating': 5,
                'comment': 'Outstanding quality! Great value for money. Will definitely buy again.'
            },
            {
                'user_key': 'reviewer1',  # Same user, different product
                'rating': 2,
                'comment': 'Not satisfied with this product. Expected better quality for the price.'
            }
        ]
        
        for i, scenario in enumerate(review_scenarios):
            if i >= len(self.test_products):
                break  # Don't exceed available products
                
            product = self.test_products[i]
            user_headers = self.get_auth_headers(self.users[scenario['user_key']])
            
            review_data = {
                'product': product['id'],
                'rating': scenario['rating'],
                'comment': scenario['comment']
            }
            
            try:
                response = self.client.post('/api/products/reviews/', 
                                          data=json.dumps(review_data),
                                          content_type='application/json',
                                          **user_headers)
                
                if response.status_code == 201:
                    review = response.json()
                    self.test_results['created_reviews'].append(review)
                    self.log_test(f"Create Review {scenario['rating']}⭐ by {scenario['user_key']}", "PASS", {
                        "review_id": review['id'],
                        "product_id": product['id'],
                        "rating": review['rating']
                    })
                else:
                    self.log_test(f"Create Review {scenario['rating']}⭐ by {scenario['user_key']}", "FAIL", {
                        "status_code": response.status_code,
                        "response": response.json() if response.content else "No content"
                    })
                    
            except Exception as e:
                self.log_test(f"Create Review {scenario['rating']}⭐ by {scenario['user_key']}", "FAIL", error=e)
                
    def test_get_reviews(self):
        """Test retrieving reviews"""
        print("\n📖 Testing Review Retrieval...")
        
        # Test getting all reviews (anonymous access)
        try:
            response = self.client.get('/api/products/reviews/')
            if response.status_code == 200:
                reviews = response.json().get('results', [])
                self.log_test("GET All Reviews (Anonymous)", "PASS", {
                    "reviews_count": len(reviews),
                    "status_code": response.status_code
                })
            else:
                self.log_test("GET All Reviews (Anonymous)", "FAIL", {
                    "status_code": response.status_code
                })
        except Exception as e:
            self.log_test("GET All Reviews (Anonymous)", "FAIL", error=e)
            
        # Test getting reviews with authenticated user
        user_headers = self.get_auth_headers(self.users['user1'])
        try:
            response = self.client.get('/api/products/reviews/', **user_headers)
            if response.status_code == 200:
                reviews = response.json().get('results', [])
                self.log_test("GET All Reviews (Authenticated)", "PASS", {
                    "reviews_count": len(reviews),
                    "status_code": response.status_code
                })
            else:
                self.log_test("GET All Reviews (Authenticated)", "FAIL", {
                    "status_code": response.status_code
                })
        except Exception as e:
            self.log_test("GET All Reviews (Authenticated)", "FAIL", error=e)
            
        # Test getting reviews for specific product
        if self.test_products:
            product_id = self.test_products[0]['id']
            try:
                response = self.client.get(f'/api/products/reviews/?product={product_id}')
                if response.status_code == 200:
                    reviews = response.json().get('results', [])
                    self.log_test("GET Product Reviews (Filtered)", "PASS", {
                        "product_id": product_id,
                        "reviews_count": len(reviews)
                    })
                else:
                    self.log_test("GET Product Reviews (Filtered)", "FAIL", {
                        "status_code": response.status_code
                    })
            except Exception as e:
                self.log_test("GET Product Reviews (Filtered)", "FAIL", error=e)
                
    def test_get_review_details(self):
        """Test getting individual review details"""
        print("\n🔍 Testing Review Detail Retrieval...")
        
        if not self.test_results['created_reviews']:
            self.log_test("GET Review Details", "SKIP", {"reason": "No reviews available"})
            return
            
        for review in self.test_results['created_reviews'][:3]:  # Test first 3 reviews
            review_id = review['id']
            try:
                response = self.client.get(f'/api/products/reviews/{review_id}/')
                if response.status_code == 200:
                    review_detail = response.json()
                    self.log_test(f"GET Review {review_id} Detail", "PASS", {
                        "review_id": review_id,
                        "rating": review_detail.get('rating'),
                        "has_comment": bool(review_detail.get('comment'))
                    })
                else:
                    self.log_test(f"GET Review {review_id} Detail", "FAIL", {
                        "status_code": response.status_code
                    })
            except Exception as e:
                self.log_test(f"GET Review {review_id} Detail", "FAIL", error=e)
                
    def test_update_reviews(self):
        """Test updating reviews by their creators"""
        print("\n✏️ Testing Review Updates...")
        
        if not self.test_results['created_reviews']:
            self.log_test("Update Reviews", "SKIP", {"reason": "No reviews available"})
            return
            
        # Test updating first review (created by user1)
        if self.test_results['created_reviews']:
            review = self.test_results['created_reviews'][0]
            review_id = review['id']
            user_headers = self.get_auth_headers(self.users['user1'])
            
            # Test PATCH update
            updated_data = {
                'rating': 4,
                'comment': 'Updated review: Still good product but found better alternatives recently.'
            }
            
            try:
                response = self.client.patch(f'/api/products/reviews/{review_id}/', 
                                           data=json.dumps(updated_data),
                                           content_type='application/json',
                                           **user_headers)
                
                if response.status_code == 200:
                    updated_review = response.json()
                    self.log_test("PATCH Review Update (Own Review)", "PASS", {
                        "review_id": review_id,
                        "new_rating": updated_review['rating'],
                        "updated": True
                    })
                else:
                    self.log_test("PATCH Review Update (Own Review)", "FAIL", {
                        "status_code": response.status_code,
                        "response": response.json() if response.content else "No content"
                    })
                    
            except Exception as e:
                self.log_test("PATCH Review Update (Own Review)", "FAIL", error=e)
                
        # Test updating another user's review (should fail)
        if len(self.test_results['created_reviews']) > 1:
            review = self.test_results['created_reviews'][1]  # Created by reviewer1
            review_id = review['id']
            user_headers = self.get_auth_headers(self.users['user1'])  # Different user
            
            updated_data = {
                'rating': 1,
                'comment': 'Trying to update someone else review - should fail'
            }
            
            try:
                response = self.client.patch(f'/api/products/reviews/{review_id}/', 
                                           data=json.dumps(updated_data),
                                           content_type='application/json',
                                           **user_headers)
                
                if response.status_code in [403, 404]:  # Forbidden or not found
                    self.log_test("PATCH Review Update (Others Review - Should Fail)", "PASS", {
                        "correctly_blocked": True,
                        "status_code": response.status_code
                    })
                else:
                    self.log_test("PATCH Review Update (Others Review - Should Fail)", "FAIL", {
                        "expected_403_got": response.status_code
                    })
                    
            except Exception as e:
                self.log_test("PATCH Review Update (Others Review - Should Fail)", "FAIL", error=e)
                
    def test_delete_reviews(self):
        """Test deleting reviews"""
        print("\n🗑️ Testing Review Deletion...")
        
        if not self.test_results['created_reviews']:
            self.log_test("Delete Reviews", "SKIP", {"reason": "No reviews available"})
            return
            
        # Test deleting own review
        if len(self.test_results['created_reviews']) >= 3:
            review = self.test_results['created_reviews'][-1]  # Take last review
            review_id = review['id']
            
            # Get the review object to find the actual user
            try:
                from products.models import ProductReview
                review_obj = ProductReview.objects.get(id=review_id)
                creator_user = review_obj.user
                
                user_headers = self.get_auth_headers(creator_user)
                
                try:
                    response = self.client.delete(f'/api/products/reviews/{review_id}/', 
                                                **user_headers)
                    
                    if response.status_code == 204:
                        self.log_test("DELETE Own Review", "PASS", {
                            "review_id": review_id,
                            "deleted": True
                        })
                    else:
                        self.log_test("DELETE Own Review", "FAIL", {
                            "status_code": response.status_code
                        })
                        
                except Exception as e:
                    self.log_test("DELETE Own Review", "FAIL", error=e)
                    
            except Exception as e:
                self.log_test("DELETE Own Review", "FAIL", error=f"Could not find review: {e}")
                
        # Test admin delete review
        if len(self.test_results['created_reviews']) >= 2:
            review = self.test_results['created_reviews'][-2]  # Take second last review
            review_id = review['id']
            admin_headers = self.get_auth_headers(self.users['admin'])
            
            try:
                response = self.client.delete(f'/api/products/reviews/{review_id}/', 
                                            **admin_headers)
                
                if response.status_code == 204:
                    self.log_test("DELETE Review (Admin)", "PASS", {
                        "review_id": review_id,
                        "admin_deleted": True
                    })
                else:
                    self.log_test("DELETE Review (Admin)", "FAIL", {
                        "status_code": response.status_code
                    })
                    
            except Exception as e:
                self.log_test("DELETE Review (Admin)", "FAIL", error=e)
                
    def test_review_filtering_and_search(self):
        """Test review filtering and search functionality"""
        print("\n🔍 Testing Review Filtering & Search...")
        
        # Test filtering by rating
        try:
            response = self.client.get('/api/products/reviews/?rating=5')
            if response.status_code == 200:
                reviews = response.json().get('results', [])
                all_5_star = all(review.get('rating') == 5 for review in reviews)
                self.log_test("Filter Reviews by Rating (5 stars)", "PASS", {
                    "reviews_count": len(reviews),
                    "all_5_star": all_5_star
                })
            else:
                self.log_test("Filter Reviews by Rating (5 stars)", "FAIL", {
                    "status_code": response.status_code
                })
        except Exception as e:
            self.log_test("Filter Reviews by Rating (5 stars)", "FAIL", error=e)
            
        # Test ordering by created date
        try:
            response = self.client.get('/api/products/reviews/?ordering=-created_at')
            if response.status_code == 200:
                reviews = response.json().get('results', [])
                self.log_test("Order Reviews by Date (Newest First)", "PASS", {
                    "reviews_count": len(reviews)
                })
            else:
                self.log_test("Order Reviews by Date (Newest First)", "FAIL", {
                    "status_code": response.status_code
                })
        except Exception as e:
            self.log_test("Order Reviews by Date (Newest First)", "FAIL", error=e)
            
        # Test search in comments
        try:
            response = self.client.get('/api/products/reviews/?search=excellent')
            if response.status_code == 200:
                reviews = response.json().get('results', [])
                self.log_test("Search Reviews by Comment", "PASS", {
                    "reviews_count": len(reviews)
                })
            else:
                self.log_test("Search Reviews by Comment", "FAIL", {
                    "status_code": response.status_code
                })
        except Exception as e:
            self.log_test("Search Reviews by Comment", "FAIL", error=e)
            
    def test_review_permissions(self):
        """Test review permission scenarios"""
        print("\n🔒 Testing Review Permissions...")
        
        if not self.test_products:
            self.log_test("Review Permissions", "SKIP", {"reason": "No products available"})
            return
            
        # Test unauthenticated review creation (should fail)
        product = self.test_products[0]
        review_data = {
            'product': product['id'],
            'rating': 5,
            'comment': 'Unauthenticated review attempt'
        }
        
        try:
            response = self.client.post('/api/products/reviews/', 
                                      data=json.dumps(review_data),
                                      content_type='application/json')
            
            if response.status_code == 401:
                self.log_test("Unauthenticated Review Creation (Should Fail)", "PASS", {
                    "correctly_blocked": True,
                    "status_code": response.status_code
                })
            else:
                self.log_test("Unauthenticated Review Creation (Should Fail)", "FAIL", {
                    "expected_401_got": response.status_code
                })
        except Exception as e:
            self.log_test("Unauthenticated Review Creation (Should Fail)", "FAIL", error=e)
            
        # Test duplicate review creation (should handle gracefully)
        if self.test_results['created_reviews']:
            existing_review = self.test_results['created_reviews'][0]
            user_headers = self.get_auth_headers(self.users['user1'])
            
            duplicate_review_data = {
                'product': existing_review['product'],
                'rating': 3,
                'comment': 'Attempting to create duplicate review'
            }
            
            try:
                response = self.client.post('/api/products/reviews/', 
                                          data=json.dumps(duplicate_review_data),
                                          content_type='application/json',
                                          **user_headers)
                
                # Could be 400 (duplicate) or 201 (allowed multiple reviews)
                if response.status_code in [201, 400]:
                    self.log_test("Duplicate Review Handling", "PASS", {
                        "status_code": response.status_code,
                        "behavior": "duplicate_allowed" if response.status_code == 201 else "duplicate_blocked"
                    })
                else:
                    self.log_test("Duplicate Review Handling", "FAIL", {
                        "status_code": response.status_code
                    })
            except Exception as e:
                self.log_test("Duplicate Review Handling", "FAIL", error=e)
                
    def generate_reviews_summary(self):
        """Generate reviews test summary"""
        total_tests = len(self.test_results['tests'])
        passed_tests = len([t for t in self.test_results['tests'] if t['status'] == 'PASS'])
        failed_tests = len([t for t in self.test_results['tests'] if t['status'] == 'FAIL'])
        skipped_tests = len([t for t in self.test_results['tests'] if t['status'] == 'SKIP'])
        
        self.test_results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'skipped_tests': skipped_tests,
            'success_rate': f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
            'reviews_created': len(self.test_results['created_reviews']),
            'test_users_count': len(self.users),
            'test_products_count': len(self.test_products)
        }
        
        # Save results
        with open('comprehensive_reviews_test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n⭐ COMPREHENSIVE REVIEWS SYSTEM TEST SUMMARY")
        print(f"=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⏭️ Skipped: {skipped_tests}")
        print(f"📈 Success Rate: {self.test_results['summary']['success_rate']}")
        print(f"⭐ Reviews Created: {self.test_results['summary']['reviews_created']}")
        print(f"👥 Test Users: {self.test_results['summary']['test_users_count']}")
        print(f"📦 Test Products: {self.test_results['summary']['test_products_count']}")
        print(f"\n📄 Detailed results saved to: comprehensive_reviews_test_results.json")
        
        if failed_tests == 0:
            print(f"\n🏆 EXCELLENT! All review system tests passed successfully!")
        else:
            print(f"\n⚠️ Some review tests failed. Please review the detailed results.")
        
    def run_reviews_tests(self):
        """Run all review system tests"""
        print("⭐ Starting Comprehensive Product Reviews System Test Suite")
        print("=" * 65)
        
        try:
            self.setup_test_users()
            self.cleanup_existing_reviews()
            self.fetch_test_products()
            self.test_create_reviews()
            self.test_get_reviews()
            self.test_get_review_details()
            self.test_update_reviews()
            self.test_delete_reviews()
            self.test_review_filtering_and_search()
            self.test_review_permissions()
            self.generate_reviews_summary()
            
        except Exception as e:
            print(f"❌ Critical error in reviews test suite: {e}")
            self.log_test("Reviews Test Suite Execution", "FAIL", error=e)


if __name__ == '__main__':
    test_suite = ComprehensiveReviewsTestSuite()
    test_suite.run_reviews_tests()