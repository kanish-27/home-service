from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

from services.models import Service, ServiceCategory
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Add sample services to the database'

    def handle(self, *args, **options):
        # Create sample categories if they don't exist
        categories = {
            'electrical': 'Electrical',
            'plumbing': 'Plumbing',
            'cleaning': 'Cleaning',
            'gardening': 'Gardening',
            'moving-packing': 'Moving & Packing',
            'home-repair': 'Home Repair',
            'pest-control': 'Pest Control',
            'handyman': 'Handyman',
            'painting': 'Painting'
        }
        
        for slug, name in categories.items():
            category, created = ServiceCategory.objects.get_or_create(
                name=name,
                defaults={'slug': slug}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {name}'))
        
        # Create sample services
        sample_services = [
            {
                'name': 'Electrical Installation',
                'category': 'Electrical',
                'price': 75.00,
                'duration': 180,
                'description': 'Professional installation of electrical systems in your home or office. Includes wiring, outlets, switches, and circuit breakers.'
            },
            {
                'name': 'Lighting Repair',
                'category': 'Electrical',
                'price': 50.00,
                'duration': 120,
                'description': 'Fix broken lights, install new lighting fixtures, and upgrade to energy-efficient LED lighting. Includes troubleshooting and replacement of faulty components.'
            },
            {
                'name': 'Circuit Breaker Repair',
                'category': 'Electrical',
                'price': 60.00,
                'duration': 120,
                'description': 'Professional repair and replacement of circuit breakers. Includes troubleshooting electrical issues, safety checks, and ensuring proper functionality.'
            },
            {
                'name': 'Pipe Repair',
                'category': 'Plumbing',
                'price': 45.00,
                'duration': 120,
                'description': 'Professional repair of leaking or damaged pipes. Includes copper, PVC, and PEX pipe repairs.'
            },
            {
                'name': 'Leak Detection',
                'category': 'Plumbing',
                'price': 60.00,
                'duration': 60,
                'description': 'Advanced leak detection services using thermal imaging and acoustic detection.'
            },
            {
                'name': 'Water Heater Repair',
                'category': 'Plumbing',
                'price': 75.00,
                'duration': 120,
                'description': 'Professional repair and maintenance of water heaters. Includes gas and electric systems.'
            },
        ]
        
        # Get or create a sample provider
        try:
            provider = User.objects.get(username='sample_provider')
        except User.DoesNotExist:
            provider = User.objects.create_user(
                username='sample_provider',
                email='provider@example.com',
                password='sample_password'
            )
            self.stdout.write(self.style.SUCCESS('Created sample provider'))
        
        # Create services
        for service_data in sample_services:
            category = ServiceCategory.objects.get(name=service_data['category'])
            service = Service.objects.create(
                name=service_data['name'],
                category=category,
                provider=provider,
                description=service_data['description'],
                price=service_data['price'],
                duration=service_data['duration'],
                is_available=True,
                status='active',
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            self.stdout.write(self.style.SUCCESS(f'Created service: {service.name}'))
