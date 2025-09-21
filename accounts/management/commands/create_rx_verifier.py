# accounts/management/commands/create_rx_verifier.py
import os
import secrets
import string
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Create RX verifier account with email notification'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True, help='Email for the RX verifier')
        parser.add_argument('--full_name', type=str, required=True, help='Full name for the RX verifier')
        parser.add_argument('--contact', type=str, required=True, help='Contact number for the RX verifier')
        parser.add_argument('--password', type=str, help='Custom password (if not provided, will be generated)')
        parser.add_argument('--send-email', action='store_true', help='Send credentials via email')

    def handle(self, *args, **options):
        email = options['email']
        full_name = options['full_name']
        contact = options['contact']
        custom_password = options.get('password')
        send_email = options.get('send_email', False)

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            raise CommandError(f'User with email {email} already exists')

        # Generate password if not provided
        if not custom_password:
            # Generate a secure password
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
            password = ''.join(secrets.choice(alphabet) for i in range(12))
        else:
            password = custom_password

        try:
            with transaction.atomic():
                # Create RX verifier account
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    full_name=full_name,
                    contact=contact,
                    role='rx_verifier',
                    email_verified=True,  # Admin created accounts are pre-verified
                    is_active=True
                )

                self.stdout.write(
                    self.style.SUCCESS(f'✅ RX verifier account created successfully')
                )
                self.stdout.write(f'📧 Email: {email}')
                self.stdout.write(f'👤 Name: {full_name}')
                self.stdout.write(f'📱 Contact: {contact}')
                self.stdout.write(f'🔑 Password: {password}')

                # Send credentials via email if requested
                if send_email:
                    success, message = user.send_rx_verifier_credentials(password)
                    if success:
                        self.stdout.write(
                            self.style.SUCCESS(f'📧 Credentials sent to {email}')
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'❌ Failed to send email: {message}')
                        )
                        self.stdout.write(
                            self.style.WARNING('⚠️ Please send credentials manually')
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING('📧 Email not sent. Use --send-email flag to send credentials automatically')
                    )

                # Create workload tracking record
                from rx_upload.models import VerifierWorkload
                VerifierWorkload.objects.create(
                    verifier=user,
                    is_available=True,
                    max_daily_capacity=50
                )

                self.stdout.write(
                    self.style.SUCCESS(f'📊 Workload tracking initialized for {full_name}')
                )

        except Exception as e:
            raise CommandError(f'Failed to create RX verifier account: {str(e)}')