# seeding user
from django.core.management.base import BaseCommand
from accounts.models import User
from django.db import IntegrityError

class Command(BaseCommand):
    help = 'Seed the database with a test user'

    def handle(self, *args, **kwargs):
        email = 'user@example.com'
        password = 'User@123'
        try:
            user = User.objects.create_user(email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Successfully created user: {user.email}'))
        except IntegrityError:
            self.stdout.write(self.style.WARNING(f'User with email {email} already exists.'))