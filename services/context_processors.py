from django.conf import settings

def sample_services(request):
    """Context processor to provide sample services for development"""
    if settings.DEBUG:
        sample_services = [
            {
                'id': 1,
                'name': 'Plumbing Repair',
                'description': 'Professional plumbing repairs and installations. Fix leaks, unclog drains, and more.',
                'price': 1500,
                'duration': 2,
                'category': 'Plumbing',
                'provider': {
                    'name': 'Rajesh Kumar',
                    'email': 'rajesh@example.com'
                }
            },
            {
                'id': 2,
                'name': 'Electrical Work',
                'description': 'Licensed electrician for home electrical repairs and installations.',
                'price': 2200,
                'duration': 3,
                'category': 'Electrical',
                'provider': {
                    'name': 'Priya Sharma',
                    'email': 'priya@example.com'
                }
            },
            {
                'id': 3,
                'name': 'Carpet Cleaning',
                'description': 'Deep cleaning for carpets and rugs. Remove stains and freshen your home.',
                'price': 1800,
                'duration': 1,
                'category': 'Cleaning',
                'provider': {
                    'name': 'Amit Singh',
                    'email': 'amit@example.com'
                }
            },
            {
                'id': 4,
                'name': 'Garden Maintenance',
                'description': 'Regular garden care and maintenance services.',
                'price': 1200,
                'duration': 2,
                'category': 'Gardening',
                'provider': {
                    'name': 'Sunita Patel',
                    'email': 'sunita@example.com'
                }
            }
        ]
        return {'sample_services': sample_services}
    return {}
