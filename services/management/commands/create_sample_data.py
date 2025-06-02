from django.core.management.base import BaseCommand
from services.models import Service, ServiceCategory
from users.models import User

class Command(BaseCommand):
    help = 'Create sample services and categories for testing'

    def handle(self, *args, **options):
        self.stdout.write("🏠 Creating Sample Home Services Data...")
        
        # Create admin user if doesn't exist
        admin_user, created = User.objects.get_or_create(
            email='admin@homeservice.com',
            defaults={
                'first_name': 'Admin',
                'last_name': 'User',
                'user_type': 'admin',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(f"✅ Created admin user: {admin_user.email}")
        else:
            self.stdout.write(f"✅ Admin user exists: {admin_user.email}")
        
        # Create categories
        categories_data = [
            {'name': 'Plumbing', 'slug': 'plumbing', 'description': 'Plumbing repair and installation services'},
            {'name': 'Electrical', 'slug': 'electrical', 'description': 'Electrical repair and installation services'},
            {'name': 'Cleaning', 'slug': 'cleaning', 'description': 'Home and office cleaning services'},
            {'name': 'Painting', 'slug': 'painting', 'description': 'Interior and exterior painting services'},
            {'name': 'AC Service', 'slug': 'ac-service', 'description': 'Air conditioning repair and maintenance'},
        ]
        
        created_categories = []
        for cat_data in categories_data:
            category, created = ServiceCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            created_categories.append(category)
            if created:
                self.stdout.write(f"✅ Created category: {category.name}")
        
        # Create sample services
        services_data = [
            {
                'name': 'Basic Plumbing Repair',
                'category': created_categories[0],  # Plumbing
                'price': 500.00,
                'duration': 2,
                'description': 'Fix leaks, unclog drains, and basic plumbing repairs for your home'
            },
            {
                'name': 'Electrical Installation',
                'category': created_categories[1],  # Electrical
                'price': 800.00,
                'duration': 3,
                'description': 'Install switches, outlets, fans, and basic electrical work'
            },
            {
                'name': 'Deep House Cleaning',
                'category': created_categories[2],  # Cleaning
                'price': 1200.00,
                'duration': 4,
                'description': 'Complete deep cleaning of your home including all rooms and bathrooms'
            },
            {
                'name': 'Interior Wall Painting',
                'category': created_categories[3],  # Painting
                'price': 2000.00,
                'duration': 6,
                'description': 'Professional interior wall painting service with premium quality paint'
            },
            {
                'name': 'AC Repair & Service',
                'category': created_categories[4],  # AC Service
                'price': 600.00,
                'duration': 2,
                'description': 'Air conditioning repair, cleaning, and maintenance service'
            },
        ]
        
        for service_data in services_data:
            service, created = Service.objects.get_or_create(
                name=service_data['name'],
                defaults={
                    'description': service_data['description'],
                    'price': service_data['price'],
                    'category': service_data['category'],
                    'provider': admin_user,
                    'duration': service_data['duration'],
                    'is_available': True,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f"✅ Created service: {service.name} - ₹{service.price}")
        
        self.stdout.write(f"\n🎉 Sample data creation complete!")
        self.stdout.write(f"📊 Total Services: {Service.objects.count()}")
        self.stdout.write(f"📊 Total Categories: {ServiceCategory.objects.count()}")
        self.stdout.write(f"\n🔗 Admin Login: admin@homeservice.com / admin123")
        self.stdout.write(f"🔗 Admin Services URL: http://127.0.0.1:8000/services/admin-services/")
