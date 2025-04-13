from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from products.models import Product, ProductVariant, ProductCategory, Brand
from .models import Wishlist, WishlistItem

User = get_user_model()


class WishlistModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User'
        )

        # Create required related objects
        self.brand = Brand.objects.create(
            name='Test Brand',
            created_by=self.user
        )
        self.category = ProductCategory.objects.create(
            name='Test Category',
            created_by=self.user
        )

        self.product = Product.objects.create(
            name='Test Product',
            price=100.00,
            category=self.category,
            created_by=self.user
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            size='Large',
            additional_price=20.00
        )

    def test_create_wishlist(self):
        wishlist = Wishlist.objects.create(
            user=self.user,
            name='My Wishlist'
        )
        self.assertEqual(wishlist.user, self.user)
        self.assertEqual(wishlist.name, 'My Wishlist')

    def test_unique_default_wishlist(self):
        Wishlist.objects.create(
            user=self.user,
            name='Default',
            is_default=True
        )
        with self.assertRaises(Exception):
            Wishlist.objects.create(
                user=self.user,
                name='Another Default',
                is_default=True
            )

    def test_add_wishlist_item(self):
        wishlist = Wishlist.objects.create(user=self.user)
        item = WishlistItem.objects.create(
            wishlist=wishlist,
            product=self.product
        )
        self.assertEqual(item.wishlist, wishlist)
        self.assertEqual(item.product, self.product)

    def test_unique_product_variant_in_wishlist(self):
        wishlist = Wishlist.objects.create(user=self.user)
        WishlistItem.objects.create(
            wishlist=wishlist,
            product=self.product,
            variant=self.variant
        )
        with self.assertRaises(Exception):
            WishlistItem.objects.create(
                wishlist=wishlist,
                product=self.product,
                variant=self.variant
            )


class WishlistAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User'
        )
        self.client.force_authenticate(user=self.user)

        # Create required related objects
        self.brand = Brand.objects.create(
            name='Test Brand',
            created_by=self.user
        )
        self.category = ProductCategory.objects.create(
            name='Test Category',
            created_by=self.user
        )

        self.product = Product.objects.create(
            name='Test Product',
            price=100.00,
            category=self.category,
            created_by=self.user
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            size='Large',
            additional_price=20.00
        )

    def test_create_wishlist(self):
        payload = {'name': 'New Wishlist'}
        response = self.client.post('/api/wishlist/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Wishlist')

    def test_get_default_wishlist(self):
        response = self.client.get('/api/wishlist/default/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'My Wishlist')
        self.assertTrue(response.data['is_default'])

    def test_add_item_to_wishlist(self):
        wishlist = Wishlist.objects.create(user=self.user)
        payload = {
            'product_id': self.product.id,
            'variant_id': self.variant.id
        }
        response = self.client.post(
            f'/api/wishlist/{wishlist.id}/items/',
            payload
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['product']['name'], 'Test Product')

    def test_remove_item_from_wishlist(self):
        wishlist = Wishlist.objects.create(user=self.user)
        item = WishlistItem.objects.create(
            wishlist=wishlist,
            product=self.product
        )
        response = self.client.delete(
            f'/api/wishlist/items/{item.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(WishlistItem.objects.filter(id=item.id).exists())

    def test_cannot_add_duplicate_items(self):
        wishlist = Wishlist.objects.create(user=self.user)
        payload = {'product_id': self.product.id}

        # First request should succeed
        response1 = self.client.post(
            f'/api/wishlist/{wishlist.id}/items/',
            payload
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Second request should fail
        response2 = self.client.post(
            f'/api/wishlist/{wishlist.id}/items/',
            payload
        )
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already exists', str(response2.data).lower())

    def test_update_wishlist(self):
        wishlist = Wishlist.objects.create(user=self.user, name='Old Name')
        payload = {'name': 'New Name'}
        response = self.client.patch(
            f'/api/wishlist/{wishlist.id}/',
            payload
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'New Name')

    def test_delete_wishlist(self):
        wishlist = Wishlist.objects.create(user=self.user)
        response = self.client.delete(
            f'/api/wishlist/{wishlist.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Wishlist.objects.filter(id=wishlist.id).exists())


def test_cannot_add_duplicate_variant_items(self):
    wishlist = Wishlist.objects.create(user=self.user)
    payload = {
        'product_id': self.product.id,
        'variant_id': self.variant.id
    }

    # First request should succeed
    response1 = self.client.post(
        f'/api/wishlist/{wishlist.id}/items/',
        payload
    )
    self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

    # Second request should fail
    response2 = self.client.post(
        f'/api/wishlist/{wishlist.id}/items/',
        payload
    )
    self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
    self.assertIn('already exists', str(response2.data).lower())
