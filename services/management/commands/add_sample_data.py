from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from services.models import ServiceCategory, Service, Booking, ProviderProfile
from users.models import User

class Command(BaseCommand):
    help = 'Add sample data for admin testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Adding sample data...'))
        
        # Create categories
        categories_data = [
            {'name': 'Electrical', 'slug': 'electrical', 'description': 'Professional electrical services'},
            {'name': 'Plumbing', 'slug': 'plumbing', 'description': 'Expert plumbing services'},
            {'name': 'Cleaning', 'slug': 'cleaning', 'description': 'Professional cleaning services'},
        ]
        
        for cat_data in categories_data:
            category, created = ServiceCategory.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'✅ Created category: {category.name}')
        
        # Create provider user
        provider_user, created = User.objects.get_or_create(
            email='provider@example.com',
            defaults={
                'first_name': 'Rajesh',
                'last_name': 'Kumar',
                'user_type': 'provider',
                'is_active': True
            }
        )
        if created:
            provider_user.set_password('provider123')
            provider_user.save()
            self.stdout.write(f'✅ Created provider user: {provider_user.get_full_name()}')
        
        # Create provider profile
        provider_profile, created = ProviderProfile.objects.get_or_create(
            user=provider_user,
            defaults={
                'company_name': 'Kumar Services',
                'business_description': 'Professional home services',
                'phone_number': '+91 9876543210',
                'address': 'Mumbai, Maharashtra',
                'is_verified': True,
                'is_available': True
            }
        )
        if created:
            self.stdout.write(f'✅ Created provider profile: {provider_profile.company_name}')
        
        # Create services
        electrical_cat = ServiceCategory.objects.get(slug='electrical')
        plumbing_cat = ServiceCategory.objects.get(slug='plumbing')
        cleaning_cat = ServiceCategory.objects.get(slug='cleaning')
        
        services_data = [
            {
                'name': 'Electrical Installation',
                'description': 'Professional electrical installation services',
                'price': 2500,
                'duration': timedelta(hours=3),
                'category': electrical_cat,
                'provider': provider_user
            },
            {
                'name': 'Pipe Repair',
                'description': 'Expert pipe repair services',
                'price': 1200,
                'duration': timedelta(hours=2),
                'category': plumbing_cat,
                'provider': provider_user
            },
            {
                'name': 'Deep Cleaning',
                'description': 'Comprehensive home cleaning',
                'price': 3500,
                'duration': timedelta(hours=4),
                'category': cleaning_cat,
                'provider': provider_user
            }
        ]
        
        for service_data in services_data:
            service, created = Service.objects.get_or_create(
                name=service_data['name'],
                provider=service_data['provider'],
                defaults=service_data
            )
            if created:
                self.stdout.write(f'✅ Created service: {service.name}')
        
        # Create customer
        customer, created = User.objects.get_or_create(
            email='customer@example.com',
            defaults={
                'first_name': 'John',
                'last_name': 'Doe',
                'user_type': 'customer',
                'is_active': True
            }
        )
        if created:
            customer.set_password('customer123')
            customer.save()
            self.stdout.write(f'✅ Created customer: {customer.get_full_name()}')
        
        # Create sample booking
        service = Service.objects.filter(name='Electrical Installation').first()
        if service:
            booking_date = timezone.now() + timedelta(days=1)
            booking, created = Booking.objects.get_or_create(
                service=service,
                customer=customer,
                defaults={
                    'provider': service.provider,
                    'booking_date': booking_date,
                    'start_time': booking_date,
                    'end_time': booking_date + service.duration,
                    'status': 'confirmed',
                    'payment_status': 'paid',
                    'is_paid': True,
                    'total_amount': service.price,
                    'special_instructions': 'Sample booking for admin testing'
                }
            )
            if created:
                self.stdout.write(f'✅ Created booking: {booking.service.name}')
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Sample data added successfully!'))
        self.stdout.write('📋 Admin can now:')
        self.stdout.write('   ✅ View and manage services')
        self.stdout.write('   ✅ See customer bookings')
        self.stdout.write('   ✅ Manage categories')
        self.stdout.write('   ✅ Monitor provider profiles')
