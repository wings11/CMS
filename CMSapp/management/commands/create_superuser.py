from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Create a superuser if environment variables are set'

    def handle(self, *args, **options):
        # Check if superuser credentials are provided via environment variables
        superuser_username = os.environ.get('SUPERUSER_USERNAME')
        superuser_email = os.environ.get('SUPERUSER_EMAIL')
        superuser_password = os.environ.get('SUPERUSER_PASSWORD')

        if not all([superuser_username, superuser_email, superuser_password]):
            self.stdout.write(
                self.style.WARNING(
                    'Superuser environment variables not set. Skipping superuser creation.\n'
                    'Set SUPERUSER_USERNAME, SUPERUSER_EMAIL, and SUPERUSER_PASSWORD to create a superuser.'
                )
            )
            return

        # Check if superuser already exists
        if User.objects.filter(username=superuser_username).exists():
            self.stdout.write(
                self.style.SUCCESS(f'Superuser "{superuser_username}" already exists.')
            )
            return

        # Create the superuser
        try:
            User.objects.create_superuser(
                username=superuser_username,
                email=superuser_email,
                password=superuser_password
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser "{superuser_username}".')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create superuser: {e}')
            )