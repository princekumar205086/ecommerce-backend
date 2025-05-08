from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from decimal import Decimal
from django.conf import settings
from accounts.models import User
from orders.models import Order
from payments.models import Payment
import json
import razorpay


class PaymentTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create users
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass123',
            full_name='Test User'
        )

        # Create test order
        self.order = Order.objects.create(
            user=self.user,
            order_number='TEST123',
            total=Decimal('1000.00'),
            payment_status='pending',
            shipping_address={'street': '123 Test St'},
            billing_address={'street': '123 Test St'}
        )

        # Razorpay test client
        self.razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))

        # Authenticate user
        self.client.force_authenticate(user=self.user)

    def test_create_payment(self):
        """Test creating a payment intent"""
        url = reverse('create-payment')
        data = {
            'order_id': self.order.id,
            'amount': str(self.order.total),
            'currency': 'INR'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('order_id', response.data)
        self.assertIn('amount', response.data)
        self.assertIn('key', response.data)

        # Verify payment record was created
        payment = Payment.objects.get(order=self.order)
        self.assertEqual(payment.amount, self.order.total)
        self.assertEqual(payment.status, 'pending')

    def test_verify_valid_payment(self):
        """Test verifying a valid payment"""
        # Create a test payment record
        payment = Payment.objects.create(
            order=self.order,
            razorpay_order_id='test_razorpay_order_id',
            amount=self.order.total,
            currency='INR'
        )

        # Mock Razorpay verification
        with patch.object(razorpay.Client, 'utility') as mock_utility:
            mock_utility.verify_payment_signature.return_value = True

            url = reverse('verify-payment')
            data = {
                'razorpay_payment_id': 'test_payment_id',
                'razorpay_order_id': payment.razorpay_order_id,
                'razorpay_signature': 'test_signature'
            }

            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Verify payment was updated
            payment.refresh_from_db()
            self.assertEqual(payment.status, 'successful')
            self.assertEqual(payment.razorpay_payment_id, 'test_payment_id')

            # Verify order was updated
            self.order.refresh_from_db()
            self.assertEqual(self.order.payment_status, 'paid')

    def test_verify_invalid_payment(self):
        """Test verifying an invalid payment"""
        payment = Payment.objects.create(
            order=self.order,
            razorpay_order_id='test_razorpay_order_id',
            amount=self.order.total,
            currency='INR'
        )

        # Mock failed verification
        with patch.object(razorpay.Client, 'utility') as mock_utility:
            mock_utility.verify_payment_signature.side_effect = Exception("Invalid signature")

            url = reverse('verify-payment')
            data = {
                'razorpay_payment_id': 'test_payment_id',
                'razorpay_order_id': payment.razorpay_order_id,
                'razorpay_signature': 'invalid_signature'
            }

            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            # Verify payment was marked as failed
            payment.refresh_from_db()
            self.assertEqual(payment.status, 'failed')

    def test_payment_list(self):
        """Test retrieving payment list"""
        # Create test payments
        Payment.objects.create(
            order=self.order,
            razorpay_order_id='order_1',
            razorpay_payment_id='payment_1',
            amount=Decimal('500.00'),
            status='successful'
        )
        Payment.objects.create(
            order=self.order,
            razorpay_order_id='order_2',
            razorpay_payment_id='payment_2',
            amount=Decimal('1000.00'),
            status='failed'
        )

        url = reverse('payment-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['amount'], '500.00')
        self.assertEqual(response.data[1]['amount'], '1000.00')

    def test_payment_detail(self):
        """Test retrieving payment detail"""
        payment = Payment.objects.create(
            order=self.order,
            razorpay_order_id='test_order_id',
            razorpay_payment_id='test_payment_id',
            amount=self.order.total,
            status='successful'
        )

        url = reverse('payment-detail', kwargs={'pk': payment.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['razorpay_payment_id'], 'test_payment_id')
        self.assertEqual(response.data['status'], 'successful')

    def test_create_payment_invalid_order(self):
        """Test creating payment for invalid order"""
        url = reverse('create-payment')
        data = {
            'order_id': 999,  # Non-existent order
            'amount': '1000.00',
            'currency': 'INR'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_payment_unauthorized(self):
        """Test creating payment for order not belonging to user"""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )
        other_order = Order.objects.create(
            user=other_user,
            order_number='OTHER123',
            total=Decimal('500.00')
        )

        url = reverse('create-payment')
        data = {
            'order_id': other_order.id,
            'amount': str(other_order.total),
            'currency': 'INR'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_verify_payment_invalid_order(self):
        """Test verifying payment for invalid order"""
        url = reverse('verify-payment')
        data = {
            'razorpay_payment_id': 'test_payment_id',
            'razorpay_order_id': 'invalid_order_id',
            'razorpay_signature': 'test_signature'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch.object(razorpay.Client, 'order_create')
    def test_create_payment_razorpay_error(self, mock_order_create):
        """Test handling Razorpay API error"""
        mock_order_create.side_effect = Exception("Razorpay API error")

        url = reverse('create-payment')
        data = {
            'order_id': self.order.id,
            'amount': str(self.order.total),
            'currency': 'INR'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)

    def test_payment_model_str(self):
        """Test Payment model string representation"""
        payment = Payment.objects.create(
            order=self.order,
            razorpay_order_id='test_order_id',
            razorpay_payment_id='test_payment_id',
            amount=self.order.total
        )

        self.assertEqual(str(payment), f"Payment test_payment_id for Order TEST123")