from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.core.exceptions import ValidationError
from products.models import Product, ProductVariant, ProductCategory
from .models import Cart, CartItem

User = get_user_model()


class CartModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User'
        )

        # Create required category
        self.category = ProductCategory.objects.create(
            name='Test Category',
            created_by=self.user
        )

        self.product = Product.objects.create(
            name='Test Product',
            price=100.00,
            stock=10,
            created_by=self.user,
            category=self.category
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            size='Large',
            additional_price=20.00,
            stock=5
        )
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            variant=self.variant,
            quantity=2
        )

    def test_cart_creation(self):
        self.assertEqual(self.cart.user, self.user)
        self.assertEqual(self.cart.total_price, 240.00)  # (100 + 20) * 2
        self.assertEqual(str(self.cart), f"Cart {self.cart.id} - {self.user.email}")

    def test_cart_item_creation(self):
        self.assertEqual(self.cart_item.quantity, 2)
        self.assertEqual(self.cart_item.total_price, 240.00)
        self.assertEqual(str(self.cart_item), "2 x Test Product (Large)")

    def test_unique_cart_item_constraint(self):
        with self.assertRaises(Exception):
            CartItem.objects.create(
                cart=self.cart,
                product=self.product,
                variant=self.variant,
                quantity=1
            )

    def test_cart_item_without_variant_string_representation(self):
        item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=1
        )
        self.assertEqual(str(item), "1 x Test Product")

    def test_cart_clear_method(self):
        self.cart.clear()
        self.assertEqual(self.cart.items.count(), 0)

    def test_cart_item_validation(self):
        # Test valid variant (belonging to product)
        valid_item = CartItem(
            cart=Cart.objects.create(user=self.user),  # New cart to avoid unique constraint
            product=self.product,
            variant=self.variant,
            quantity=1
        )
        try:
            valid_item.full_clean()
        except ValidationError:
            self.fail("Valid cart item raised ValidationError unexpectedly")

        # Test with invalid variant
        other_product = Product.objects.create(
            name='Other Product',
            price=50.00,
            stock=5,
            created_by=self.user,
            category=self.category
        )
        other_variant = ProductVariant.objects.create(
            product=other_product,
            size='Small',
            additional_price=10.00
        )

        invalid_item = CartItem(
            cart=self.cart,
            product=self.product,
            variant=other_variant,  # Variant doesn't belong to product
            quantity=1
        )
        with self.assertRaises(ValidationError):
            invalid_item.full_clean()

    def test_cart_item_stock_validation(self):
        # Test quantity exceeds product stock
        item = CartItem(
            cart=Cart.objects.create(user=self.user),  # New cart
            product=self.product,
            quantity=15  # Product stock is 10
        )
        with self.assertRaises(ValidationError):
            item.full_clean()

        # Test quantity exceeds variant stock
        item = CartItem(
            cart=Cart.objects.create(user=self.user),  # New cart
            product=self.product,
            variant=self.variant,
            quantity=6  # Variant stock is 5
        )
        with self.assertRaises(ValidationError):
            item.full_clean()


class CartAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User'
        )
        self.client.force_authenticate(user=self.user)

        # Create required category
        self.category = ProductCategory.objects.create(
            name='Test Category',
            created_by=self.user
        )

        self.product = Product.objects.create(
            name='Test Product',
            price=100.00,
            stock=10,
            created_by=self.user,
            category=self.category
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            size='Large',
            additional_price=20.00,
            stock=5
        )
        self.other_product = Product.objects.create(
            name='Other Product',
            price=50.00,
            stock=5,
            created_by=self.user,
            category=self.category
        )

    def test_get_empty_cart(self):
        res = self.client.get('/api/cart/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['items']), 0)
        self.assertEqual(res.data['total_items'], 0)
        self.assertEqual(float(res.data['total_price']), 0.00)

    def test_add_to_cart_with_variant(self):
        payload = {
            'product_id': self.product.id,
            'variant_id': self.variant.id,
            'quantity': 2
        }
        res = self.client.post('/api/cart/add/', payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.total_price, 240.00)  # (100 + 20) * 2

        # Verify response data
        res = self.client.get('/api/cart/')
        self.assertEqual(len(res.data['items']), 1)
        self.assertEqual(res.data['items'][0]['quantity'], 2)
        self.assertEqual(float(res.data['items'][0]['total_price']), 240.00)

    def test_add_to_cart_without_variant(self):
        payload = {
            'product_id': self.product.id,
            'quantity': 3
        }
        res = self.client.post('/api/cart/add/', payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.total_price, 300.00)  # 100 * 3

    def test_add_duplicate_item_to_cart(self):
        # First addition
        payload = {
            'product_id': self.product.id,
            'variant_id': self.variant.id,
            'quantity': 1
        }
        res = self.client.post('/api/cart/add/', payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Second addition - should update quantity
        res = self.client.post('/api/cart/add/', payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.first().quantity, 2)

    def test_update_cart_item_quantity(self):
        # First add item
        payload = {
            'product_id': self.product.id,
            'variant_id': self.variant.id,
            'quantity': 1
        }
        self.client.post('/api/cart/add/', payload)
        item_id = CartItem.objects.first().id

        # Update quantity
        update_payload = {'quantity': 5}
        res = self.client.put(f'/api/cart/items/{item_id}/', update_payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.first().quantity, 5)
        self.assertEqual(cart.total_price, 600.00)  # (100 + 20) * 5

    def test_update_cart_item_invalid_quantity(self):
        # First add item
        payload = {
            'product_id': self.product.id,
            'variant_id': self.variant.id,
            'quantity': 1
        }
        self.client.post('/api/cart/add/', payload)
        item_id = CartItem.objects.first().id

        # Try to update with invalid quantity
        update_payload = {'quantity': 0}
        res = self.client.put(f'/api/cart/items/{item_id}/', update_payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        update_payload = {'quantity': -1}
        res = self.client.put(f'/api/cart/items/{item_id}/', update_payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_item_from_cart(self):
        # First add item
        payload = {
            'product_id': self.product.id,
            'quantity': 1
        }
        self.client.post('/api/cart/add/', payload)
        item_id = CartItem.objects.first().id

        # Remove item
        res = self.client.delete(f'/api/cart/items/{item_id}/remove/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.count(), 0)

    def test_remove_nonexistent_item(self):
        res = self.client.delete('/api/cart/remove/999/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_clear_cart(self):
        # Add multiple items
        self.client.post('/api/cart/add/', {
            'product_id': self.product.id,
            'variant_id': self.variant.id,
            'quantity': 1
        })
        self.client.post('/api/cart/add/', {
            'product_id': self.other_product.id,
            'quantity': 2
        })

        # Clear cart
        res = self.client.delete('/api/cart/clear/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.count(), 0)

    def test_clear_empty_cart(self):
        res = self.client.delete('/api/cart/clear/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_unauthorized_access(self):
        self.client.logout()

        # Create an item first
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1
        )

        endpoints = [
            ('get', '/api/cart/'),
            ('post', '/api/cart/add/', {'product_id': self.product.id, 'quantity': 1}),
            ('put', f'/api/cart/items/{item.id}/update/', {'quantity': 2}),
            ('delete', f'/api/cart/items/{item.id}/remove/'),
            ('delete', '/api/cart/clear/')
        ]

        for method, url, *data in endpoints:
            if method == 'get':
                res = self.client.get(url)
            elif method == 'post':
                res = self.client.post(url, data[0] if data else {})
            elif method == 'put':
                res = self.client.put(url, data[0] if data else {})
            elif method == 'delete':
                res = self.client.delete(url)

            self.assertEqual(
                res.status_code,
                status.HTTP_401_UNAUTHORIZED,
                f"Failed on {method.upper()} {url}"
            )

    def test_add_to_cart_invalid_product(self):
        payload = {
            'product_id': 9999,  # Invalid product ID
            'quantity': 1
        }
        res = self.client.post('/api/cart/add/', payload)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_to_cart_invalid_variant(self):
        payload = {
            'product_id': self.product.id,
            'variant_id': 9999,  # Invalid variant ID
            'quantity': 1
        }
        res = self.client.post('/api/cart/add/', payload)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_to_cart_variant_mismatch(self):
        # Create variant for other product
        other_variant = ProductVariant.objects.create(
            product=self.other_product,
            size='Small',
            additional_price=10.00
        )

        payload = {
            'product_id': self.product.id,
            'variant_id': other_variant.id,  # Variant doesn't belong to product
            'quantity': 1
        }
        res = self.client.post('/api/cart/add/', payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_to_cart_insufficient_stock(self):
        # Test product stock
        payload = {
            'product_id': self.product.id,
            'quantity': 15  # Product stock is 10
        }
        res = self.client.post('/api/cart/add/', payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Only 10 items available in stock', str(res.data['error']))

        # Test variant stock
        payload = {
            'product_id': self.product.id,
            'variant_id': self.variant.id,
            'quantity': 6  # Variant stock is 5
        }
        res = self.client.post('/api/cart/add/', payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Only 5 items available in stock', str(res.data['error']))

    def test_update_nonexistent_item(self):
        update_payload = {'quantity': 5}
        res = self.client.put('/api/cart/update/999/', update_payload)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_cart_item_serialization(self):
        # Add item to cart
        payload = {
            'product_id': self.product.id,
            'variant_id': self.variant.id,
            'quantity': 2
        }
        self.client.post('/api/cart/add/', payload)

        # Get cart and verify serialized data
        res = self.client.get('/api/cart/')
        item_data = res.data['items'][0]

        self.assertEqual(item_data['quantity'], 2)
        self.assertEqual(float(item_data['total_price']), 240.00)
        self.assertEqual(item_data['product']['name'], 'Test Product')
        self.assertEqual(item_data['variant']['size'], 'Large')
        self.assertEqual(float(item_data['variant']['additional_price']), 20.00)
