from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from accounts.models import User
from coupon.models import Coupon
from orders.models import Order, OrderItem, OrderStatusChange
from products.models import Product, ProductCategory, Brand, ProductVariant


class OrderAppTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create users
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='admin123',
            full_name='Admin User',
            role='admin'
        )
        self.customer = User.objects.create_user(
            email='customer@example.com',
            password='customer123',
            full_name='Customer User'
        )

        # Create product category and brand
        self.category = ProductCategory.objects.create(name='Test Category', created_by=self.admin)
        self.brand = Brand.objects.create(name='Test Brand', created_by=self.admin)

        # Create products
        self.product1 = Product.objects.create(
            name='Test Product 1', price=Decimal('100.00'), stock=10,
            category=self.category, brand=self.brand, created_by=self.admin
        )
        self.product2 = Product.objects.create(
            name='Test Product 2', price=Decimal('200.00'), stock=5,
            category=self.category, brand=self.brand, created_by=self.admin
        )

        # Create variant
        self.variant = ProductVariant.objects.create(
            product=self.product1, size='Large',
            additional_price=Decimal('20.00'), stock=5
        )

        # Create coupon
        self.coupon = Coupon.objects.create(
            code='TEST20', coupon_type='percentage', discount_value=20,
            max_discount=Decimal('50.00'), min_order_amount=Decimal('100.00'),
            valid_from=timezone.now(), valid_to=timezone.now() + timezone.timedelta(days=30),
            max_uses=100, created_by=self.admin
        )

        # Sample addresses
        self.shipping_address = {
            'street': '123 Test St', 'city': 'Testville',
            'state': 'TS', 'zip_code': '12345', 'country': 'Testland'
        }
        self.billing_address = self.shipping_address.copy()

        self.client.force_authenticate(user=self.customer)

    def tearDown(self):
        OrderStatusChange.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()

        User.objects.exclude(email__in=['admin@example.com', 'customer@example.com']).delete()

        from cart.models import Cart, CartItem
        CartItem.objects.all().delete()
        Cart.objects.all().delete()

    def create_test_order(self):
        order = Order.objects.create(
            user=self.customer,
            shipping_address=self.shipping_address,
            billing_address=self.billing_address,
            payment_method='credit_card'
        )
        OrderItem.objects.create(order=order, product=self.product1, quantity=2, price=self.product1.price)
        OrderItem.objects.create(order=order, product=self.product2, quantity=1, price=self.product2.price)
        order.calculate_totals()
        order.save()
        return order


class ModelTests(OrderAppTestCase):
    def test_order_creation(self):
        order = self.create_test_order()
        self.assertEqual(str(order), f"Order #{order.order_number}")
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.payment_status, 'pending')
        self.assertEqual(order.subtotal, Decimal('400.00'))
        self.assertEqual(order.tax, Decimal('40.00'))
        self.assertEqual(order.total, Decimal('440.00'))

    def test_order_item_creation(self):
        order = self.create_test_order()
        items = order.items.all()
        self.assertEqual(items.count(), 2)
        self.assertEqual(items[0].product, self.product1)
        self.assertEqual(items[0].quantity, 2)
        self.assertEqual(items[0].total_price, Decimal('200.00'))

    def test_order_status_change(self):
        order = self.create_test_order()
        OrderStatusChange.objects.create(order=order, status='processing', changed_by=self.admin)
        order.status = 'processing'
        order.save()
        status_changes = order.status_changes.all()
        self.assertEqual(status_changes.count(), 1)
        self.assertEqual(status_changes[0].status, 'processing')

    def test_order_from_cart(self):
        from cart.models import Cart, CartItem
        cart = Cart.objects.create(user=self.customer)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=2)
        CartItem.objects.create(cart=cart, product=self.product2, quantity=1)
        order = Order.create_from_cart(
            cart=cart,
            shipping_address=self.shipping_address,
            billing_address=self.billing_address,
            payment_method='credit_card'
        )
        self.assertEqual(order.user, self.customer)
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.subtotal, Decimal('400.00'))
        self.product1.refresh_from_db()
        self.product2.refresh_from_db()
        self.assertEqual(self.product1.stock, 8)
        self.assertEqual(self.product2.stock, 4)
        self.assertEqual(cart.items.count(), 0)

    def test_insufficient_stock(self):
        from cart.models import Cart, CartItem
        cart = Cart.objects.create(user=self.customer)
        item = CartItem.objects.create(cart=cart, product=self.product1, quantity=5)
        CartItem.objects.filter(pk=item.pk).update(quantity=15)  # Update quantity for the test
        with self.assertRaises(ValidationError) as context:
            Order.create_from_cart(
                cart=cart,
                shipping_address=self.shipping_address,
                billing_address=self.billing_address
            )
        self.assertIn('Not enough stock for Test Product 1', str(context.exception))


class APITests(OrderAppTestCase):
    def setUp(self):
        super().setUp()
        Order.objects.all().delete()
        OrderItem.objects.all().delete()

    def test_create_order_from_cart(self):
        from cart.models import Cart, CartItem
        cart = Cart.objects.create(user=self.customer)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=2)
        url = reverse('cart-checkout')
        data = {
            'cart_id': cart.id,
            'shipping_address': self.shipping_address,
            'billing_address': self.billing_address,
            'payment_method': 'credit_card'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'pending')
        self.assertEqual(response.data['payment_status'], 'pending')
        self.assertEqual(Decimal(response.data['subtotal']), Decimal('200.00'))
        order = Order.objects.get(order_number=response.data['order_number'])
        self.assertEqual(order.items.count(), 1)

    def test_apply_coupon(self):
        order = self.create_test_order()
        url = reverse('apply-coupon', kwargs={'order_id': order.id})
        data = {'coupon_code': 'TEST20'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.coupon, self.coupon)
        self.assertEqual(Decimal(response.data['coupon_discount']), Decimal('50.00'))

    def test_invalid_coupon(self):
        order = self.create_test_order()
        url = reverse('apply-coupon', kwargs={'order_id': order.id})
        data = {'coupon_code': 'INVALID'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_order_list(self):
        Order.objects.all().delete()
        self.create_test_order()
        url = reverse('order-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_order_detail(self):
        order = self.create_test_order()
        url = reverse('order-detail', kwargs={'pk': order.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_number'], order.order_number)
        self.assertEqual(len(response.data['items']), 2)

    def test_order_status_update(self):
        order = self.create_test_order()
        url = reverse('order-detail', kwargs={'pk': order.pk})
        data = {'status': 'processing', 'notes': 'Processing started'}
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, 'processing')
        self.assertEqual(order.status_changes.count(), 1)
        self.assertEqual(order.status_changes.first().status, 'processing')

    def test_order_stats(self):
        self.create_test_order()
        self.client.force_authenticate(user=self.admin)
        url = reverse('order-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_orders'], 1)
        self.assertEqual(response.data['total_revenue'], '440.00')


class PermissionTests(OrderAppTestCase):
    def setUp(self):
        super().setUp()
        Order.objects.all().delete()

    def test_customer_access(self):
        order = self.create_test_order()
        other_user = User.objects.create_user(email='other@example.com', password='testpass')
        self.client.force_authenticate(user=other_user)
        response = self.client.get(reverse('order-detail', kwargs={'pk': order.pk}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
