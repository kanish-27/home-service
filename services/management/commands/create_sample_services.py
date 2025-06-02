from django.core.management.base import BaseCommand
from services.models import Service, ServiceCategory, ProviderProfile
from users.models import User
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create sample services for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample services...')

        # Create categories
        categories_data = [
            {'name': 'Electrical', 'description': 'Electrical services for home and office', 'slug': 'electrical'},
            {'name': 'Plumbing', 'description': 'Plumbing services and repairs', 'slug': 'plumbing'},
            {'name': 'Cleaning', 'description': 'Professional cleaning services', 'slug': 'cleaning'},
            {'name': 'HVAC', 'description': 'Heating, ventilation, and air conditioning', 'slug': 'hvac'},
            {'name': 'Repair', 'description': 'General repair services', 'slug': 'repair'},
            {'name': 'Painting', 'description': 'Professional painting services', 'slug': 'painting'},
        ]

        for cat_data in categories_data:
            category, created = ServiceCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')

        # Create provider users
        providers_data = [
            {'email': 'rajesh@example.com', 'first_name': 'Rajesh', 'last_name': 'Kumar', 'company_name': 'Kumar Electrical Services'},
            {'email': 'amit@example.com', 'first_name': 'Amit', 'last_name': 'Sharma', 'company_name': 'Sharma Plumbing Works'},
            {'email': 'priya@example.com', 'first_name': 'Priya', 'last_name': 'Singh', 'company_name': 'Singh Electrical Solutions'},
            {'email': 'suresh@example.com', 'first_name': 'Suresh', 'last_name': 'Patel', 'company_name': 'Patel Plumbing Services'},
            {'email': 'sunita@example.com', 'first_name': 'Sunita', 'last_name': 'Joshi', 'company_name': 'Joshi Cleaning Services'},
        ]

        for prov_data in providers_data:
            user, created = User.objects.get_or_create(
                email=prov_data['email'],
                defaults={
                    'first_name': prov_data['first_name'],
                    'last_name': prov_data['last_name'],
                    'user_type': 'provider',
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'Created provider user: {user.email}')

            profile, created = ProviderProfile.objects.get_or_create(
                user=user,
                defaults={
                    'company_name': prov_data['company_name'],
                    'phone_number': f'+91 987654{len(ProviderProfile.objects.all()) + 3210}',
                    'address': f'{prov_data["first_name"]} Street, Mumbai, Maharashtra',
                    'business_description': f'Professional {prov_data["company_name"]} with years of experience.'
                }
            )

        # Get categories and providers
        electrical = ServiceCategory.objects.get(name='Electrical')
        plumbing = ServiceCategory.objects.get(name='Plumbing')
        cleaning = ServiceCategory.objects.get(name='Cleaning')
        hvac = ServiceCategory.objects.get(name='HVAC')
        repair = ServiceCategory.objects.get(name='Repair')
        painting = ServiceCategory.objects.get(name='Painting')

        rajesh_user = User.objects.get(email='rajesh@example.com')
        amit_user = User.objects.get(email='amit@example.com')
        priya_user = User.objects.get(email='priya@example.com')
        suresh_user = User.objects.get(email='suresh@example.com')
        sunita_user = User.objects.get(email='sunita@example.com')

        # Create services
        services_data = [
            # Electrical Services
            {'name': 'Electrical Installation', 'category': electrical, 'provider': rajesh_user, 'price': Decimal('2500.00'), 'duration': 3, 'description': 'Professional installation of electrical systems in your home or office. Includes wiring, outlets, switches, and circuit breakers.'},
            {'name': 'Lighting Repair', 'category': electrical, 'provider': rajesh_user, 'price': Decimal('1500.00'), 'duration': 2, 'description': 'Fix broken lights, install new lighting fixtures, and upgrade to energy-efficient LED lighting.'},
            {'name': 'Circuit Breaker Repair', 'category': electrical, 'provider': priya_user, 'price': Decimal('2000.00'), 'duration': 2, 'description': 'Professional repair and replacement of circuit breakers. Safety checks included.'},

            # Plumbing Services
            {'name': 'Pipe Repair', 'category': plumbing, 'provider': suresh_user, 'price': Decimal('1200.00'), 'duration': 2, 'description': 'Professional repair of leaking or damaged pipes. Includes copper, PVC, and PEX pipe repairs.'},
            {'name': 'Leak Detection', 'category': plumbing, 'provider': amit_user, 'price': Decimal('1800.00'), 'duration': 1, 'description': 'Advanced leak detection services using thermal imaging and acoustic detection.'},
            {'name': 'Water Heater Repair', 'category': plumbing, 'provider': suresh_user, 'price': Decimal('2200.00'), 'duration': 2, 'description': 'Professional repair and maintenance of water heaters. Gas and electric systems.'},

            # Cleaning Services
            {'name': 'Deep Cleaning', 'category': cleaning, 'provider': sunita_user, 'price': Decimal('3500.00'), 'duration': 4, 'description': 'Comprehensive deep cleaning service for your entire home. Includes all rooms and surfaces.'},
            {'name': 'Carpet Cleaning', 'category': cleaning, 'provider': sunita_user, 'price': Decimal('2000.00'), 'duration': 3, 'description': 'Professional carpet cleaning using advanced steam cleaning technology.'},

            # HVAC Services
            {'name': 'AC Repair', 'category': hvac, 'provider': rajesh_user, 'price': Decimal('2800.00'), 'duration': 3, 'description': 'Professional air conditioning repair and maintenance services.'},
            {'name': 'AC Installation', 'category': hvac, 'provider': priya_user, 'price': Decimal('8500.00'), 'duration': 5, 'description': 'Professional air conditioning installation services.'},

            # Repair Services
            {'name': 'Furniture Repair', 'category': repair, 'provider': amit_user, 'price': Decimal('1800.00'), 'duration': 3, 'description': 'Professional furniture repair and restoration services.'},

            # Painting Services
            {'name': 'Interior Painting', 'category': painting, 'provider': sunita_user, 'price': Decimal('4500.00'), 'duration': 6, 'description': 'Professional interior painting services for homes and offices.'},
        ]

        for service_data in services_data:
            service, created = Service.objects.get_or_create(
                name=service_data['name'],
                provider=service_data['provider'],
                defaults={
                    'category': service_data['category'],
                    'description': service_data['description'],
                    'price': service_data['price'],
                    'duration': service_data['duration'],
                    'is_active': True,
                    'is_available': True
                }
            )
            if created:
                self.stdout.write(f'Created service: {service.name} - ₹{service.price}')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {Service.objects.count()} services!')
        )
