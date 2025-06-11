from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Brand, ProductCategory, Product, ProductVariant, ProductReview

User = get_user_model()


class BaseSetupMixin:
    """Reusable setup for model and API tests"""
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            full_name='Admin User',
            role='admin'
        )
        cls.brand = Brand.objects.create(name='Test Brand', created_by=cls.user)
        cls.category = ProductCategory.objects.create(name='Test Category', created_by=cls.user)
        cls.product = Product.objects.create(
            name='Test Product',
            description='Initial Description',
            price=100.00,
            stock=10,
            category=cls.category,
            brand=cls.brand,
            created_by=cls.user
        )
        cls.variant = ProductVariant.objects.create(
            product=cls.product,
            size='Large',
            weight='500g',
            additional_price=20.00
        )


class ProductModelTests(BaseSetupMixin, TestCase):

    def test_brand_creation(self):
        self.assertEqual(self.brand.name, 'Test Brand')

    def test_product_creation(self):
        self.assertEqual(self.product.name, 'Test Product')
        self.assertEqual(float(self.product.price), 100.00)

    def test_variant_total_price(self):
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

    def test_product_review_auto_publish(self):
        review = ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            comment='Excellent!'
        )
        self.assertTrue(review.is_published)

    def test_low_rating_review_flagged(self):
        review = ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=2,
            comment='Poor'
        )
        self.assertFalse(review.is_published)


class ProductAPITests(BaseSetupMixin, TestCase):

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_product(self):
        payload = {
            'name': 'New Product',
            'description': 'A new product',
            'price': 150.00,
            'stock': 5,
            'category': self.category.id,
            'brand': self.brand.id
        }
        response = self.client.post('/api/products/products/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], payload['name'])

    def test_create_product_variant(self):
        payload = {
            'product': self.product.id,
            'size': 'Medium',
            'weight': '300g',
            'additional_price': 10.00
        }
        response = self.client.post('/api/products/variants/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.data['total_price']), 110.00)

    def test_duplicate_variant_blocked(self):
        payload = {
            'product': self.product.id,
            'size': 'XL',
            'weight': '600g',
            'additional_price': 30.00
        }
        self.client.post('/api/products/variants/', payload)
        duplicate = self.client.post('/api/products/variants/', payload)
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already exists', str(duplicate.data).lower())

    def test_get_products_with_variants(self):
        response = self.client.get('/api/products/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)
        product = response.data['results'][0]
        self.assertIn('variants', product)
        self.assertEqual(len(product['variants']), 1)
        self.assertEqual(float(product['variants'][0]['total_price']), 120.00)

    def test_filter_by_category(self):
        response = self.client.get(f'/api/products/products/?category={self.category.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['category'], self.category.id)

    def test_review_creation_and_block_duplicate(self):
        # First review
        response1 = self.client.post('/api/products/reviews/', {
            'product': self.product.id,
            'rating': 5,
            'comment': 'Awesome!'
        })
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response1.data['is_published'])

        # Duplicate review
        response2 = self.client.post('/api/products/reviews/', {
            'product': self.product.id,
            'rating': 4,
            'comment': 'Second review attempt'
        })
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already reviewed', str(response2.data).lower())

    def test_review_auto_flag_for_low_rating(self):
        user2 = User.objects.create_user(email='new@example.com', password='test123', full_name='New User')
        self.client.force_authenticate(user=user2)
        response = self.client.post('/api/products/reviews/', {
            'product': self.product.id,
            'rating': 2,
            'comment': 'Not good enough'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['is_published'])

    def test_create_supplier_price(self):
        payload = {
            'product': self.product.id,
            'price': 95.00
        }
        response = self.client.post('/api/products/supplier-prices/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.data['price']), 95.00)
