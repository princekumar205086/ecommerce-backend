#!/usr/bin/env python
"""
Products API Endpoints Documentation and Testing Script
Tests existing products and documents all API endpoints with payloads and responses
"""
import os
import sys
import json
import requests
from datetime import datetime
from decimal import Decimal

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal and datetime types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(DecimalEncoder, self).default(obj)

import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from products.models import Product, ProductCategory, Brand, ProductVariant

User = get_user_model()

class ProductsEndpointDocumenter:
    def __init__(self):
        self.client = APIClient()
        self.endpoints_documentation = []
        self.setup_users()
        
    def setup_users(self):
        """Get existing users or create them"""
        try:
            self.admin_user = User.objects.filter(role='admin').first()
            if not self.admin_user:
                self.admin_user = User.objects.create_user(
                    email='admin_test@example.com',
                    password='testpass123',
                    full_name='Test Admin',
                    role='admin',
                    is_staff=True,
                    is_superuser=True
                )
                
            self.supplier_user = User.objects.filter(role='supplier').first()
            if not self.supplier_user:
                self.supplier_user = User.objects.create_user(
                    email='supplier_test@example.com',
                    password='testpass123',
                    full_name='Test Supplier',
                    role='supplier'
                )
                
            self.customer_user = User.objects.filter(role='user').first()
            if not self.customer_user:
                self.customer_user = User.objects.create_user(
                    email='customer_test@example.com',
                    password='testpass123',
                    full_name='Test Customer',
                    role='user'
                )
        except Exception as e:
            print(f"Error setting up users: {e}")
            
    def get_jwt_token(self, user):
        """Get JWT token for user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def authenticate_as(self, user):
        """Authenticate client as specific user"""
        token = self.get_jwt_token(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return token
        
    def document_endpoint(self, title, method, endpoint, description, auth_required, user_role, payload, response_example, status_code, notes=""):
        """Document an API endpoint"""
        doc = {
            "title": title,
            "method": method,
            "endpoint": endpoint,
            "description": description,
            "authentication_required": auth_required,
            "required_user_role": user_role,
            "payload_example": payload,
            "response_example": response_example,
            "status_code": status_code,
            "notes": notes,
            "timestamp": datetime.now().isoformat()
        }
        self.endpoints_documentation.append(doc)
        
    def test_categories_endpoints(self):
        """Test and document category endpoints"""
        print("\n=== TESTING CATEGORY ENDPOINTS ===")
        
        # 1. List categories (public)
        self.client.credentials()
        response = self.client.get('/api/products/categories/')
        self.document_endpoint(
            title="List Categories (Public)",
            method="GET",
            endpoint="/api/products/categories/",
            description="Get all published categories visible to public",
            auth_required=False,
            user_role="Anonymous",
            payload={},
            response_example=response.data if hasattr(response, 'data') else response.content.decode() if hasattr(response.content, 'decode') else str(response.content),
            status_code=response.status_code,
            notes="Returns only published categories for anonymous users"
        )
        print(f"✅ Public categories list: {response.status_code}")
        
        # 2. List categories (admin) - should see all
        self.authenticate_as(self.admin_user)
        response = self.client.get('/api/products/categories/')
        self.document_endpoint(
            title="List Categories (Admin)",
            method="GET",
            endpoint="/api/products/categories/",
            description="Get all categories including pending ones (admin view)",
            auth_required=True,
            user_role="admin",
            payload={},
            response_example=response.data if hasattr(response, 'data') else response.content.decode() if hasattr(response.content, 'decode') else str(response.content),
            status_code=response.status_code,
            notes="Admin can see all categories regardless of status"
        )
        print(f"✅ Admin categories list: {response.status_code}")
        
        # 3. Create category (supplier)
        self.authenticate_as(self.supplier_user)
        category_payload = {
            "name": f"Test Category {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "icon": ""
        }
        response = self.client.post('/api/products/categories/', data=category_payload)
        self.document_endpoint(
            title="Create Category (Supplier)",
            method="POST",
            endpoint="/api/products/categories/",
            description="Create a new category (requires approval for suppliers)",
            auth_required=True,
            user_role="supplier",
            payload=category_payload,
            response_example=response.data if hasattr(response, 'data') else response.content.decode() if hasattr(response.content, 'decode') else str(response.content),
            status_code=response.status_code,
            notes="Supplier-created categories start with status 'pending' and is_publish=False"
        )
        print(f"✅ Supplier category creation: {response.status_code}")
        
        # 4. Get existing category
        categories = ProductCategory.objects.all()[:1]
        if categories:
            category = categories[0]
            response = self.client.get(f'/api/products/categories/{category.id}/')
            self.document_endpoint(
                title="Get Category Details",
                method="GET",
                endpoint=f"/api/products/categories/{category.id}/",
                description="Get detailed information about a specific category",
                auth_required=False,
                user_role="Any",
                payload={},
                response_example=response.data if hasattr(response, 'data') else response.content.decode() if hasattr(response.content, 'decode') else str(response.content),
                status_code=response.status_code
            )
            print(f"✅ Category detail: {response.status_code}")
            
    def test_brands_endpoints(self):
        """Test and document brand endpoints"""
        print("\n=== TESTING BRAND ENDPOINTS ===")
        
        # 1. List brands
        self.client.credentials()
        response = self.client.get('/api/products/brands/')
        self.document_endpoint(
            title="List Brands",
            method="GET",
            endpoint="/api/products/brands/",
            description="Get all brands",
            auth_required=False,
            user_role="Any",
            payload={},
            response_example=response.data if hasattr(response, 'data') else response.content.decode() if hasattr(response.content, 'decode') else str(response.content),
            status_code=response.status_code
        )
        print(f"✅ Brands list: {response.status_code}")
        
        # 2. Create brand (supplier)
        self.authenticate_as(self.supplier_user)
        brand_payload = {
            "name": f"Test Brand {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "image": ""
        }
        response = self.client.post('/api/products/brands/', data=brand_payload)
        self.document_endpoint(
            title="Create Brand (Supplier)",
            method="POST",
            endpoint="/api/products/brands/",
            description="Create a new brand (requires approval for suppliers)",
            auth_required=True,
            user_role="supplier",
            payload=brand_payload,
            response_example=response.data if hasattr(response, 'data') else response.content.decode() if hasattr(response.content, 'decode') else str(response.content),
            status_code=response.status_code,
            notes="Supplier-created brands need admin approval"
        )
        print(f"✅ Supplier brand creation: {response.status_code}")
        
        # 3. Get existing brand
        brands = Brand.objects.all()[:1]
        if brands:
            brand = brands[0]
            response = self.client.get(f'/api/products/brands/{brand.id}/')
            self.document_endpoint(
                title="Get Brand Details",
                method="GET",
                endpoint=f"/api/products/brands/{brand.id}/",
                description="Get detailed information about a specific brand",
                auth_required=False,
                user_role="Any",
                payload={},
                response_example=response.data if hasattr(response, 'data') else response.content.decode() if hasattr(response.content, 'decode') else str(response.content),
                status_code=response.status_code
            )
            print(f"✅ Brand detail: {response.status_code}")
            
    def test_products_endpoints(self):
        """Test and document product endpoints"""
        print("\n=== TESTING PRODUCT ENDPOINTS ===")
        
        # 1. List products
        response = self.client.get('/api/products/products/')
        self.document_endpoint(
            title="List Products (Internal)",
            method="GET",
            endpoint="/api/products/products/",
            description="Get products (internal API for suppliers/admins)",
            auth_required=True,
            user_role="supplier/admin",
            payload={},
            response_example=response.data if hasattr(response, 'data') else response.content.decode() if hasattr(response.content, 'decode') else str(response.content),
            status_code=response.status_code
        )
        print(f"✅ Internal products list: {response.status_code}")
        
        # 2. Create medicine product
        self.authenticate_as(self.supplier_user)
        categories = ProductCategory.objects.all()[:1]
        brands = Brand.objects.all()[:1]
        
        if categories:
            medicine_payload = {
                "name": f"Test Medicine Product {datetime.now().strftime('%Y%m%d%H%M%S')}",
                "description": "A comprehensive test medicine for API documentation",
                "category": categories[0].id,
                "brand": brands[0].id if brands else None,
                "product_type": "medicine",
                "price": "99.99",
                "stock": 50,
                "specifications": json.dumps({
                    "weight": "100mg",
                    "storage": "Room temperature",
                    "shelf_life": "24 months"
                }),
                "medicine_details": json.dumps({
                    "composition": "Active ingredient 100mg, Excipients q.s.",
                    "quantity": "30 tablets",
                    "manufacturer": "Test Pharmaceutical Company",
                    "expiry_date": "2025-12-31",
                    "batch_number": "BATCH001",
                    "prescription_required": True,
                    "form": "Tablet",
                    "pack_size": "30 tablets"
                })
            }
            
            response = self.client.post('/api/products/products/', data=medicine_payload)
            self.document_endpoint(
                title="Create Medicine Product",
                method="POST",
                endpoint="/api/products/products/",
                description="Create a new medicine product with medicine-specific details",
                auth_required=True,
                user_role="supplier",
                payload=medicine_payload,
                response_example=response.data if hasattr(response, 'data') else response.content.decode() if hasattr(response.content, 'decode') else str(response.content),
                status_code=response.status_code,
                notes="Medicine products require medicine_details with composition, expiry_date, etc."
            )
            print(f"✅ Medicine product creation: {response.status_code}")
            
            # 3. Create equipment product
            equipment_payload = {
                "name": f"Test Equipment {datetime.now().strftime('%Y%m%d%H%M%S')}",
                "description": "A comprehensive test medical equipment",
                "category": categories[0].id,
                "brand": brands[0].id if brands else None,
                "product_type": "equipment",
                "price": "999.99",
                "stock": 10,
                "specifications": json.dumps({
                    "dimensions": "10x10x5 cm",
                    "weight": "2kg",
                    "material": "Medical grade plastic"
                }),
                "equipment_details": json.dumps({
                    "model_number": "EQ001",
                    "warranty_period": "2 years",
                    "usage_type": "Diagnostic",
                    "technical_specifications": "Advanced digital display with LCD screen, Bluetooth connectivity",
                    "power_requirement": "220V AC, 50Hz",
                    "equipment_type": "Monitoring Device"
                })
            }
            
            response = self.client.post('/api/products/products/', data=equipment_payload)
            self.document_endpoint(
                title="Create Equipment Product",
                method="POST",
                endpoint="/api/products/products/",
                description="Create a new medical equipment product with equipment-specific details",
                auth_required=True,
                user_role="supplier",
                payload=equipment_payload,
                response_example=response.data if hasattr(response, 'data') else response.content.decode() if hasattr(response.content, 'decode') else str(response.content),
                status_code=response.status_code,
                notes="Equipment products require equipment_details with model_number, warranty_period, etc."
            )
            print(f"✅ Equipment product creation: {response.status_code}")
            
            # 4. Create pathology product
            pathology_payload = {
                "name": f"Test Pathology Kit {datetime.now().strftime('%Y%m%d%H%M%S')}",
                "description": "A comprehensive test pathology testing kit",
                "category": categories[0].id,
                "brand": brands[0].id if brands else None,
                "product_type": "pathology",
                "price": "199.99",
                "stock": 25,
                "specifications": json.dumps({
                    "test_count": "50 tests",
                    "shelf_life": "24 months",
                    "accuracy": "99.5%"
                }),
                "pathology_details": json.dumps({
                    "compatible_tests": "Blood glucose, Cholesterol, Hemoglobin, Protein",
                    "chemical_composition": "Glucose oxidase, Cholesterol esterase, Reagent solutions",
                    "storage_condition": "Store at 2-8°C, protect from light and moisture"
                })
            }
            
            response = self.client.post('/api/products/products/', data=pathology_payload)
            self.document_endpoint(
                title="Create Pathology Product",
                method="POST",
                endpoint="/api/products/products/",
                description="Create a new pathology product with pathology-specific details",
                auth_required=True,
                user_role="supplier",
                payload=pathology_payload,
                response_example=response.data if hasattr(response, 'data') else response.content.decode() if hasattr(response.content, 'decode') else str(response.content),
                status_code=response.status_code,
                notes="Pathology products require pathology_details with compatible_tests, storage_condition, etc."
            )
            print(f"✅ Pathology product creation: {response.status_code}")
            
        # 5. Get existing product detail
        products = Product.objects.all()[:1]
        if products:
            product = products[0]
            response = self.client.get(f'/api/products/products/{product.id}/')
            self.document_endpoint(
                title="Get Product Details",
                method="GET",
                endpoint=f"/api/products/products/{product.id}/",
                description="Get detailed information about a specific product including variants and images",
                auth_required=True,
                user_role="supplier/admin",
                payload={},
                response_example=response.data if hasattr(response, 'data') else response.content.decode() if hasattr(response.content, 'decode') else str(response.content),
                status_code=response.status_code
            )
            print(f"✅ Product detail: {response.status_code}")
            
    def test_public_endpoints(self):
        """Test and document public endpoints"""
        print("\n=== TESTING PUBLIC ENDPOINTS ===")
        
        self.client.credentials()  # Remove authentication
        
        # 1. Public products list
        response = self.client.get('/api/public/products/products/')
        self.document_endpoint(
            title="Public Products List",
            method="GET",
            endpoint="/api/public/products/products/",
            description="Get all published products visible to public users",
            auth_required=False,
            user_role="Anonymous",
            payload={},
            response_example=response.data if hasattr(response, 'data') else response.content.decode() if hasattr(response.content, 'decode') else str(response.content),
            status_code=response.status_code,
            notes="Only returns published products with approved status"
        )
        print(f"✅ Public products list: {response.status_code}")
        
        # 2. Public categories
        response = self.client.get('/api/public/products/categories/')
        self.document_endpoint(
            title="Public Categories List",
            method="GET",
            endpoint="/api/public/products/categories/",
            description="Get all published categories",
            auth_required=False,
            user_role="Anonymous",
            payload={},
            response_example=response.data if hasattr(response, 'data') else response.content.decode() if hasattr(response.content, 'decode') else str(response.content),
            status_code=response.status_code
        )
        print(f"✅ Public categories: {response.status_code}")
        
        # 3. Public brands
        response = self.client.get('/api/public/products/brands/')
        self.document_endpoint(
            title="Public Brands List",
            method="GET",
            endpoint="/api/public/products/brands/",
            description="Get all published brands",
            auth_required=False,
            user_role="Anonymous",
            payload={},
            response_example=response.data if hasattr(response, 'data') else response.content.decode() if hasattr(response.content, 'decode') else str(response.content),
            status_code=response.status_code
        )
        print(f"✅ Public brands: {response.status_code}")
        
        # 4. Product search
        response = self.client.get('/api/public/products/search/?q=medicine')
        self.document_endpoint(
            title="Product Search",
            method="GET",
            endpoint="/api/public/products/search/?q=medicine",
            description="Search products by name, description, or specifications",
            auth_required=False,
            user_role="Anonymous",
            payload={"query_params": {"q": "medicine"}},
            response_example=response.data if hasattr(response, 'data') else response.content.decode() if hasattr(response.content, 'decode') else str(response.content),
            status_code=response.status_code,
            notes="Supports full-text search across product fields"
        )
        print(f"✅ Product search: {response.status_code}")
        
        # 5. Products by type
        for product_type in ['medicine', 'equipment', 'pathology']:
            response = self.client.get(f'/api/public/products/types/{product_type}/products/')
            self.document_endpoint(
                title=f"Products by Type ({product_type.title()})",
                method="GET",
                endpoint=f"/api/public/products/types/{product_type}/products/",
                description=f"Get all {product_type} products",
                auth_required=False,
                user_role="Anonymous",
                payload={},
                response_example=response.data if hasattr(response, 'data') else response.content.decode() if hasattr(response.content, 'decode') else str(response.content),
                status_code=response.status_code,
                notes=f"Filters products by product_type='{product_type}'"
            )
            print(f"✅ {product_type.title()} products: {response.status_code}")
            
        # 6. Featured products
        response = self.client.get('/api/public/products/featured/')
        self.document_endpoint(
            title="Featured Products",
            method="GET",
            endpoint="/api/public/products/featured/",
            description="Get featured/promoted products",
            auth_required=False,
            user_role="Anonymous",
            payload={},
            response_example=response.data if hasattr(response, 'data') else response.content.decode() if hasattr(response.content, 'decode') else str(response.content),
            status_code=response.status_code
        )
        print(f"✅ Featured products: {response.status_code}")
        
        # 7. Product detail (public)
        products = Product.objects.filter(is_publish=True, status__in=['approved', 'published'])[:1]
        if products:
            product = products[0]
            response = self.client.get(f'/api/public/products/products/{product.id}/')
            self.document_endpoint(
                title="Public Product Detail",
                method="GET",
                endpoint=f"/api/public/products/products/{product.id}/",
                description="Get detailed product information for public users",
                auth_required=False,
                user_role="Anonymous",
                payload={},
                response_example=response.data if hasattr(response, 'data') else response.content.decode() if hasattr(response.content, 'decode') else str(response.content),
                status_code=response.status_code,
                notes="Includes product details, variants, images, and type-specific information"
            )
            print(f"✅ Public product detail: {response.status_code}")
            
    def test_variants_endpoints(self):
        """Test and document variant endpoints"""
        print("\n=== TESTING VARIANT ENDPOINTS ===")
        
        self.authenticate_as(self.supplier_user)
        
        # 1. List variants
        response = self.client.get('/api/products/variants/')
        self.document_endpoint(
            title="List Product Variants",
            method="GET",
            endpoint="/api/products/variants/",
            description="Get all product variants",
            auth_required=True,
            user_role="supplier/admin",
            payload={},
            response_example=response.data if hasattr(response, 'data') else response.content.decode() if hasattr(response.content, 'decode') else str(response.content),
            status_code=response.status_code
        )
        print(f"✅ Variants list: {response.status_code}")
        
        # 2. Create variant
        products = Product.objects.all()[:1]
        if products:
            product = products[0]
            variant_payload = {
                "product": product.id,
                "price": "119.99",
                "additional_price": "20.00",
                "stock": 30,
                "is_active": True
            }
            
            response = self.client.post('/api/products/variants/', data=variant_payload)
            self.document_endpoint(
                title="Create Product Variant",
                method="POST",
                endpoint="/api/products/variants/",
                description="Create a new product variant with different pricing/stock",
                auth_required=True,
                user_role="supplier",
                payload=variant_payload,
                response_example=response.data if hasattr(response, 'data') else response.content.decode() if hasattr(response.content, 'decode') else str(response.content),
                status_code=response.status_code,
                notes="Variants allow different pricing, stock levels, and attributes for same product"
            )
            print(f"✅ Variant creation: {response.status_code}")
            
    def test_admin_approval_endpoints(self):
        """Test and document admin approval endpoints"""
        print("\n=== TESTING ADMIN APPROVAL ENDPOINTS ===")
        
        self.authenticate_as(self.admin_user)
        
        # 1. Pending approvals
        response = self.client.get('/api/products/admin/pending-approvals/')
        self.document_endpoint(
            title="Get Pending Approvals",
            method="GET",
            endpoint="/api/products/admin/pending-approvals/",
            description="Get all items pending admin approval (brands, categories, products, variants)",
            auth_required=True,
            user_role="admin",
            payload={},
            response_example=response.data if hasattr(response, 'data') else response.content.decode() if hasattr(response.content, 'decode') else str(response.content),
            status_code=response.status_code,
            notes="Shows all pending items across all product-related models"
        )
        print(f"✅ Pending approvals: {response.status_code}")
        
        # 2. Approve product (if any pending)
        products = Product.objects.filter(status='pending')[:1]
        if products:
            product = products[0]
            response = self.client.post(f'/api/products/admin/products/{product.id}/approve/')
            self.document_endpoint(
                title="Approve Product",
                method="POST",
                endpoint=f"/api/products/admin/products/{product.id}/approve/",
                description="Approve a pending product",
                auth_required=True,
                user_role="admin",
                payload={},
                response_example=response.data if hasattr(response, 'data') else response.content.decode() if hasattr(response.content, 'decode') else str(response.content),
                status_code=response.status_code,
                notes="Sets status to 'approved' and is_publish to True"
            )
            print(f"✅ Product approval: {response.status_code}")
            
        # 3. Bulk approve
        bulk_payload = {
            "items": [
                {"type": "product", "id": 1, "action": "approve"},
                {"type": "brand", "id": 1, "action": "approve"}
            ]
        }
        
        response = self.client.post('/api/products/admin/bulk-approve/', data=bulk_payload, format='json')
        self.document_endpoint(
            title="Bulk Approve Items",
            method="POST",
            endpoint="/api/products/admin/bulk-approve/",
            description="Approve multiple items in a single request",
            auth_required=True,
            user_role="admin",
            payload=bulk_payload,
            response_example=response.data if hasattr(response, 'data') else response.content.decode() if hasattr(response.content, 'decode') else str(response.content),
            status_code=response.status_code,
            notes="Supports bulk operations on products, brands, categories, and variants"
        )
        print(f"✅ Bulk approval: {response.status_code}")
        
    def run_all_tests(self):
        """Run all endpoint tests and generate documentation"""
        print("🚀 Starting Products API Documentation Generation")
        print("=" * 60)
        
        try:
            self.test_categories_endpoints()
            self.test_brands_endpoints() 
            self.test_products_endpoints()
            self.test_public_endpoints()
            self.test_variants_endpoints()
            self.test_admin_approval_endpoints()
            
            print(f"\n✅ Documentation generation completed!")
            print(f"📊 Total endpoints documented: {len(self.endpoints_documentation)}")
            
        except Exception as e:
            print(f"❌ Documentation generation failed: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def generate_markdown_documentation(self):
        """Generate comprehensive markdown documentation"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        doc_file = f'COMPLETE_PRODUCTS_API_DOCUMENTATION_{timestamp}.md'
        
        markdown_content = self.generate_markdown_content()
        
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
            
        print(f"\n📚 Complete API documentation saved to: {doc_file}")
        return doc_file
        
    def generate_markdown_content(self):
        """Generate markdown content for the documentation"""
        content = f"""# Complete Products API Documentation

**Generated on:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Overview

This document provides comprehensive documentation for the Products API, covering all endpoints for managing products, categories, brands, variants, and related functionality in the eCommerce platform.

## Authentication

Most endpoints require JWT token authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## User Roles

- **Anonymous**: No authentication required
- **Customer/User**: Basic authenticated user  
- **Supplier**: Can create products, categories, brands (subject to approval)
- **Admin**: Full access, can approve/reject items, manage all data

## Base URLs

- **Internal API**: `/api/products/`
- **Public API**: `/api/public/`

## Product Types

The system supports three main product types:
1. **Medicine**: Pharmaceutical products with medicine-specific details
2. **Equipment**: Medical equipment with technical specifications  
3. **Pathology**: Laboratory testing products with test details

---

## API Endpoints

"""

        # Group endpoints by category
        categories = {
            'Categories': [],
            'Brands': [],
            'Products': [],
            'Public': [],
            'Variants': [],
            'Admin': []
        }
        
        for endpoint in self.endpoints_documentation:
            title = endpoint['title']
            if 'Category' in title or 'Categories' in title:
                categories['Categories'].append(endpoint)
            elif 'Brand' in title or 'Brands' in title:
                categories['Brands'].append(endpoint)
            elif 'Public' in title:
                categories['Public'].append(endpoint)
            elif 'Variant' in title:
                categories['Variants'].append(endpoint)
            elif 'Admin' in title or 'Approval' in title or 'Approve' in title:
                categories['Admin'].append(endpoint)
            else:
                categories['Products'].append(endpoint)
                
        for category_name, endpoints in categories.items():
            if not endpoints:
                continue
                
            content += f"## {category_name} Endpoints\n\n"
            
            for endpoint in endpoints:
                content += f"### {endpoint['title']}\n\n"
                content += f"**Method:** `{endpoint['method']}`  \n"
                content += f"**Endpoint:** `{endpoint['endpoint']}`  \n"
                content += f"**Authentication:** {'Required' if endpoint['authentication_required'] else 'Not Required'}  \n"
                content += f"**User Role:** {endpoint['required_user_role']}  \n"
                content += f"**Status Code:** {endpoint['status_code']}  \n\n"
                
                content += f"**Description:**  \n{endpoint['description']}\n\n"
                
                if endpoint['payload_example'] and endpoint['payload_example'] != {}:
                    content += "**Request Payload:**\n```json\n"
                    content += json.dumps(endpoint['payload_example'], indent=2, cls=DecimalEncoder)
                    content += "\n```\n\n"
                
                content += "**Response Example:**\n```json\n"
                if isinstance(endpoint['response_example'], (dict, list)):
                    content += json.dumps(endpoint['response_example'], indent=2, cls=DecimalEncoder)
                else:
                    content += str(endpoint['response_example'])
                content += "\n```\n\n"
                
                if endpoint['notes']:
                    content += f"**Notes:** {endpoint['notes']}\n\n"
                
                content += "---\n\n"
        
        # Add payload examples for different product types
        content += """## Product Creation Examples

### Medicine Product Payload
```json
{
  "name": "Sample Medicine Product",
  "description": "A comprehensive pharmaceutical product",
  "category": 1,
  "brand": 1,
  "product_type": "medicine",
  "price": "99.99",
  "stock": 50,
  "specifications": {
    "weight": "100mg",
    "storage": "Room temperature",
    "shelf_life": "24 months"
  },
  "medicine_details": {
    "composition": "Active ingredient 100mg, Excipients q.s.",
    "quantity": "30 tablets",
    "manufacturer": "Pharmaceutical Company",
    "expiry_date": "2025-12-31",
    "batch_number": "BATCH001",
    "prescription_required": true,
    "form": "Tablet",
    "pack_size": "30 tablets"
  }
}
```

### Equipment Product Payload
```json
{
  "name": "Sample Medical Equipment",
  "description": "Advanced medical monitoring device",
  "category": 1,
  "brand": 1,
  "product_type": "equipment",
  "price": "999.99",
  "stock": 10,
  "specifications": {
    "dimensions": "10x10x5 cm",
    "weight": "2kg",
    "material": "Medical grade plastic"
  },
  "equipment_details": {
    "model_number": "EQ001",
    "warranty_period": "2 years",
    "usage_type": "Diagnostic",
    "technical_specifications": "Advanced digital display with LCD screen",
    "power_requirement": "220V AC, 50Hz",
    "equipment_type": "Monitoring Device"
  }
}
```

### Pathology Product Payload
```json
{
  "name": "Sample Pathology Kit",
  "description": "Comprehensive testing kit for laboratory use",
  "category": 1,
  "brand": 1,
  "product_type": "pathology",
  "price": "199.99",
  "stock": 25,
  "specifications": {
    "test_count": "50 tests",
    "shelf_life": "24 months",
    "accuracy": "99.5%"
  },
  "pathology_details": {
    "compatible_tests": "Blood glucose, Cholesterol, Hemoglobin",
    "chemical_composition": "Test reagents and control solutions",
    "storage_condition": "Store at 2-8°C, protect from light"
  }
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "field_name": ["Error message describing the issue"]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

## Status Codes

- **200**: Success (GET requests)
- **201**: Created (POST requests)
- **204**: No Content (DELETE requests)
- **400**: Bad Request (validation errors)
- **401**: Unauthorized (authentication required)
- **403**: Forbidden (insufficient permissions)
- **404**: Not Found (resource doesn't exist)

## Approval Workflow

For suppliers, the following items require admin approval:
- **Categories**: Status starts as 'pending', is_publish=False
- **Brands**: Status starts as 'pending', is_publish=False  
- **Products**: Status starts as 'pending', is_publish=False
- **Variants**: Status starts as 'pending', is_active=False

Admins can approve/reject these items through the admin endpoints.

## Image Upload

Several endpoints support image upload via multipart/form-data:
- Brand creation/update (image_file)
- Category creation/update (icon_file)
- Product creation/update (image_file)
- Product images (image_file)

Images are uploaded to ImageKit and URLs are stored in the database.

---

**Documentation Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

        return content

if __name__ == '__main__':
    documenter = ProductsEndpointDocumenter()
    documenter.run_all_tests()
    documenter.generate_markdown_documentation()