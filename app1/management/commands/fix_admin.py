from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Fix admin user permissions'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Create admin user if it doesn't exist
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@roadmate.com',
                password='roadmate'
            )
            self.stdout.write(self.style.SUCCESS('Created admin user'))
        else:
            admin = User.objects.get(username='admin')
            admin.is_staff = True
            admin.is_superuser = True
            admin.set_password('roadmate')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Updated admin user permissions'))
        
        # Print admin user details
        admin = User.objects.get(username='admin')
        self.stdout.write(self.style.SUCCESS('\nAdmin User Details:'))
        self.stdout.write(f'Username: {admin.username}')
        self.stdout.write(f'Email: {admin.email}')
        self.stdout.write(f'is_staff: {admin.is_staff}')
        self.stdout.write(f'is_superuser: {admin.is_superuser}')
