from django.core.management.base import BaseCommand
from apps.accounts.models import User


class Command(BaseCommand):
    help = 'Create an admin user'

    def handle(self, *args, **options):
        if User.objects.filter(username='Admin').exists():
            self.stdout.write(self.style.WARNING('Admin user already exists'))
            return

        user = User.objects.create_user(
            username='Admin',
            email='admin@zustore.com',
            password='1234',
            role='ADMIN'
        )
        user.is_staff = True
        user.is_superuser = True
        user.save()
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created admin user: {user.username}'))
        self.stdout.write(self.style.SUCCESS(f'Username: Admin'))
        self.stdout.write(self.style.SUCCESS(f'Password: 1234'))
        self.stdout.write(self.style.SUCCESS(f'Role: ADMIN'))
