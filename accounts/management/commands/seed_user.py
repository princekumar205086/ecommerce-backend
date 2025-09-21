# seeding user and supplier for testing
from django.core.management.base import BaseCommand
from accounts.models import User
from django.db import IntegrityError

class Command(BaseCommand):
    help = 'Seed the database with a test user and supplier'

    def handle(self, *args, **kwargs):
        users = [
            {
                'email': 'user@example.com',
                'password': 'User@123',
                'full_name': 'Test User',
                'contact': '9876543210',
                'role': 'user',
                'is_active': True,
                'email_verified': True
            },
            {
                'email': 'supplier@example.com',
                'password': 'Supplier@123',
                'full_name': 'Test Supplier',
                'contact': '0123456789',
                'role': 'supplier',
                'is_active': True,
                'email_verified': True
            }
        ]

        for user_data in users:
            email = user_data['email']
            password = user_data['password']
            full_name = user_data['full_name']
            contact = user_data['contact']
            role = user_data['role']

            try:
                user = User.objects.create_user(email=email, password=password)
                user.full_name = full_name
                user.contact = contact
                user.role = role
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Successfully created user: {user.email}'))
            except IntegrityError:
                self.stdout.write(self.style.WARNING(f'User with email {email} already exists.'))
