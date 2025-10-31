from django.core.management.base import BaseCommand
from app1.models import ServiceCategory

class Command(BaseCommand):
    help = 'Create default service categories'

    def handle(self, *args, **kwargs):
        categories = [
            {
                'name': 'Towing Service',
                'description': 'Vehicle towing to nearest garage or preferred location',
                'icon': 'fa-truck-pickup'
            },
            {
                'name': 'Fuel Delivery',
                'description': '24/7 fuel delivery service to get you back on the road',
                'icon': 'fa-gas-pump'
            },
            {
                'name': 'Battery Jump Start',
                'description': 'Quick battery jump start service',
                'icon': 'fa-car-battery'
            },
            {
                'name': 'Tire Change',
                'description': 'Flat tire change with spare tire',
                'icon': 'fa-tire'
            },
            {
                'name': 'Lockout Service',
                'description': 'Vehicle lockout assistance',
                'icon': 'fa-key'
            },
            {
                'name': 'On-Site Mechanic',
                'description': 'Mobile mechanic for on-site repairs',
                'icon': 'fa-wrench'
            },
        ]

        for cat_data in categories:
            category, created = ServiceCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'icon': cat_data['icon'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Category already exists: {category.name}'))

        self.stdout.write(self.style.SUCCESS('Service categories setup complete!'))
