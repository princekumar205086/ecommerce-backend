from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailCheckViewTestCase(APITestCase):
    """Test cases for the email check endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.url = reverse('check_email')
        # Create a test user
        self.existing_user = User.objects.create_user(
            email='existing@example.com',
            full_name='Existing User',
            password='testpass123'
        )
    
    def test_email_check_existing_email(self):
        """Test checking an email that already exists"""
        data = {'email': 'existing@example.com'}
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'existing@example.com')
        self.assertTrue(response.data['is_registered'])
        self.assertEqual(response.data['message'], 'Email is already registered')
    
    def test_email_check_new_email(self):
        """Test checking an email that doesn't exist"""
        data = {'email': 'new@example.com'}
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'new@example.com')
        self.assertFalse(response.data['is_registered'])
        self.assertEqual(response.data['message'], 'Email is available')
    
    def test_email_check_invalid_email_format(self):
        """Test checking with invalid email format"""
        data = {'email': 'invalid-email'}
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('Enter a valid email address', str(response.data['email']))
    
    def test_email_check_missing_email_field(self):
        """Test checking without email field"""
        data = {}
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('This field is required', str(response.data['email']))
    
    def test_email_check_empty_email(self):
        """Test checking with empty email field"""
        data = {'email': ''}
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_email_check_case_insensitive(self):
        """Test that email check is case insensitive"""
        # Create user with lowercase email
        User.objects.create_user(
            email='casetest@example.com',
            full_name='Case Test User',
            password='testpass123'
        )
        
        # Test with uppercase email
        data = {'email': 'CASETEST@EXAMPLE.COM'}
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_registered'])
    
    def test_email_check_method_not_allowed(self):
        """Test that only POST method is allowed"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        response = self.client.put(self.url, {'email': 'test@example.com'})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)