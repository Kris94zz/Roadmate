from django.core.management.base import BaseCommand
from app1.models import ServiceProvider

class Command(BaseCommand):
    help = 'Approve a service provider by username'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the provider to approve')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        
        try:
            provider = ServiceProvider.objects.get(user__username=username)
            
            # Approve the provider
            provider.is_approved = True
            provider.save()
            
            # Activate the user account
            user = provider.user
            user.is_active = True
            user.save()
            
            self.stdout.write(self.style.SUCCESS(
                f'Successfully approved provider: {provider.company_name} ({username})'
            ))
            self.stdout.write(self.style.SUCCESS(
                f'User account activated: {user.username}'
            ))
            
        except ServiceProvider.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f'Provider with username "{username}" not found'
            ))
