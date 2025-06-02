from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from services.models import Service, ServiceCategory
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample service providers and their services'

    def handle(self, *args, **options):
        # Sample service categories
        categories = [
            'Plumbing',
            'Electrical',
            'Cleaning',
            'Carpentry',
            'Painting',
            'Landscaping'
        ]

        # Create service categories if they don't exist
        for category_name in categories:
            ServiceCategory.objects.get_or_create(name=category_name)

        # Sample provider data
        providers = [
            {
                'email': 'plumber1@servicepro.com',
                'name': 'John Plumber',
                'category': 'Plumbing',
                'services': [
                    {'name': 'Pipe Installation', 'duration': 2, 'price': 5000},
                    {'name': 'Leak Repair', 'duration': 1, 'price': 3000},
                    {'name': 'Water Heater Repair', 'duration': 2, 'price': 4000}
                ]
            },
            {
                'email': 'electrician1@servicepro.com',
                'name': 'Mike Electrician',
                'category': 'Electrical',
                'services': [
                    {'name': 'Wiring Installation', 'duration': 3, 'price': 6000},
                    {'name': 'Light Fixtures', 'duration': 1, 'price': 2500},
                    {'name': 'Circuit Breaker', 'duration': 2, 'price': 3500}
                ]
            },
            {
                'email': 'cleaner1@servicepro.com',
                'name': 'Sarah Cleaner',
                'category': 'Cleaning',
                'services': [
                    {'name': 'Deep Cleaning', 'duration': 4, 'price': 4000},
                    {'name': 'Carpet Cleaning', 'duration': 2, 'price': 3000},
                    {'name': 'Window Cleaning', 'duration': 3, 'price': 2000}
                ]
            }
        ]

        # Create sample providers and their services
        for provider_data in providers:
            # Create user
            user = User.objects.create_user(
                email=provider_data['email'],
                password='provider123',
                first_name=provider_data['name'].split()[0],
                last_name=' '.join(provider_data['name'].split()[1:]),
                user_type='provider'
            )



            # Get category
            category = ServiceCategory.objects.get(name=provider_data['category'])

            # Create services
            for service_data in provider_data['services']:
                Service.objects.create(
                    provider=user,
                    category=category,
                    name=service_data['name'],
                    duration=service_data['duration'],
                    price=service_data['price'],
                    description=f"Professional {service_data['name'].lower()} service by {provider_data['name']}",
                    is_available=True,
                    status='active'
                )

        self.stdout.write(self.style.SUCCESS('Successfully created sample service providers and their services'))
