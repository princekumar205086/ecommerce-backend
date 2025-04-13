from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError
from .models import (
    Brand, ProductCategory, ProductSubCategory,
    Product, ProductVariant, ProductReview
)

User = get_user_model()


class ProductModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User'
        )
        self.brand = Brand.objects.create(
            name='Test Brand',
            created_by=self.user
        )
        self.category = ProductCategory.objects.create(
            name='Test Category',
            created_by=self.user
        )
        self.subcategory = ProductSubCategory.objects.create(
            name='Test Subcategory',
            category=self.category,
            created_by=self.user
        )
        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=100.00,
            stock=10,
            category=self.category,
            subcategory=self.subcategory,
            brand=self.brand,
            created_by=self.user
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            size='Large',
            weight='500g',
            additional_price=20.00
        )

    def test_brand_creation(self):
        self.assertEqual(self.brand.name, 'Test Brand')
        self.assertEqual(self.brand.created_by, self.user)

    def test_product_creation(self):
        self.assertEqual(self.product.name, 'Test Product')
        self.assertEqual(float(self.product.price), 100.00)
        self.assertEqual(self.product.category, self.category)

    def test_variant_creation(self):
        self.assertEqual(self.variant.product, self.product)
        self.assertEqual(self.variant.size, 'Large')
        self.assertEqual(float(self.variant.total_price), 120.00)

    def test_unique_variant_constraint(self):
        with self.assertRaises(IntegrityError):
            ProductVariant.objects.create(
                product=self.product,
                size='Large',
                weight='500g',
                additional_price=20.00
            )

    def test_product_review_creation(self):
        review = ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            comment='Great product!'
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.user, self.user)
        self.assertTrue(review.is_published)

    def test_low_rating_review_not_published(self):
        review = ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=2,
            comment='Could be better'
        )
        self.assertEqual(review.rating, 2)
        self.assertFalse(review.is_published)


class ProductAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User',
            role='admin'
        )
        self.client.force_authenticate(user=self.user)

        self.brand = Brand.objects.create(name='Test Brand', created_by=self.user)
        self.category = ProductCategory.objects.create(name='Test Category', created_by=self.user)
        self.subcategory = ProductSubCategory.objects.create(
            name='Test Subcategory',
            category=self.category,
            created_by=self.user
        )
        self.product = Product.objects.create(
            name='Test Product',
            price=100.00,
            stock=10,
            category=self.category,
            created_by=self.user
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            size='Large',
            additional_price=20.00
        )
        self.review = ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=4,
            comment='Initial review'
        )

    def test_create_product(self):
        payload = {
            'name': 'New Product',
            'price': 150.00,
            'stock': 5,
            'category': self.category.id,
            'subcategory': self.subcategory.id,
            'brand': self.brand.id,
            'type': 'medical'
        }
        res = self.client.post('/api/products/products/', payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['name'], 'New Product')
        self.assertEqual(float(res.data['price']), 150.00)

    def test_create_product_variant(self):
        payload = {
            'product': self.product.id,
            'size': 'Medium',
            'weight': '300g',
            'additional_price': 10.00
        }
        res = self.client.post('/api/products/variants/', payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['size'], 'Medium')
        self.assertEqual(float(res.data['additional_price']), 10.00)
        self.assertEqual(float(res.data['total_price']), 110.00)

    def test_create_duplicate_variant(self):
        payload = {
            'product': self.product.id,
            'size': 'Large',
            'weight': '500g',
            'additional_price': 20.00
        }

        # First request should succeed
        response1 = self.client.post('/api/products/variants/', payload)
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Second request with same data should fail
        response2 = self.client.post('/api/products/variants/', payload)
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('must make a unique set', str(response2.data))

    def test_get_product_list(self):
        res = self.client.get('/api/products/products/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(res.data['results'][0]['name'], 'Test Product')

    def test_product_list_includes_variants(self):
        res = self.client.get('/api/products/products/')
        product_data = res.data['results'][0]
        self.assertIn('variants', product_data)
        self.assertEqual(len(product_data['variants']), 1)

        variant_data = product_data['variants'][0]
        self.assertIn('total_price', variant_data)
        self.assertEqual(float(variant_data['total_price']), 120.00)

    def test_filter_products_by_category(self):
        res = self.client.get(f'/api/products/products/?category={self.category.id}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(res.data['results'][0]['category'], self.category.id)

    def test_create_product_review(self):
        # Create a new user for this test to avoid duplicate review issues
        new_user = User.objects.create_user(
            email='newuser@example.com',
            password='testpass123',
            full_name='New User'
        )
        self.client.force_authenticate(user=new_user)

        payload = {
            'product': self.product.id,
            'rating': 5,
            'comment': 'Excellent product!'
        }
        res = self.client.post('/api/products/reviews/', payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['rating'], 5)
        self.assertTrue(res.data['is_published'])

    def test_duplicate_review_prevention(self):
        payload = {
            'product': self.product.id,
            'rating': 4,
            'comment': 'Good product'
        }
        res = self.client.post('/api/products/reviews/', payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already reviewed', str(res.data))

    def test_low_rating_review_not_published(self):
        # Create a new user for this test to avoid duplicate review issues
        new_user = User.objects.create_user(
            email='anotheruser@example.com',
            password='testpass123',
            full_name='Another User'
        )
        self.client.force_authenticate(user=new_user)

        payload = {
            'product': self.product.id,
            'rating': 2,
            'comment': 'Could be better'
        }
        res = self.client.post('/api/products/reviews/', payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['rating'], 2)
        self.assertFalse(res.data['is_published'])
