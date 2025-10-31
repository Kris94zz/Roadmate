from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Creates or updates the admin user'

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'admin'
        email = 'admin@roadmate.com'
        password = 'roadmate'
        
        if User.objects.filter(username=username).exists():
            admin = User.objects.get(username=username)
            admin.set_password(password)
            admin.email = email
            admin.is_staff = True
            admin.is_superuser = True
            admin.is_active = True
            admin.save()
            self.stdout.write(self.style.SUCCESS('Successfully updated admin user'))
        else:
            User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS('Successfully created admin user'))
            
        # Verify the user exists and has correct permissions
        admin = User.objects.get(username=username)
        self.stdout.write(self.style.SUCCESS(f'Admin user details:'))
        self.stdout.write(f'Username: {admin.username}')
        self.stdout.write(f'Email: {admin.email}')
        self.stdout.write(f'is_staff: {admin.is_staff}')
        self.stdout.write(f'is_superuser: {admin.is_superuser}')
        self.stdout.write(f'is_active: {admin.is_active}')
