from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Review
from products.models import Product  # adjust if needed

User = get_user_model()

class ReviewAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.product = Product.objects.create(name='Test Product', price=10)
        self.content_type = ContentType.objects.get_for_model(self.product)

    def test_create_review_authenticated(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.post('/api/reviews/', {
            'content_type': self.content_type.model,
            'object_id': self.product.id,
            'rating': 4,
            'comment': 'Great product!'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_review_unauthenticated(self):
        response = self.client.post('/api/reviews/', {
            'content_type': self.content_type.model,
            'object_id': self.product.id,
            'rating': 4,
            'comment': 'Great product!'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_reviews(self):
        Review.objects.create(user=self.user, content_type=self.content_type, object_id=self.product.id, rating=5)
        response = self.client.get('/api/reviews/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_review(self):
        review = Review.objects.create(user=self.user, content_type=self.content_type, object_id=self.product.id, rating=5)
        self.client.login(username='testuser', password='testpass')
        response = self.client.patch(f'/api/reviews/{review.id}/', {'rating': 3})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_review(self):
        review = Review.objects.create(user=self.user, content_type=self.content_type, object_id=self.product.id, rating=5)
        self.client.login(username='testuser', password='testpass')
        response = self.client.delete(f'/api/reviews/{review.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_cannot_update_other_users_review(self):
        other_user = User.objects.create_user(username='otheruser', password='otherpass')
        review = Review.objects.create(user=other_user, content_type=self.content_type, object_id=self.product.id, rating=4)
        self.client.login(username='testuser', password='testpass')
        response = self.client.patch(f'/api/reviews/{review.id}/', {'rating': 1})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
