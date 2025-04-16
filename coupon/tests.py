from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Coupon
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class CouponAPITest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email='admin@test.com', password='admin123', role='admin')
        self.user = User.objects.create_user(email='user@test.com', password='user123', role='user')
        self.client = APIClient()
        self.valid_from = timezone.now()
        self.valid_to = self.valid_from + timedelta(days=10)

    def test_admin_can_create_coupon(self):
        self.client.force_authenticate(user=self.admin)
        data = {
            "code": "SAVE20",
            "discount_percent": "20.00",
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "active": True,
            "assigned_users": [self.user.id]
        }
        response = self.client.post('/api/coupons/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Coupon.objects.count(), 1)

    def test_user_cannot_create_coupon(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "code": "SAVE30",
            "discount_percent": "30.00",
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "active": True
        }
        response = self.client.post('/api/coupons/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_assign_coupon(self):
        self.client.force_authenticate(user=self.admin)
        coupon = Coupon.objects.create(
            code='WELCOME',
            discount_value=15.0,  # Updated field name
            valid_from=self.valid_from,
            valid_to=self.valid_to,
            is_active=True  # Updated field name
        )
        coupon.assigned_users.add(self.user)
        self.assertIn(self.user, coupon.assigned_users.all())
