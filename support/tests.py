from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import SupportTicket
from django.urls import reverse

User = get_user_model()

class SupportTicketAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user1', password='pass123')
        self.admin = User.objects.create_superuser(username='admin', password='admin123')
        self.ticket = SupportTicket.objects.create(user=self.user, subject='Issue A', message='Help me')

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_user_can_create_ticket(self):
        self.authenticate(self.user)
        data = {'subject': 'New Issue', 'message': 'Please check this'}
        response = self.client.post(reverse('support:list-create'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_can_list_own_tickets(self):
        self.authenticate(self.user)
        response = self.client.get(reverse('support:list-create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_admin_can_see_all_tickets(self):
        self.authenticate(self.admin)
        response = self.client.get(reverse('support:list-create'))
        self.assertEqual(len(response.data), SupportTicket.objects.count())

    def test_user_cannot_see_others_ticket(self):
        user2 = User.objects.create_user(username='user2', password='pass123')
        self.authenticate(user2)
        response = self.client.get(reverse('support:detail', kwargs={'pk': self.ticket.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_ticket(self):
        self.authenticate(self.admin)
        data = {'subject': 'Updated', 'message': 'Updated msg', 'status': 'resolved'}
        response = self.client.put(reverse('support:detail', kwargs={'pk': self.ticket.id}), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, 'resolved')

    def test_user_can_update_own_ticket(self):
        self.authenticate(self.user)
        data = {'subject': 'New', 'message': 'Updated msg', 'status': 'in_progress'}
        response = self.client.put(reverse('support:detail', kwargs={'pk': self.ticket.id}), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_cannot_delete_others_ticket(self):
        user2 = User.objects.create_user(username='user2', password='pass123')
        self.authenticate(user2)
        response = self.client.delete(reverse('support:detail', kwargs={'pk': self.ticket.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
