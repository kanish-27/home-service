from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from django.views import View
from users.models import User

from .models import Service, ServiceCategory, Booking, Review, ProviderProfile
from .forms import ServiceForm, BookingForm, ReviewForm, RescheduleBookingForm



def check_mongodb_connection(request):
    try:
        # Try to connect to MongoDB and fetch a document
        service = Service.objects.first()
        if service:
            return JsonResponse({
                'status': 'success',
                'connected': True,
                'message': 'Successfully connected to MongoDB'
            })
        else:
            return JsonResponse({
                'status': 'success',
                'connected': True,
                'message': 'Connected to MongoDB, but no documents found'
            })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'connected': False,
            'message': f'Error connecting to MongoDB: {str(e)}'
        })

def mongodb_status(request):
    return render(request, 'services/mongodb_status.html')

class ServiceListView(View):
    template_name = 'services/service_list.html'

    def get(self, request, category_slug=None):
        # Get search and filter parameters
        query = request.GET.get('q', '')
        category = request.GET.get('category', '') or category_slug  # Use URL parameter if available
        min_price = request.GET.get('min_price', '')
        max_price = request.GET.get('max_price', '')
        sort_by = request.GET.get('sort_by', 'recent')

        # Start with all available services or create sample data
        services = self.get_sample_services()

        # Apply filters
        if query:
            services = [s for s in services if query.lower() in s['name'].lower() or query.lower() in s['description'].lower()]

        if category:
            services = [s for s in services if s['category_slug'] == category]

        if min_price:
            try:
                min_price = float(min_price)
                services = [s for s in services if s['price'] >= min_price]
            except ValueError:
                pass

        if max_price:
            try:
                max_price = float(max_price)
                services = [s for s in services if s['price'] <= max_price]
            except ValueError:
                pass

        # Apply sorting
        if sort_by == 'price_asc':
            services.sort(key=lambda x: x['price'])
        elif sort_by == 'price_desc':
            services.sort(key=lambda x: x['price'], reverse=True)
        elif sort_by == 'rating':
            services.sort(key=lambda x: x['average_rating'], reverse=True)
        # Default is 'recent' - already in order

        # Add comprehensive categories for filter dropdown with accurate service counts
        categories = [
            {'name': 'Electrical', 'slug': 'electrical', 'service_count': 3},
            {'name': 'Plumbing', 'slug': 'plumbing', 'service_count': 3},
            {'name': 'Cleaning', 'slug': 'cleaning', 'service_count': 3},
            {'name': 'Carpentry', 'slug': 'carpentry', 'service_count': 2},
            {'name': 'Painting', 'slug': 'painting', 'service_count': 2},
            {'name': 'Appliance Repair', 'slug': 'appliance-repair', 'service_count': 2},
            {'name': 'HVAC', 'slug': 'hvac', 'service_count': 2},
            {'name': 'Landscaping', 'slug': 'landscaping', 'service_count': 2},
            {'name': 'Security', 'slug': 'security', 'service_count': 2},
            {'name': 'Pest Control', 'slug': 'pest-control', 'service_count': 2},
            {'name': 'Handyman', 'slug': 'handyman', 'service_count': 2},
            {'name': 'Moving & Packing', 'slug': 'moving-packing', 'service_count': 2},
        ]

        # Get selected category info for template
        selected_category = None
        if category:
            selected_category = next((cat for cat in categories if cat['slug'] == category), None)

        context = {
            'services': services,
            'categories': categories,
            'selected_category': selected_category,
            'current_category': category,
        }

        return render(request, self.template_name, context)

    def get_sample_services(self):
        """Return sample services for demonstration"""
        return [
            # Electrical Services
            {
                'id': 1,
                'name': 'Electrical Installation',
                'description': 'Professional installation of electrical systems in your home or office. Includes wiring, outlets, switches, and circuit breakers.',
                'price': 2500,
                'duration': 3,
                'average_rating': 4.5,
                'review_count': 12,
                'category_name': 'Electrical',
                'category_slug': 'electrical',
                'provider': {'user': {'get_full_name': 'Rajesh Kumar', 'email': 'rajesh@example.com'}},
                'image': None
            },
            {
                'id': 2,
                'name': 'Lighting Repair',
                'description': 'Fix broken lights, install new lighting fixtures, and upgrade to energy-efficient LED lighting.',
                'price': 1500,
                'duration': 2,
                'average_rating': 4.8,
                'review_count': 8,
                'category_name': 'Electrical',
                'category_slug': 'electrical',
                'provider': {'user': {'get_full_name': 'Amit Sharma', 'email': 'amit@example.com'}},
                'image': None
            },
            {
                'id': 3,
                'name': 'Circuit Breaker Repair',
                'description': 'Professional repair and replacement of circuit breakers. Safety checks included.',
                'price': 2000,
                'duration': 2,
                'average_rating': 4.7,
                'review_count': 15,
                'category_name': 'Electrical',
                'category_slug': 'electrical',
                'provider': {'user': {'get_full_name': 'Priya Singh', 'email': 'priya@example.com'}},
                'image': None
            },
            # Plumbing Services
            {
                'id': 4,
                'name': 'Pipe Repair',
                'description': 'Professional repair of leaking or damaged pipes. Includes copper, PVC, and PEX pipe repairs.',
                'price': 1200,
                'duration': 2,
                'average_rating': 4.6,
                'review_count': 10,
                'category_name': 'Plumbing',
                'category_slug': 'plumbing',
                'provider': {'user': {'get_full_name': 'Suresh Patel', 'email': 'suresh@example.com'}},
                'image': None
            },
            {
                'id': 5,
                'name': 'Leak Detection',
                'description': 'Advanced leak detection services using thermal imaging and acoustic detection.',
                'price': 1800,
                'duration': 1,
                'average_rating': 4.9,
                'review_count': 14,
                'category_name': 'Plumbing',
                'category_slug': 'plumbing',
                'provider': {'user': {'get_full_name': 'Kavita Reddy', 'email': 'kavita@example.com'}},
                'image': None
            },
            {
                'id': 6,
                'name': 'Water Heater Repair',
                'description': 'Professional repair and maintenance of water heaters. Gas and electric systems.',
                'price': 2200,
                'duration': 2,
                'average_rating': 4.7,
                'review_count': 18,
                'category_name': 'Plumbing',
                'category_slug': 'plumbing',
                'provider': {'user': {'get_full_name': 'Vikram Gupta', 'email': 'vikram@example.com'}},
                'image': None
            },
            # Cleaning Services
            {
                'id': 7,
                'name': 'Deep Cleaning',
                'description': 'Comprehensive deep cleaning service for your entire home. Includes all rooms and surfaces.',
                'price': 3500,
                'duration': 4,
                'average_rating': 4.8,
                'review_count': 22,
                'category_name': 'Cleaning',
                'category_slug': 'cleaning',
                'provider': {'user': {'get_full_name': 'Sunita Joshi', 'email': 'sunita@example.com'}},
                'image': None
            },
            {
                'id': 8,
                'name': 'Carpet Cleaning',
                'description': 'Professional carpet cleaning using advanced steam cleaning technology.',
                'price': 1800,
                'duration': 2,
                'average_rating': 4.6,
                'review_count': 16,
                'category_name': 'Cleaning',
                'category_slug': 'cleaning',
                'provider': {'user': {'get_full_name': 'Ravi Mehta', 'email': 'ravi@example.com'}},
                'image': None
            },
            {
                'id': 9,
                'name': 'Window Cleaning',
                'description': 'Professional window cleaning for interior and exterior windows.',
                'price': 1000,
                'duration': 1,
                'average_rating': 4.5,
                'review_count': 9,
                'category_name': 'Cleaning',
                'category_slug': 'cleaning',
                'provider': {'user': {'get_full_name': 'Neha Agarwal', 'email': 'neha@example.com'}},
                'image': None
            },
            # Carpentry Services
            {
                'id': 10,
                'name': 'Furniture Repair',
                'description': 'Professional furniture repair and restoration services.',
                'price': 1800,
                'duration': 3,
                'average_rating': 4.7,
                'review_count': 11,
                'category_name': 'Carpentry',
                'category_slug': 'carpentry',
                'provider': {'user': {'get_full_name': 'Manoj Kumar', 'email': 'manoj@example.com'}},
                'image': None
            },
            {
                'id': 11,
                'name': 'Cabinet Installation',
                'description': 'Custom cabinet installation and fitting services.',
                'price': 4500,
                'duration': 6,
                'average_rating': 4.8,
                'review_count': 8,
                'category_name': 'Carpentry',
                'category_slug': 'carpentry',
                'provider': {'user': {'get_full_name': 'Ramesh Yadav', 'email': 'ramesh@example.com'}},
                'image': None
            },
            # Painting Services
            {
                'id': 12,
                'name': 'Interior Painting',
                'description': 'Professional interior wall painting with premium quality paints.',
                'price': 3000,
                'duration': 5,
                'average_rating': 4.6,
                'review_count': 13,
                'category_name': 'Painting',
                'category_slug': 'painting',
                'provider': {'user': {'get_full_name': 'Deepak Singh', 'email': 'deepak@example.com'}},
                'image': None
            },
            {
                'id': 13,
                'name': 'Exterior Painting',
                'description': 'Weather-resistant exterior painting for homes and buildings.',
                'price': 5500,
                'duration': 8,
                'average_rating': 4.7,
                'review_count': 9,
                'category_name': 'Painting',
                'category_slug': 'painting',
                'provider': {'user': {'get_full_name': 'Kiran Sharma', 'email': 'kiran@example.com'}},
                'image': None
            },
            # Appliance Repair Services
            {
                'id': 14,
                'name': 'AC Repair',
                'description': 'Professional air conditioning repair and maintenance services.',
                'price': 2500,
                'duration': 2,
                'average_rating': 4.8,
                'review_count': 19,
                'category_name': 'Appliance Repair',
                'category_slug': 'appliance-repair',
                'provider': {'user': {'get_full_name': 'Rohit Sharma', 'email': 'rohit@example.com'}},
                'image': None
            },
            {
                'id': 15,
                'name': 'Washing Machine Repair',
                'description': 'Expert washing machine repair and maintenance services.',
                'price': 1800,
                'duration': 2,
                'average_rating': 4.5,
                'review_count': 14,
                'category_name': 'Appliance Repair',
                'category_slug': 'appliance-repair',
                'provider': {'user': {'get_full_name': 'Santosh Kumar', 'email': 'santosh@example.com'}},
                'image': None
            },
            # HVAC Services
            {
                'id': 16,
                'name': 'AC Installation',
                'description': 'Professional air conditioning installation with warranty.',
                'price': 8000,
                'duration': 4,
                'average_rating': 4.9,
                'review_count': 7,
                'category_name': 'HVAC',
                'category_slug': 'hvac',
                'provider': {'user': {'get_full_name': 'Ankit Verma', 'email': 'ankit@example.com'}},
                'image': None
            },
            {
                'id': 17,
                'name': 'Duct Cleaning',
                'description': 'Professional air duct cleaning and maintenance services.',
                'price': 3500,
                'duration': 3,
                'average_rating': 4.6,
                'review_count': 6,
                'category_name': 'HVAC',
                'category_slug': 'hvac',
                'provider': {'user': {'get_full_name': 'Mukesh Patel', 'email': 'mukesh@example.com'}},
                'image': None
            },
            # Landscaping Services
            {
                'id': 18,
                'name': 'Garden Maintenance',
                'description': 'Complete garden maintenance including pruning, weeding, and fertilizing.',
                'price': 2000,
                'duration': 3,
                'average_rating': 4.5,
                'review_count': 8,
                'category_name': 'Landscaping',
                'category_slug': 'landscaping',
                'provider': {'user': {'get_full_name': 'Sanjay Patel', 'email': 'sanjay@example.com'}},
                'image': None
            },
            {
                'id': 19,
                'name': 'Lawn Mowing',
                'description': 'Regular lawn mowing and grass cutting services.',
                'price': 800,
                'duration': 1,
                'average_rating': 4.4,
                'review_count': 12,
                'category_name': 'Landscaping',
                'category_slug': 'landscaping',
                'provider': {'user': {'get_full_name': 'Gopal Singh', 'email': 'gopal@example.com'}},
                'image': None
            },
            # Security Services
            {
                'id': 20,
                'name': 'CCTV Installation',
                'description': 'Professional CCTV camera installation and setup.',
                'price': 5500,
                'duration': 4,
                'average_rating': 4.7,
                'review_count': 12,
                'category_name': 'Security',
                'category_slug': 'security',
                'provider': {'user': {'get_full_name': 'Ajay Kumar', 'email': 'ajay@example.com'}},
                'image': None
            },
            {
                'id': 21,
                'name': 'Home Security System',
                'description': 'Complete home security system installation and monitoring.',
                'price': 12000,
                'duration': 6,
                'average_rating': 4.8,
                'review_count': 5,
                'category_name': 'Security',
                'category_slug': 'security',
                'provider': {'user': {'get_full_name': 'Vinay Gupta', 'email': 'vinay@example.com'}},
                'image': None
            },
            # Pest Control Services
            {
                'id': 22,
                'name': 'General Pest Control',
                'description': 'Comprehensive pest control treatment for your home.',
                'price': 2500,
                'duration': 2,
                'average_rating': 4.6,
                'review_count': 15,
                'category_name': 'Pest Control',
                'category_slug': 'pest-control',
                'provider': {'user': {'get_full_name': 'Vinod Gupta', 'email': 'vinod@example.com'}},
                'image': None
            },
            {
                'id': 23,
                'name': 'Termite Treatment',
                'description': 'Professional termite treatment and prevention services.',
                'price': 4500,
                'duration': 4,
                'average_rating': 4.7,
                'review_count': 8,
                'category_name': 'Pest Control',
                'category_slug': 'pest-control',
                'provider': {'user': {'get_full_name': 'Sunil Yadav', 'email': 'sunil@example.com'}},
                'image': None
            },
            # Handyman Services
            {
                'id': 24,
                'name': 'General Handyman',
                'description': 'General handyman services for various home repairs and maintenance.',
                'price': 1500,
                'duration': 2,
                'average_rating': 4.5,
                'review_count': 18,
                'category_name': 'Handyman',
                'category_slug': 'handyman',
                'provider': {'user': {'get_full_name': 'Ravi Mehta', 'email': 'ravi@example.com'}},
                'image': None
            },
            {
                'id': 25,
                'name': 'Wall Mount Installation',
                'description': 'Professional TV and appliance wall mounting services.',
                'price': 1200,
                'duration': 1,
                'average_rating': 4.6,
                'review_count': 22,
                'category_name': 'Handyman',
                'category_slug': 'handyman',
                'provider': {'user': {'get_full_name': 'Ashok Kumar', 'email': 'ashok@example.com'}},
                'image': None
            },
            # Moving & Packing Services
            {
                'id': 26,
                'name': 'Local Moving',
                'description': 'Professional local moving and relocation services.',
                'price': 5000,
                'duration': 6,
                'average_rating': 4.4,
                'review_count': 10,
                'category_name': 'Moving & Packing',
                'category_slug': 'moving-packing',
                'provider': {'user': {'get_full_name': 'Mohan Lal', 'email': 'mohan@example.com'}},
                'image': None
            },
            {
                'id': 27,
                'name': 'Packing Services',
                'description': 'Professional packing services for safe transportation.',
                'price': 2500,
                'duration': 4,
                'average_rating': 4.3,
                'review_count': 7,
                'category_name': 'Moving & Packing',
                'category_slug': 'moving-packing',
                'provider': {'user': {'get_full_name': 'Prakash Singh', 'email': 'prakash@example.com'}},
                'image': None
            }
        ]

class CategoriesView(View):
    def get(self, request):
        categories = [
            {
                'name': 'Electrical',
                'slug': 'electrical',
                'description': 'Professional electrical services for your home',
                'sample_services': [
                    {'name': 'Electrical Installation', 'price': 2500},
                    {'name': 'Lighting Repair', 'price': 1500},
                    {'name': 'Circuit Breaker Repair', 'price': 2000}
                ]
            },
            {
                'name': 'Plumbing',
                'slug': 'plumbing',
                'description': 'Professional plumbing services for your home',
                'sample_services': [
                    {'name': 'Pipe Repair', 'price': 1200},
                    {'name': 'Leak Detection', 'price': 1800},
                    {'name': 'Water Heater Repair', 'price': 2200}
                ]
            },
            {
                'name': 'Cleaning',
                'slug': 'cleaning',
                'description': 'Home cleaning and maintenance services',
                'sample_services': [
                    {'name': 'Deep Cleaning', 'price': 3500},
                    {'name': 'Carpet Cleaning', 'price': 1800},
                    {'name': 'Window Cleaning', 'price': 1000}
                ]
            },
            {
                'name': 'Carpentry',
                'slug': 'carpentry',
                'description': 'Wood work and furniture repair services',
                'sample_services': [
                    {'name': 'Furniture Repair', 'price': 1800},
                    {'name': 'Cabinet Installation', 'price': 4500},
                    {'name': 'Door Repair', 'price': 1200}
                ]
            },
            {
                'name': 'Painting',
                'slug': 'painting',
                'description': 'Interior and exterior painting services',
                'sample_services': [
                    {'name': 'Interior Painting', 'price': 3000},
                    {'name': 'Exterior Painting', 'price': 5500},
                    {'name': 'Touch-up Painting', 'price': 800}
                ]
            },
            {
                'name': 'Appliance Repair',
                'slug': 'appliance-repair',
                'description': 'Repair services for home appliances',
                'sample_services': [
                    {'name': 'AC Repair', 'price': 2500},
                    {'name': 'Washing Machine Repair', 'price': 1800},
                    {'name': 'Refrigerator Repair', 'price': 2200}
                ]
            },
            {
                'name': 'HVAC',
                'slug': 'hvac',
                'description': 'Heating, ventilation, and air conditioning services',
                'sample_services': [
                    {'name': 'AC Installation', 'price': 8000},
                    {'name': 'Duct Cleaning', 'price': 3500},
                    {'name': 'Heater Repair', 'price': 2800}
                ]
            },
            {
                'name': 'Landscaping',
                'slug': 'landscaping',
                'description': 'Garden and outdoor maintenance services',
                'sample_services': [
                    {'name': 'Garden Maintenance', 'price': 2000},
                    {'name': 'Lawn Mowing', 'price': 800},
                    {'name': 'Tree Trimming', 'price': 1500}
                ]
            },
            {
                'name': 'Security',
                'slug': 'security',
                'description': 'Home security system installation and maintenance',
                'sample_services': [
                    {'name': 'CCTV Installation', 'price': 5500},
                    {'name': 'Home Security System', 'price': 12000},
                    {'name': 'Lock Installation', 'price': 1200}
                ]
            },
            {
                'name': 'Pest Control',
                'slug': 'pest-control',
                'description': 'Professional pest control and extermination services',
                'sample_services': [
                    {'name': 'General Pest Control', 'price': 2500},
                    {'name': 'Termite Treatment', 'price': 4500},
                    {'name': 'Rodent Control', 'price': 1800}
                ]
            },
            {
                'name': 'Handyman',
                'slug': 'handyman',
                'description': 'General handyman services for various home repairs',
                'sample_services': [
                    {'name': 'General Handyman', 'price': 1500},
                    {'name': 'Wall Mount Installation', 'price': 1200},
                    {'name': 'Minor Repairs', 'price': 800}
                ]
            },
            {
                'name': 'Moving & Packing',
                'slug': 'moving-packing',
                'description': 'Professional moving and packing services',
                'sample_services': [
                    {'name': 'Local Moving', 'price': 5000},
                    {'name': 'Packing Services', 'price': 2500},
                    {'name': 'Long Distance Moving', 'price': 12000}
                ]
            }
        ]
        return render(request, 'services/categories.html', {'categories': categories})


class ServiceDetailView(View):
    def get(self, request, pk):
        # Get sample services data
        sample_services = self.get_sample_services()

        # Find the requested service
        service = None
        for s in sample_services:
            if s['id'] == int(pk):
                service = s
                break

        if not service:
            messages.error(request, 'Service not found.')
            return redirect('services:service_list')

        # Get related services from the same category
        related_services = [s for s in sample_services
                          if s['category_slug'] == service['category_slug'] and s['id'] != service['id']][:3]

        # Enhanced service details for the detail page
        service_details = {
            'id': service['id'],
            'name': service['name'],
            'description': service['description'],
            'price': service['price'],
            'duration': service['duration'],
            'average_rating': service['average_rating'],
            'review_count': service['review_count'],
            'category_name': service['category_name'],
            'category_slug': service['category_slug'],
            'provider_name': service['provider']['user']['get_full_name'],
            'provider_email': service['provider']['user']['email'],
            'image': service.get('image'),
            'features': [
                'Professional and experienced technician',
                'All tools and equipment included',
                'Quality guarantee on work performed',
                'Flexible scheduling available',
                'Clean-up after service completion'
            ],
            'what_included': [
                'Initial assessment and consultation',
                'Professional service execution',
                'Quality testing and verification',
                'Basic warranty on service',
                'Follow-up support if needed'
            ],
            'reviews': self.get_sample_reviews(service['id'])
        }

        context = {
            'service': service_details,
            'related_services': related_services,
            'has_booked': False,  # For sample data, assume not booked
            'can_book': request.user.is_authenticated,
        }

        return render(request, 'services/service_detail.html', context)

    def get_sample_reviews(self, service_id):
        """Return sample reviews for the service"""
        all_reviews = {
            1: [  # Electrical Installation
                {
                    'user_name': 'Priya Sharma',
                    'rating': 5,
                    'comment': 'Excellent work! Rajesh was very professional and completed the electrical installation perfectly. All outlets and switches are working great. Highly recommended!',
                    'date': '2024-01-15'
                },
                {
                    'user_name': 'Amit Patel',
                    'rating': 4,
                    'comment': 'Good service overall. The electrician arrived on time and did quality work. Only minor issue was some cleanup could have been better.',
                    'date': '2024-01-10'
                },
                {
                    'user_name': 'Sunita Gupta',
                    'rating': 5,
                    'comment': 'Outstanding service! Very knowledgeable and explained everything clearly. The electrical work was done safely and efficiently.',
                    'date': '2024-01-05'
                }
            ],
            2: [  # Lighting Repair
                {
                    'user_name': 'Ravi Kumar',
                    'rating': 5,
                    'comment': 'Amit fixed all our lighting issues quickly. Very professional and reasonably priced. Will definitely use again!',
                    'date': '2024-01-12'
                },
                {
                    'user_name': 'Meera Singh',
                    'rating': 4,
                    'comment': 'Good work on the lighting repair. The technician was punctual and completed the job efficiently.',
                    'date': '2024-01-08'
                }
            ],
            3: [  # Circuit Breaker Repair
                {
                    'user_name': 'Vikram Reddy',
                    'rating': 5,
                    'comment': 'Priya did an excellent job fixing our circuit breaker. Very knowledgeable about electrical safety. Highly recommend!',
                    'date': '2024-01-14'
                },
                {
                    'user_name': 'Kavita Joshi',
                    'rating': 4,
                    'comment': 'Professional service. The circuit breaker issue was resolved quickly and safely.',
                    'date': '2024-01-09'
                }
            ],
            4: [  # Pipe Repair
                {
                    'user_name': 'Deepak Agarwal',
                    'rating': 5,
                    'comment': 'Suresh did an amazing job fixing our pipe leak. Very clean work and no mess left behind. Excellent plumber!',
                    'date': '2024-01-13'
                },
                {
                    'user_name': 'Anita Sharma',
                    'rating': 4,
                    'comment': 'Good plumbing service. The pipe repair was done properly and the price was fair.',
                    'date': '2024-01-07'
                },
                {
                    'user_name': 'Rohit Gupta',
                    'rating': 5,
                    'comment': 'Very satisfied with the pipe repair work. Professional approach and quality materials used.',
                    'date': '2024-01-03'
                }
            ],
            5: [  # Leak Detection
                {
                    'user_name': 'Sanjay Patel',
                    'rating': 5,
                    'comment': 'Kavita found the hidden leak that other plumbers missed. Used advanced equipment and solved the problem perfectly!',
                    'date': '2024-01-11'
                },
                {
                    'user_name': 'Pooja Singh',
                    'rating': 5,
                    'comment': 'Excellent leak detection service. Very thorough and professional. Saved us from major water damage!',
                    'date': '2024-01-06'
                }
            ],
            6: [  # Water Heater Repair
                {
                    'user_name': 'Manoj Kumar',
                    'rating': 4,
                    'comment': 'Vikram repaired our water heater efficiently. Good service and reasonable pricing.',
                    'date': '2024-01-10'
                },
                {
                    'user_name': 'Rekha Jain',
                    'rating': 5,
                    'comment': 'Outstanding water heater repair service. Very knowledgeable technician and quality work.',
                    'date': '2024-01-04'
                }
            ],
            7: [  # Deep Cleaning
                {
                    'user_name': 'Neha Verma',
                    'rating': 5,
                    'comment': 'Sunita and her team did an incredible deep cleaning job! Our house looks brand new. Very thorough and professional.',
                    'date': '2024-01-12'
                },
                {
                    'user_name': 'Ajay Sharma',
                    'rating': 5,
                    'comment': 'Amazing deep cleaning service! Every corner was cleaned perfectly. Highly recommend for anyone needing thorough cleaning.',
                    'date': '2024-01-08'
                },
                {
                    'user_name': 'Priyanka Gupta',
                    'rating': 4,
                    'comment': 'Very good cleaning service. The team was professional and did quality work throughout the house.',
                    'date': '2024-01-02'
                }
            ],
            10: [  # Furniture Repair
                {
                    'user_name': 'Rajesh Agarwal',
                    'rating': 5,
                    'comment': 'Manoj did excellent furniture repair work. My old dining table looks like new! Very skilled craftsman.',
                    'date': '2024-01-14'
                },
                {
                    'user_name': 'Sita Devi',
                    'rating': 4,
                    'comment': 'Good furniture repair service. The work was done carefully and the price was reasonable.',
                    'date': '2024-01-09'
                }
            ],
            12: [  # Interior Painting
                {
                    'user_name': 'Kiran Joshi',
                    'rating': 5,
                    'comment': 'Deepak did amazing interior painting work! The finish is perfect and the colors look beautiful. Highly recommend!',
                    'date': '2024-01-13'
                },
                {
                    'user_name': 'Ramesh Kumar',
                    'rating': 4,
                    'comment': 'Professional painting service. Good quality work and clean finish. Satisfied with the results.',
                    'date': '2024-01-07'
                }
            ],
            14: [  # AC Repair
                {
                    'user_name': 'Sunil Sharma',
                    'rating': 5,
                    'comment': 'Rohit fixed our AC perfectly! Very knowledgeable about air conditioning systems. Quick and efficient service.',
                    'date': '2024-01-11'
                },
                {
                    'user_name': 'Geeta Patel',
                    'rating': 5,
                    'comment': 'Excellent AC repair service. The technician was professional and solved the problem quickly. AC is working great now!',
                    'date': '2024-01-06'
                },
                {
                    'user_name': 'Ashok Gupta',
                    'rating': 4,
                    'comment': 'Good AC repair work. The service was prompt and the pricing was fair.',
                    'date': '2024-01-01'
                }
            ],
            16: [  # AC Installation
                {
                    'user_name': 'Mohan Lal',
                    'rating': 5,
                    'comment': 'Ankit did professional AC installation. Very clean work and explained everything about maintenance. Excellent service!',
                    'date': '2024-01-10'
                },
                {
                    'user_name': 'Lakshmi Devi',
                    'rating': 4,
                    'comment': 'Good AC installation service. The technician was skilled and completed the work efficiently.',
                    'date': '2024-01-05'
                }
            ],
            20: [  # CCTV Installation
                {
                    'user_name': 'Vinod Kumar',
                    'rating': 5,
                    'comment': 'Ajay installed our CCTV system perfectly! Very professional setup and explained how to use the system. Great security solution!',
                    'date': '2024-01-12'
                },
                {
                    'user_name': 'Radha Sharma',
                    'rating': 4,
                    'comment': 'Professional CCTV installation. Good quality cameras and clean cable management.',
                    'date': '2024-01-08'
                }
            ]
        }

        # Return reviews for the specific service, or empty list if none
        return all_reviews.get(service_id, [])

    def get_sample_services(self):
        """Return the same comprehensive sample services as ServiceListView"""
        # Use the same method from ServiceListView to ensure consistency
        service_list_view = ServiceListView()
        return service_list_view.get_sample_services()


class ServiceCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'services/service_form.html'

    def form_valid(self, form):
        form.instance.provider = self.request.user.providerprofile
        messages.success(self.request, 'Service created successfully!')
        return super().form_valid(form)

    def test_func(self):
        return hasattr(self.request.user, 'providerprofile')


class ServiceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'services/service_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Service updated successfully!')
        return super().form_valid(form)

    def test_func(self):
        service = self.get_object()
        return self.request.user == service.provider.user


class ServiceDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Service
    template_name = 'services/service_confirm_delete.html'
    success_url = reverse_lazy('services:provider_service_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Service deleted successfully!')
        return super().delete(request, *args, **kwargs)

    def test_func(self):
        service = self.get_object()
        return self.request.user == service.provider.user


class ServiceBookingView(LoginRequiredMixin, TemplateView):
    template_name = 'services/service_booking_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get service from sample data
        service_id = int(self.kwargs['service_id'])
        service_list_view = ServiceListView()
        sample_services = service_list_view.get_sample_services()

        service = None
        for s in sample_services:
            if s['id'] == service_id:
                service = s
                break

        if not service:
            messages.error(self.request, 'Service not found.')
            return redirect('services:service_list')

        # Calculate minimum booking date (today)
        from django.utils import timezone
        min_booking_date = timezone.now().date().isoformat()

        context.update({
            'service': service,
            'addresses': [],  # For sample data, use empty addresses
            'min_booking_date': min_booking_date
        })
        return context

    def post(self, request, *args, **kwargs):
        # Get service from sample data
        service_id = int(self.kwargs['service_id'])
        service_list_view = ServiceListView()
        sample_services = service_list_view.get_sample_services()

        service = None
        for s in sample_services:
            if s['id'] == service_id:
                service = s
                break

        if not service:
            messages.error(request, 'Service not found.')
            return redirect('services:service_list')

        # Get form data
        booking_date = request.POST.get('booking_date')
        booking_time = request.POST.get('booking_time')
        address = request.POST.get('address', '')
        phone_number = request.POST.get('phone_number', '')
        notes = request.POST.get('notes', '')

        try:
            # SIMPLIFIED APPROACH: Create booking without complex database relationships
            from django.utils import timezone
            from datetime import datetime
            from decimal import Decimal
            from users.models import User

            print(f"DEBUG: Starting simplified booking creation for service: {service['name']}")

            # Combine date and time
            booking_datetime = datetime.strptime(f"{booking_date} {booking_time}", "%Y-%m-%d %H:%M")
            booking_datetime = timezone.make_aware(booking_datetime)

            # Get or create a provider user for the booking
            provider_user, created = User.objects.get_or_create(
                email=service['provider']['user']['email'],
                defaults={
                    'first_name': service['provider']['user']['get_full_name'].split()[0],
                    'last_name': ' '.join(service['provider']['user']['get_full_name'].split()[1:]),
                    'user_type': 'provider',
                    'is_active': True
                }
            )
            print(f"DEBUG: Provider user: {provider_user.email} (created: {created})")

            # Ensure we have a service to use (create a default one if needed)
            existing_service = Service.objects.first()
            if existing_service:
                print(f"DEBUG: Using existing service: {existing_service.name}")
                db_service = existing_service
            else:
                # Create a minimal default service for bookings
                print("DEBUG: No existing services found, creating a default service")

                # Get or create a default category first
                from .models import ServiceCategory
                default_category = ServiceCategory.objects.first()
                if not default_category:
                    # Create a basic category using raw MongoDB if needed
                    try:
                        default_category = ServiceCategory.objects.create(
                            name='General Services',
                            slug='general',
                            description='General home services'
                        )
                    except Exception as cat_err:
                        print(f"DEBUG: Could not create category: {cat_err}")
                        # Use direct MongoDB insertion as last resort
                        import pymongo
                        from django.conf import settings
                        client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'])
                        db = client[settings.DATABASES['default']['NAME']]
                        cat_result = db['services_servicecategory'].insert_one({
                            'name': 'General Services',
                            'slug': 'general',
                            'description': 'General home services'
                        })
                        # Refresh to get the created category
                        default_category = ServiceCategory.objects.first()

                if default_category:
                    try:
                        db_service = Service.objects.create(
                            name='Default Home Service',
                            category=default_category,
                            provider=provider_user,
                            description='Default service for bookings',
                            price=Decimal('1000.00'),
                            duration=2,
                            is_active=True,
                            is_available=True
                        )
                        print(f"DEBUG: Created default service: {db_service.name}")
                    except Exception as svc_err:
                        print(f"DEBUG: Could not create default service: {svc_err}")
                        # Use the current user as both customer and provider for a minimal booking
                        db_service = None
                else:
                    db_service = None

            # Ensure price is a proper Decimal
            try:
                booking_amount = Decimal(str(service['price']))
            except (ValueError, TypeError):
                booking_amount = Decimal('0.00')

            # SINGLE PATH: Create booking directly in MongoDB to prevent duplicates
            print("DEBUG: Creating booking directly in MongoDB (single path)")
            import pymongo
            from django.conf import settings
            from bson import ObjectId

            client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'])
            db = client[settings.DATABASES['default']['NAME']]

            booking_data = {
                'customer_id': request.user.id,
                'provider_id': provider_user.id,
                'service_id': None,  # We'll handle this in the payment page
                'status': 'pending',
                'booking_date': booking_datetime,
                'address': address,
                'phone_number': phone_number,
                'total_amount': float(booking_amount),
                'payment_status': 'pending',
                'is_paid': False,
                'special_instructions': notes,
                'notes': f"Booking for {service['name']} - Provider: {service['provider']['user']['get_full_name']}",
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }

            result = db['services_booking'].insert_one(booking_data)
            booking_id = str(result.inserted_id)
            print(f"DEBUG: Created booking directly in MongoDB: {booking_id}")

            # Create a mock booking object for the redirect
            class MockBooking:
                def __init__(self, booking_id):
                    self.id = booking_id

            booking = MockBooking(booking_id)

            print(f"DEBUG: Booking created successfully: {booking.id}")
            messages.success(request, f'Booking created successfully! Please proceed to payment to confirm your booking.')

            # Redirect to payment page
            return redirect('services:payment', booking_id=booking.id)

        except Exception as e:
            # Enhanced error handling with more details
            print(f"Booking creation error: {e}")  # For debugging
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")

            messages.error(request, f'Unable to create booking at this time. Please try again later.')
            return redirect('services:service_list')




class BookingCreateView(LoginRequiredMixin, CreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'services/booking_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        service = get_object_or_404(Service, id=self.kwargs['service_id'])
        kwargs['service'] = service
        return kwargs

    def form_valid(self, form):
        service = get_object_or_404(Service, id=self.kwargs['service_id'])
        form.instance.user = self.request.user
        form.instance.service = service
        form.instance.status = 'pending'
        messages.success(self.request, 'Booking request sent successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('services:booking_detail', kwargs={'pk': self.object.id})


class BookingDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'services/booking_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking_id = kwargs.get('pk')

        # Handle MongoDB ObjectId issues - similar to PaymentView
        booking = None

        # First try: direct MongoDB query if booking_id looks like ObjectId
        if booking_id and len(str(booking_id)) == 24:
            try:
                import pymongo
                from django.conf import settings
                from bson import ObjectId

                client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'])
                db = client[settings.DATABASES['default']['NAME']]

                # Query MongoDB directly
                booking_data = db['services_booking'].find_one({
                    '_id': ObjectId(booking_id),
                    'customer_id': self.request.user.id
                })

                if booking_data:
                    # Create a mock booking object with all necessary attributes
                    class MockBooking:
                        def __init__(self, data, user):
                            self.id = str(data['_id'])
                            self.customer = user
                            self.provider_id = data.get('provider_id')
                            self.booking_date = data.get('booking_date')
                            self.address = data.get('address', '')
                            self.phone_number = data.get('phone_number', '')
                            self.total_amount = data.get('total_amount', 0)
                            self.notes = data.get('notes', '')
                            self.special_instructions = data.get('special_instructions', '')
                            self.status = data.get('status', 'pending')
                            self.payment_status = data.get('payment_status', 'pending')
                            self.is_paid = data.get('is_paid', False)
                            self.payment_method = data.get('payment_method', '')
                            self.transaction_id = data.get('transaction_id', '')
                            self.created_at = data.get('created_at')
                            self.updated_at = data.get('updated_at')
                            self.rejection_reason = data.get('rejection_reason', '')
                            self.rejected_at = data.get('rejected_at')
                            self.admin_notes = data.get('admin_notes', '')

                            # Additional fields that might be accessed by template
                            self.confirmed_at = data.get('confirmed_at')
                            self.started_at = data.get('started_at')
                            self.completed_at = data.get('completed_at')
                            self.paid_at = data.get('paid_at')
                            self.cancellation_reason = data.get('cancellation_reason', '')
                            self.cancellation_policy = data.get('cancellation_policy', '')
                            self.additional_charges = data.get('additional_charges', 0)
                            self.discount_amount = data.get('discount_amount', 0)

                            # Address fields
                            self.address_line1 = data.get('address', '')
                            self.address_line2 = data.get('address_line2', '')
                            self.city = data.get('city', '')
                            self.state = data.get('state', '')
                            self.postal_code = data.get('postal_code', '')
                            self.country = data.get('country', 'IN')

                            # Mock review (always None for now)
                            self.review = None

                            # Get provider info
                            try:
                                from users.models import User
                                self.provider = User.objects.get(id=data.get('provider_id'))
                            except:
                                self.provider = None

                            # Mock service object from notes
                            self.service = self.create_mock_service(data.get('notes', ''))

                        def create_mock_service(self, notes):
                            """Create a mock service object from booking notes"""
                            class MockService:
                                def __init__(self, notes, provider):
                                    # Parse service name from notes
                                    if ' - Provider: ' in notes:
                                        service_part = notes.split(' - Provider: ')[0]
                                        if service_part.startswith('Booking for '):
                                            self.name = service_part.replace('Booking for ', '')
                                        else:
                                            self.name = service_part
                                    else:
                                        self.name = 'Home Service'

                                    self.provider = provider
                                    self.price = 1800  # Default price
                                    self.duration = 2  # Default duration
                                    self.description = f"Professional {self.name.lower()} service"

                                    # Mock category
                                    class MockCategory:
                                        def __init__(self):
                                            self.name = 'Home Services'

                                    self.category = MockCategory()
                                    self.image = None
                                    self.service_area = 'Local Area'

                            return MockService(notes, self.provider)

                        def get_status_display(self):
                            status_map = {
                                'pending': 'Pending',
                                'confirmed': 'Confirmed',
                                'rejected': 'Rejected',
                                'completed': 'Completed',
                                'cancelled': 'Cancelled'
                            }
                            return status_map.get(self.status, self.status.title())

                        def get_payment_status_display(self):
                            status_map = {
                                'pending': 'Pending',
                                'paid': 'Paid',
                                'failed': 'Failed'
                            }
                            return status_map.get(self.payment_status, self.payment_status.title())

                        def get(self, key, default=None):
                            """Allow template to access data using get method"""
                            return getattr(self, key, default)

                        def get_country_display(self):
                            """Return country display name"""
                            country_map = {
                                'IN': 'India',
                                'US': 'United States',
                                'UK': 'United Kingdom'
                            }
                            return country_map.get(self.country, self.country)

                        def get_payment_method_display(self):
                            """Return payment method display name"""
                            method_map = {
                                'card': 'Credit/Debit Card',
                                'upi': 'UPI',
                                'netbanking': 'Net Banking',
                                'wallet': 'Digital Wallet'
                            }
                            return method_map.get(self.payment_method, self.payment_method.title())



                    booking = MockBooking(booking_data, self.request.user)
                    print(f"DEBUG: Found booking via MongoDB for detail view: {booking.id}")

            except Exception as mongo_error:
                print(f"DEBUG: MongoDB detail query failed: {mongo_error}")

        # Second try: Django ORM
        if not booking:
            try:
                from django.shortcuts import get_object_or_404
                booking = get_object_or_404(Booking, id=booking_id, customer=self.request.user)
                print(f"DEBUG: Found booking via Django ORM for detail view: {booking.id}")
            except Exception as orm_error:
                print(f"DEBUG: Django ORM detail query failed: {orm_error}")

        if not booking:
            from django.http import Http404
            raise Http404("Booking not found")

        context['booking'] = booking

        # Add review form if the booking is completed and the user is the one who booked
        if booking.status == 'completed' and self.request.user == booking.customer:
            if not hasattr(booking, 'review'):
                from .forms import ReviewForm
                context['review_form'] = ReviewForm()

        return context


class BookingListView(LoginRequiredMixin, TemplateView):
    template_name = 'services/booking_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ONLY use MongoDB bookings to prevent corrupted Django ORM booking issues
        mongodb_bookings = self.get_mongodb_bookings()

        # Create mock booking objects for MongoDB bookings
        all_bookings = []

        # Add MongoDB bookings as mock objects
        for booking_data in mongodb_bookings:
            mock_booking = self.create_mock_booking(booking_data)
            all_bookings.append(mock_booking)

        # Sort by creation date (newest first) - handle timezone issues
        def get_sort_date(booking):
            """Get a comparable date for sorting, handling timezone issues"""
            from django.utils import timezone
            from datetime import datetime

            created_at = getattr(booking, 'created_at', None)
            updated_at = getattr(booking, 'updated_at', None)

            # Use created_at if available, otherwise updated_at
            sort_date = created_at or updated_at

            if sort_date is None:
                # Return a very old date for bookings without timestamps
                return timezone.make_aware(datetime(2000, 1, 1))

            # If it's already timezone-aware, return as is
            if hasattr(sort_date, 'tzinfo') and sort_date.tzinfo is not None:
                return sort_date

            # If it's naive, make it timezone-aware
            if isinstance(sort_date, datetime):
                return timezone.make_aware(sort_date)

            # Fallback for other types
            return timezone.make_aware(datetime(2000, 1, 1))

        all_bookings.sort(key=get_sort_date, reverse=True)

        # Filter bookings by status for each tab (ensure no duplicates)
        context['pending_bookings'] = [b for b in all_bookings if b.status == 'pending']
        context['confirmed_bookings'] = [b for b in all_bookings if b.status == 'confirmed']
        context['completed_bookings'] = [b for b in all_bookings if b.status == 'completed']
        context['rejected_bookings'] = [b for b in all_bookings if b.status == 'rejected']
        context['cancelled_bookings'] = [b for b in all_bookings if b.status == 'cancelled']

        # Upcoming = pending + confirmed (but not completed/cancelled/rejected)
        context['upcoming_bookings'] = context['pending_bookings'] + context['confirmed_bookings']

        # Add status filter for URL
        context['status'] = self.request.GET.get('status', 'upcoming')

        # Add total bookings count
        context['total_bookings'] = len(all_bookings)

        return context

    def get_mongodb_bookings(self):
        """Get bookings from MongoDB"""
        try:
            import pymongo
            from django.conf import settings

            client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'])
            db = client[settings.DATABASES['default']['NAME']]

            # Get all bookings for this user
            bookings = list(db['services_booking'].find({
                'customer_id': self.request.user.id
            }).sort('created_at', -1))

            print(f"DEBUG: Found {len(bookings)} MongoDB bookings for user {self.request.user.email}")
            return bookings

        except Exception as e:
            print(f"DEBUG: Error getting MongoDB bookings: {e}")
            return []

    def create_mock_booking(self, booking_data):
        """Create a mock booking object from MongoDB data"""
        class MockBooking:
            def __init__(self, data, user):
                self.id = str(data['_id'])
                self.customer = user
                self.provider_id = data.get('provider_id')
                self.booking_date = data.get('booking_date')
                self.address = data.get('address', '')
                self.phone_number = data.get('phone_number', '')
                self.total_amount = data.get('total_amount', 0)
                self.notes = data.get('notes', '')
                self.special_instructions = data.get('special_instructions', '')
                self.status = data.get('status', 'pending')
                self.payment_status = data.get('payment_status', 'pending')
                self.is_paid = data.get('is_paid', False)
                self.rejection_reason = data.get('rejection_reason', '')
                self.created_at = data.get('created_at')
                self.updated_at = data.get('updated_at')

                # Get provider info
                try:
                    from users.models import User
                    self.provider = User.objects.get(id=data.get('provider_id'))
                except:
                    self.provider = None

                # Create mock service object
                self.service = self.create_mock_service(data.get('notes', ''))

                # Mock review (always None for now)
                self.review = None

            def create_mock_service(self, notes):
                """Create a mock service object from booking notes"""
                class MockService:
                    def __init__(self, notes, provider):
                        # Parse service name from notes
                        if ' - Provider: ' in notes:
                            service_part = notes.split(' - Provider: ')[0]
                            if service_part.startswith('Booking for '):
                                self.name = service_part.replace('Booking for ', '')
                            else:
                                self.name = service_part
                        else:
                            self.name = 'Home Service'

                        self.provider = provider
                        self.price = 1800  # Default price
                        self.image = None

                        # Mock category
                        class MockCategory:
                            def __init__(self):
                                self.name = 'Home Services'

                        self.category = MockCategory()

                return MockService(notes, self.provider)

            def get_status_display(self):
                status_map = {
                    'pending': 'Pending',
                    'confirmed': 'Confirmed',
                    'rejected': 'Rejected',
                    'completed': 'Completed',
                    'cancelled': 'Cancelled'
                }
                return status_map.get(self.status, self.status.title())



        return MockBooking(booking_data, self.request.user)


class ProviderDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'services/provider_dashboard.html'

    def test_func(self):
        return hasattr(self.request.user, 'providerprofile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        provider = self.request.user.providerprofile

        # Get provider's services
        context['services'] = Service.objects.filter(provider=provider)[:5]

        # Get recent bookings
        context['recent_bookings'] = Booking.objects.filter(
            service__provider=provider
        ).order_by('-created_at')[:5]

        # Get upcoming bookings
        context['upcoming_bookings'] = Booking.objects.filter(
            service__provider=provider,
            booking_date__gte=timezone.now(),
            status__in=['confirmed', 'pending']
        ).order_by('booking_date')[:5]

        # Stats
        context['total_services'] = Service.objects.filter(provider=provider).count()
        context['total_bookings'] = Booking.objects.filter(service__provider=provider).count()
        context['pending_bookings'] = Booking.objects.filter(
            service__provider=provider,
            status='pending'
        ).count()
        context['completed_bookings'] = Booking.objects.filter(
            service__provider=provider,
            status='completed'
        ).count()

        return context


def add_review(request, booking_id):
    # Handle both MongoDB ObjectId and Django integer IDs
    try:
        # Try MongoDB first
        import pymongo
        from bson import ObjectId
        from django.conf import settings

        client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'])
        db = client[settings.DATABASES['default']['NAME']]

        # Convert booking_id to ObjectId if it's a MongoDB ID
        if len(booking_id) == 24:  # MongoDB ObjectId length
            booking_doc = db['services_booking'].find_one({'_id': ObjectId(booking_id)})
            if booking_doc:
                # Check if the user is the one who booked and the booking is completed
                if request.user.id != booking_doc.get('customer_id') or booking_doc.get('status') != 'completed':
                    messages.error(request, 'You are not allowed to review this booking.')
                    return redirect('services:booking_list')

                # Handle MongoDB booking reviews
                if request.method == 'POST':
                    # Process review submission for MongoDB booking
                    rating = request.POST.get('rating')
                    comment = request.POST.get('comment', '')

                    if rating:
                        try:
                            from datetime import datetime

                            # Create clean review document for MongoDB (no Django ORM fields)
                            review_doc = {
                                'booking_id': ObjectId(booking_id),
                                'customer_id': request.user.id,
                                'customer_name': request.user.get_full_name() or request.user.username,
                                'customer_email': request.user.email,
                                'rating': int(rating),
                                'comment': comment.strip(),
                                'service_name': booking_doc.get('notes', 'Home Service'),
                                'created_at': datetime.now(),
                                'updated_at': datetime.now()
                            }

                            # Insert review into MongoDB collection
                            result = db['services_review'].insert_one(review_doc)

                            if result.inserted_id:
                                print(f"Review successfully saved with ID: {result.inserted_id}")

                            messages.success(request, 'Thank you for your review!')
                            return redirect('services:booking_list')

                        except Exception as review_error:
                            print(f"Error saving review: {review_error}")
                            import traceback
                            traceback.print_exc()
                            messages.error(request, f'Error saving review: {str(review_error)}. Please try again.')
                    else:
                        messages.error(request, 'Please provide a rating.')

                # Create mock booking object for template
                from datetime import datetime
                from django.contrib.auth import get_user_model
                User = get_user_model()
                customer = User.objects.get(id=booking_doc['customer_id'])

                class MockBookingForReview:
                    def __init__(self, doc, customer_obj):
                        self.id = str(doc['_id'])
                        self.customer = customer_obj
                        self.booking_date = doc.get('booking_date')
                        self.total_amount = doc.get('total_amount', 0)
                        self.status = doc.get('status', 'pending')
                        self.notes = doc.get('notes', 'Service Booking')

                        # Mock service object
                        service_name = doc.get('notes', 'Home Service')
                        if 'plumbing' in service_name.lower():
                            service_name = 'Plumbing Service'
                        elif 'electrical' in service_name.lower():
                            service_name = 'Electrical Service'
                        elif 'cleaning' in service_name.lower():
                            service_name = 'Cleaning Service'

                        self.service = type('MockService', (), {
                            'name': service_name,
                            'price': doc.get('total_amount', 0),
                            'image': None
                        })()

                mock_booking = MockBookingForReview(booking_doc, customer)

                # Check if review already exists
                existing_review = db['services_review'].find_one({
                    'booking_id': ObjectId(booking_id),
                    'customer_id': request.user.id
                })

                if existing_review:
                    messages.info(request, 'You have already reviewed this booking.')
                    return redirect('services:booking_list')

                # Render review form
                return render(request, 'services/add_review_mongodb.html', {
                    'booking': mock_booking,
                    'booking_id': booking_id
                })

        # Fallback to Django ORM for integer IDs
        booking = get_object_or_404(Booking, id=int(booking_id))

        # Check if the user is the one who booked and the booking is completed
        if request.user != booking.user or booking.status != 'completed':
            messages.error(request, 'You are not allowed to review this booking.')
            return redirect('services:booking_detail', pk=booking_id)

    except (ValueError, TypeError, Exception):
        # If conversion fails, try Django ORM
        try:
            booking = get_object_or_404(Booking, id=int(booking_id))

            # Check if the user is the one who booked and the booking is completed
            if request.user != booking.user or booking.status != 'completed':
                messages.error(request, 'You are not allowed to review this booking.')
                return redirect('services:booking_detail', pk=booking_id)
        except:
            messages.error(request, 'Booking not found.')
            return redirect('services:booking_list')

    # Check if review already exists
    if hasattr(booking, 'review'):
        messages.warning(request, 'You have already reviewed this booking.')
        return redirect('services:booking_detail', pk=booking_id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.service = booking.service
            review.user = request.user
            review.save()
            messages.success(request, 'Thank you for your review!')
            return redirect('services:booking_detail', pk=booking_id)
    else:
        form = ReviewForm()

    return render(request, 'services/add_review.html', {'form': form, 'booking': booking})

# Booking Update and Cancel Views with MongoDB ObjectId support
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

@method_decorator(csrf_exempt, name='dispatch')
class BookingUpdateView(LoginRequiredMixin, View):
    """Update booking details like date, time, and special instructions"""

    def post(self, request):
        try:
            data = json.loads(request.body)
            booking_index = data.get('booking_index')
            new_date = data.get('booking_date')
            new_time = data.get('booking_time')
            special_instructions = data.get('special_instructions', '')

            # Get user's bookings
            user_bookings = list(Booking.objects.filter(customer=request.user))

            if 0 <= booking_index < len(user_bookings):
                booking = user_bookings[booking_index]

                # Handle MongoDB Decimal128 and other decimal types
                from decimal import Decimal, InvalidOperation
                if hasattr(booking, 'total_amount') and booking.total_amount is not None:
                    try:
                        # Handle MongoDB Decimal128 and other decimal types
                        if hasattr(booking.total_amount, 'to_decimal'):
                            # MongoDB Decimal128 has to_decimal() method
                            booking.total_amount = booking.total_amount.to_decimal()
                        elif not isinstance(booking.total_amount, Decimal):
                            # Convert other types to Decimal
                            amount_str = str(booking.total_amount)
                            booking.total_amount = Decimal(amount_str)
                    except (InvalidOperation, ValueError, TypeError, AttributeError):
                        # If conversion fails, set a default value
                        booking.total_amount = Decimal('0.00')

                # Update booking details
                if new_date and new_time:
                    from datetime import datetime
                    booking_datetime = datetime.strptime(f"{new_date} {new_time}", "%Y-%m-%d %H:%M")
                    booking.booking_date = timezone.make_aware(booking_datetime)

                if special_instructions:
                    booking.special_instructions = special_instructions

                # Use regular save()
                booking.save()

                return JsonResponse({
                    'success': True,
                    'message': 'Booking updated successfully!',
                    'booking_date': booking.booking_date.strftime('%Y-%m-%d %H:%M')
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Booking not found.'
                })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error updating booking: {str(e)}'
            })

@method_decorator(csrf_exempt, name='dispatch')
class BookingCancelView(LoginRequiredMixin, View):
    """Cancel booking by index since MongoDB ObjectIds are None"""

    def post(self, request):
        try:
            data = json.loads(request.body)
            booking_index = data.get('booking_index')
            cancellation_reason = data.get('cancellation_reason', 'User requested cancellation')

            # Get user's bookings
            user_bookings = list(Booking.objects.filter(customer=request.user))

            if 0 <= booking_index < len(user_bookings):
                booking = user_bookings[booking_index]

                # Handle MongoDB Decimal128 and other decimal types
                from decimal import Decimal, InvalidOperation
                if hasattr(booking, 'total_amount') and booking.total_amount is not None:
                    try:
                        # Handle MongoDB Decimal128 and other decimal types
                        if hasattr(booking.total_amount, 'to_decimal'):
                            # MongoDB Decimal128 has to_decimal() method
                            booking.total_amount = booking.total_amount.to_decimal()
                        elif not isinstance(booking.total_amount, Decimal):
                            # Convert other types to Decimal
                            amount_str = str(booking.total_amount)
                            booking.total_amount = Decimal(amount_str)
                    except (InvalidOperation, ValueError, TypeError, AttributeError):
                        # If conversion fails, set a default value
                        booking.total_amount = Decimal('0.00')

                if booking.status in ['pending', 'confirmed']:
                    booking.status = 'cancelled'
                    if hasattr(booking, 'cancellation_reason'):
                        booking.cancellation_reason = cancellation_reason
                    if hasattr(booking, 'cancellation_date'):
                        booking.cancellation_date = timezone.now()

                    # Use regular save()
                    booking.save()

                    return JsonResponse({
                        'success': True,
                        'message': 'Booking cancelled successfully!'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': 'This booking cannot be cancelled.'
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Booking not found.'
                })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error cancelling booking: {str(e)}'
            })

# MongoDB-compatible booking cancel view
class BookingCancelViewOriginal(LoginRequiredMixin, View):
    """Cancel booking - handles both MongoDB and Django ORM bookings"""
    template_name = 'services/booking_cancel_confirm.html'
    success_url = reverse_lazy('services:booking_list')
    success_message = "Booking has been cancelled successfully."

    def get(self, request, pk):
        """Show cancellation confirmation page"""
        try:
            # Try to get booking data for display
            booking_data = self.get_booking_data(pk, request.user)
            if not booking_data:
                messages.error(request, 'Booking not found.')
                return redirect('services:booking_list')

            return render(request, self.template_name, {
                'booking': booking_data,
                'booking_id': pk
            })

        except Exception as e:
            messages.error(request, f'Error loading booking: {str(e)}')
            return redirect('services:booking_list')

    def post(self, request, pk):
        """Process booking cancellation"""
        try:
            cancellation_reason = request.POST.get('cancellation_reason', 'User requested cancellation')

            # Try MongoDB first
            if self.cancel_mongodb_booking(pk, request.user, cancellation_reason):
                messages.success(request, self.success_message)
                return redirect('services:booking_list')

            # Fallback to Django ORM
            if self.cancel_django_booking(pk, request.user, cancellation_reason):
                messages.success(request, self.success_message)
                return redirect('services:booking_list')

            messages.error(request, 'Booking not found or cannot be cancelled.')
            return redirect('services:booking_list')

        except Exception as e:
            messages.error(request, f'Error cancelling booking: {str(e)}')
            return redirect('services:booking_list')

    def get_booking_data(self, booking_id, user):
        """Get booking data from MongoDB or Django ORM"""
        try:
            # Try MongoDB first
            import pymongo
            from django.conf import settings
            from bson import ObjectId

            client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'])
            db = client[settings.DATABASES['default']['NAME']]

            booking_doc = db['services_booking'].find_one({
                '_id': ObjectId(booking_id),
                'customer_id': user.id
            })

            if booking_doc:
                # Create a mock booking object for template compatibility
                class MockBooking:
                    def __init__(self, data):
                        self.id = str(data['_id'])
                        self.status = data.get('status', 'pending')
                        self.total_amount = data.get('total_amount', 0)
                        self.booking_date = data.get('booking_date')
                        self.address = data.get('address', '')

                        # Get service info
                        service_doc = db['services_service'].find_one({'_id': data.get('service_id')})
                        self.service_name = service_doc.get('name', 'Unknown Service') if service_doc else 'Unknown Service'

                return MockBooking(booking_doc)

            # Fallback to Django ORM
            try:
                booking = Booking.objects.get(id=booking_id, customer=user)
                return booking
            except (Booking.DoesNotExist, ValueError):
                return None

        except Exception as e:
            print(f"Error getting booking data: {e}")
            return None

    def cancel_mongodb_booking(self, booking_id, user, cancellation_reason):
        """Cancel MongoDB booking"""
        try:
            import pymongo
            from django.conf import settings
            from bson import ObjectId
            from datetime import datetime

            client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'])
            db = client[settings.DATABASES['default']['NAME']]

            # Update booking status in MongoDB
            result = db['services_booking'].update_one(
                {
                    '_id': ObjectId(booking_id),
                    'customer_id': user.id,
                    'status': {'$in': ['pending', 'confirmed']}
                },
                {
                    '$set': {
                        'status': 'cancelled',
                        'cancellation_reason': cancellation_reason,
                        'cancellation_date': datetime.now(),
                        'updated_at': datetime.now()
                    }
                }
            )

            return result.modified_count > 0

        except Exception as e:
            print(f"Error cancelling MongoDB booking: {e}")
            return False

    def cancel_django_booking(self, booking_id, user, cancellation_reason):
        """Cancel Django ORM booking"""
        try:
            booking = Booking.objects.get(id=booking_id, customer=user)

            if booking.status in ['pending', 'confirmed']:
                booking.status = 'cancelled'
                booking.cancellation_reason = cancellation_reason
                booking.cancellation_date = timezone.now()
                booking.save()
                return True

            return False

        except (Booking.DoesNotExist, ValueError):
            return False


class BookingRescheduleView(LoginRequiredMixin, TemplateView):
    template_name = 'services/booking_reschedule.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking_id = kwargs.get('pk')

        # Get booking (MongoDB or Django ORM)
        booking = self.get_booking(booking_id)
        if not booking:
            from django.http import Http404
            raise Http404("Booking not found")

        context['booking'] = booking
        context['booking_id'] = booking_id

        # Add form for reschedule
        from .forms import RescheduleBookingForm
        if self.request.method == 'GET':
            # Pre-populate with current booking date if available
            initial_data = {}
            if hasattr(booking, 'booking_date') and booking.booking_date:
                initial_data['booking_date'] = booking.booking_date
            elif hasattr(booking, 'get') and booking.get('booking_date'):
                initial_data['booking_date'] = booking.get('booking_date')

            context['form'] = RescheduleBookingForm(initial=initial_data)

        return context

    def get_booking(self, booking_id):
        """Get booking from MongoDB or Django ORM"""
        # Try MongoDB first
        if booking_id and len(str(booking_id)) == 24:
            try:
                import pymongo
                from django.conf import settings
                from bson import ObjectId

                client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'])
                db = client[settings.DATABASES['default']['NAME']]

                booking_data = db['services_booking'].find_one({
                    '_id': ObjectId(booking_id),
                    'customer_id': self.request.user.id
                })

                if booking_data:
                    # Create a booking-like object for template compatibility
                    class MongoBooking:
                        def __init__(self, data):
                            self.id = str(data['_id'])
                            self.booking_date = data.get('booking_date')
                            self.status = data.get('status', 'pending')
                            self.customer_id = data.get('customer_id')
                            self.service_id = data.get('service_id')
                            self.provider_id = data.get('provider_id')
                            self.total_amount = data.get('total_amount', 0)
                            self.address = data.get('address', '')
                            self.phone_number = data.get('phone_number', '')
                            self.special_instructions = data.get('special_instructions', '')
                            self.notes = data.get('notes', '')
                            self.rejection_reason = data.get('rejection_reason', '')
                            self.rejected_at = data.get('rejected_at')
                            self.admin_notes = data.get('admin_notes', '')
                            self._data = data

                            # Create a mock service object to prevent template errors
                            self.service = None
                            if self.service_id:
                                try:
                                    # Try to get service from Django ORM
                                    from .models import Service
                                    self.service = Service.objects.get(id=self.service_id)
                                except:
                                    # Create a mock service object
                                    class MockService:
                                        def __init__(self, service_id):
                                            self.id = service_id
                                            self.name = "Service"
                                            self.price = 0
                                            self.duration = 1
                                    self.service = MockService(self.service_id)

                        def get(self, key, default=None):
                            return self._data.get(key, default)

                        def get_status_display(self):
                            status_map = {
                                'pending': 'Pending',
                                'confirmed': 'Confirmed',
                                'in_progress': 'In Progress',
                                'completed': 'Completed',
                                'cancelled': 'Cancelled',
                                'rejected': 'Rejected'
                            }
                            return status_map.get(self.status, self.status.title())

                    return MongoBooking(booking_data)
            except Exception as e:
                print(f"MongoDB booking fetch error: {e}")

        # Try Django ORM
        try:
            return get_object_or_404(Booking, id=booking_id, customer=self.request.user)
        except:
            return None

    def post(self, request, *args, **kwargs):
        """Handle reschedule form submission"""
        booking_id = kwargs.get('pk')
        booking = self.get_booking(booking_id)

        if not booking:
            messages.error(request, 'Booking not found.')
            return redirect('services:booking_list')

        # Check if user owns this booking
        if hasattr(booking, 'customer') and booking.customer != request.user:
            messages.error(request, 'You do not have permission to reschedule this booking.')
            return redirect('services:booking_list')
        elif hasattr(booking, 'customer_id') and booking.customer_id != request.user.id:
            messages.error(request, 'You do not have permission to reschedule this booking.')
            return redirect('services:booking_list')

        from .forms import RescheduleBookingForm
        form = RescheduleBookingForm(request.POST)

        if form.is_valid():
            new_booking_date = form.cleaned_data['booking_date']

            # Update booking in appropriate database
            if hasattr(booking, '_data'):  # MongoDB booking
                success = self.update_mongodb_booking(booking_id, new_booking_date)
            else:  # Django ORM booking
                success = self.update_django_booking(booking, new_booking_date)

            if success:
                messages.success(request, 'Booking rescheduled successfully! Your new booking date has been updated.')
                return redirect('services:booking_detail', pk=booking_id)
            else:
                messages.error(request, 'Failed to reschedule booking. Please try again.')

        # If form is invalid, re-render with errors
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)

    def update_mongodb_booking(self, booking_id, new_booking_date):
        """Update booking date in MongoDB"""
        try:
            import pymongo
            from django.conf import settings
            from bson import ObjectId

            client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'])
            db = client[settings.DATABASES['default']['NAME']]

            result = db['services_booking'].update_one(
                {'_id': ObjectId(booking_id)},
                {'$set': {'booking_date': new_booking_date}}
            )

            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating MongoDB booking: {e}")
            return False

    def update_django_booking(self, booking, new_booking_date):
        """Update booking date in Django ORM"""
        try:
            booking.booking_date = new_booking_date
            booking.save()
            return True
        except Exception as e:
            print(f"Error updating Django booking: {e}")
            return False


# Payment Views
class PaymentView(LoginRequiredMixin, TemplateView):
    template_name = 'services/payment.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking_id = kwargs.get('booking_id')

        try:
            # Handle MongoDB ObjectId issues - try different approaches
            booking = None

            # First try: direct MongoDB query if booking_id looks like ObjectId
            if booking_id and len(booking_id) == 24:
                try:
                    import pymongo
                    from django.conf import settings
                    from bson import ObjectId

                    client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'])
                    db = client[settings.DATABASES['default']['NAME']]

                    # Query MongoDB directly
                    booking_data = db['services_booking'].find_one({
                        '_id': ObjectId(booking_id),
                        'customer_id': self.request.user.id
                    })

                    if booking_data:
                        # Create a mock booking object with the data
                        class MockBooking:
                            def __init__(self, data, user):
                                self.id = str(data['_id'])
                                self.customer = user
                                self.provider_id = data.get('provider_id')
                                self.booking_date = data.get('booking_date')
                                self.address = data.get('address', '')
                                self.phone_number = data.get('phone_number', '')
                                self.total_amount = data.get('total_amount', 0)
                                self.notes = data.get('notes', '')
                                self.special_instructions = data.get('special_instructions', '')
                                self.status = data.get('status', 'pending')

                                # Add service attribute (set to None since we don't have a real service)
                                self.service = None

                                # Get provider info
                                try:
                                    from users.models import User
                                    self.provider = User.objects.get(id=data.get('provider_id'))
                                except:
                                    self.provider = None

                        booking = MockBooking(booking_data, self.request.user)
                        print(f"DEBUG: Found booking via MongoDB: {booking.id}")

                except Exception as mongo_error:
                    print(f"DEBUG: MongoDB query failed: {mongo_error}")

            # Second try: Django ORM with string ID
            if not booking:
                try:
                    booking = get_object_or_404(Booking, id=booking_id, customer=self.request.user)
                    print(f"DEBUG: Found booking via Django ORM: {booking.id}")
                except Exception as orm_error:
                    print(f"DEBUG: Django ORM query failed: {orm_error}")

            # Third try: Get user's most recent booking if ID doesn't work
            if not booking:
                try:
                    booking = Booking.objects.filter(customer=self.request.user).order_by('-created_at').first()
                    if booking:
                        print(f"DEBUG: Using most recent booking: {booking.id}")
                except Exception as fallback_error:
                    print(f"DEBUG: Fallback query failed: {fallback_error}")

            if booking:
                context['booking'] = booking
            else:
                print(f"DEBUG: No booking found for ID: {booking_id}")
                context['booking'] = None
                return context

            # Calculate tax (18% GST) - handle different number types
            try:
                from decimal import Decimal
                subtotal = Decimal(str(booking.total_amount))
                tax_rate = Decimal('0.18')
                tax_amount = subtotal * tax_rate
                total_amount = subtotal + tax_amount

                context['subtotal'] = subtotal
                context['tax_amount'] = tax_amount
                context['tax_rate'] = float(tax_rate * 100)
                context['total_amount'] = total_amount
            except Exception as calc_error:
                print(f"DEBUG: Error calculating amounts: {calc_error}")
                # Fallback values
                context['subtotal'] = 0
                context['tax_amount'] = 0
                context['tax_rate'] = 18
                context['total_amount'] = 0

            # Extract detailed service information from booking notes
            if hasattr(booking, 'service') and booking.service:
                context['service_name'] = booking.service.name
                context['service_description'] = booking.service.description
                context['service_category'] = booking.service.category.name
                context['service_duration'] = booking.service.duration
            else:
                # Parse service information from booking notes
                service_info = self.parse_service_info_from_notes(booking.notes)
                context.update(service_info)

        except Exception as e:
            messages.error(self.request, f'Error loading payment page: {e}')
            context['booking'] = None

        return context

    def parse_service_info_from_notes(self, notes):
        """Parse service information from booking notes"""
        service_info = {
            'service_name': 'Home Service',
            'service_description': 'Professional home service',
            'service_category': 'General',
            'service_duration': 2,
            'provider_name': 'Service Provider'
        }

        if not notes:
            return service_info

        try:
            # Parse notes format: "Booking for {service_name} - Provider: {provider_name}"
            if ' - Provider: ' in notes:
                parts = notes.split(' - Provider: ')
                if len(parts) == 2:
                    service_part = parts[0]
                    provider_part = parts[1]

                    # Extract service name
                    if service_part.startswith('Booking for '):
                        service_name = service_part.replace('Booking for ', '')
                        service_info['service_name'] = service_name

                        # Get detailed service info from sample data
                        detailed_info = self.get_service_details_by_name(service_name)
                        if detailed_info:
                            service_info.update(detailed_info)

                    # Extract provider name
                    service_info['provider_name'] = provider_part

            # Fallback: try to extract just the service name
            elif 'Booking for ' in notes:
                service_name = notes.replace('Booking for ', '').split(' - ')[0]
                service_info['service_name'] = service_name

                # Get detailed service info from sample data
                detailed_info = self.get_service_details_by_name(service_name)
                if detailed_info:
                    service_info.update(detailed_info)

        except Exception as e:
            print(f"DEBUG: Error parsing service info from notes: {e}")

        return service_info

    def get_service_details_by_name(self, service_name):
        """Get detailed service information from sample data by name"""
        try:
            from .views import ServiceListView
            service_list_view = ServiceListView()
            sample_services = service_list_view.get_sample_services()

            for service in sample_services:
                if service['name'] == service_name:
                    return {
                        'service_name': service['name'],
                        'service_description': service['description'],
                        'service_category': service['category_name'],
                        'service_duration': service['duration'],
                        'provider_name': service['provider']['user']['get_full_name']
                    }
        except Exception as e:
            print(f"DEBUG: Error getting service details: {e}")

        return None


class ProcessPaymentView(LoginRequiredMixin, View):
    def post(self, request, booking_id):
        try:
            # Handle MongoDB ObjectId issues - try different approaches to get booking
            booking = None

            # First try: direct MongoDB query if booking_id looks like ObjectId
            if booking_id and len(booking_id) == 24:
                try:
                    import pymongo
                    from django.conf import settings
                    from bson import ObjectId

                    client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'])
                    db = client[settings.DATABASES['default']['NAME']]

                    # Query MongoDB directly
                    booking_data = db['services_booking'].find_one({
                        '_id': ObjectId(booking_id),
                        'customer_id': request.user.id
                    })

                    if booking_data:
                        # Create a mock booking object with the data
                        class MockBooking:
                            def __init__(self, data, user):
                                self.id = str(data['_id'])
                                self.customer = user
                                self.provider_id = data.get('provider_id')
                                self.booking_date = data.get('booking_date')
                                self.address = data.get('address', '')
                                self.phone_number = data.get('phone_number', '')
                                self.total_amount = data.get('total_amount', 0)
                                self.notes = data.get('notes', '')
                                self.special_instructions = data.get('special_instructions', '')
                                self.status = data.get('status', 'pending')
                                self.payment_status = data.get('payment_status', 'pending')
                                self.is_paid = data.get('is_paid', False)

                                # Get provider info
                                try:
                                    from users.models import User
                                    self.provider = User.objects.get(id=data.get('provider_id'))
                                except:
                                    self.provider = None

                        booking = MockBooking(booking_data, request.user)
                        print(f"DEBUG: Found booking via MongoDB for payment: {booking.id}")

                except Exception as mongo_error:
                    print(f"DEBUG: MongoDB payment query failed: {mongo_error}")

            # Second try: Django ORM
            if not booking:
                try:
                    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
                    print(f"DEBUG: Found booking via Django ORM for payment: {booking.id}")
                except Exception as orm_error:
                    print(f"DEBUG: Django ORM payment query failed: {orm_error}")

            if not booking:
                messages.error(request, 'Booking not found.')
                return redirect('services:service_list')

            payment_method = request.POST.get('payment_method')

            if not payment_method:
                messages.error(request, 'Please select a payment method.')
                return redirect('services:payment', booking_id=booking_id)

            # Calculate amounts
            from decimal import Decimal
            subtotal = Decimal(str(booking.total_amount))
            tax_amount = subtotal * Decimal('0.18')
            total_amount = subtotal + tax_amount

            # Generate transaction ID
            import uuid
            transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"

            print(f"DEBUG: Processing payment for booking {booking.id}")
            print(f"DEBUG: Payment method: {payment_method}")
            print(f"DEBUG: Total amount: ₹{total_amount}")

            # Update booking payment status in MongoDB
            try:
                import pymongo
                from django.conf import settings
                from bson import ObjectId
                from datetime import datetime

                client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'])
                db = client[settings.DATABASES['default']['NAME']]

                # Update booking status
                update_result = db['services_booking'].update_one(
                    {'_id': ObjectId(booking_id)},
                    {
                        '$set': {
                            'payment_status': 'paid',
                            'is_paid': True,
                            'payment_method': payment_method,
                            'transaction_id': transaction_id,
                            'paid_at': datetime.now(),
                            'updated_at': datetime.now()
                        }
                    }
                )

                if update_result.modified_count > 0:
                    print(f"DEBUG: Successfully updated booking payment status in MongoDB")
                else:
                    print(f"DEBUG: No booking updated in MongoDB")

                # Create payment record in MongoDB
                payment_data = {
                    'booking_id': booking_id,
                    'payment_method': payment_method,
                    'amount': float(total_amount),
                    'payment_status': 'completed',
                    'transaction_id': transaction_id,
                    'paid_at': datetime.now(),
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }

                payment_result = db['services_payment'].insert_one(payment_data)
                print(f"DEBUG: Created payment record: {payment_result.inserted_id}")

            except Exception as mongo_error:
                print(f"DEBUG: MongoDB payment update error: {mongo_error}")
                # Continue anyway - payment simulation

            messages.success(request, 'Payment completed successfully!')
            return redirect('services:payment_success', booking_id=booking_id)

        except Exception as e:
            messages.error(request, f'Payment failed: {e}')
            return redirect('services:payment_failed', booking_id=booking_id)


class PaymentSuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'services/payment_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking_id = kwargs.get('booking_id')

        try:
            # Handle MongoDB ObjectId issues - similar to PaymentView
            booking = None

            # First try: direct MongoDB query
            if booking_id and len(booking_id) == 24:
                try:
                    import pymongo
                    from django.conf import settings
                    from bson import ObjectId

                    client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'])
                    db = client[settings.DATABASES['default']['NAME']]

                    # Query MongoDB directly
                    booking_data = db['services_booking'].find_one({
                        '_id': ObjectId(booking_id),
                        'customer_id': self.request.user.id
                    })

                    if booking_data:
                        # Create a mock booking object
                        class MockBooking:
                            def __init__(self, data, user):
                                self.id = str(data['_id'])
                                self.customer = user
                                self.total_amount = data.get('total_amount', 0)
                                self.notes = data.get('notes', '')
                                self.payment_status = data.get('payment_status', 'pending')
                                self.is_paid = data.get('is_paid', False)
                                self.transaction_id = data.get('transaction_id', '')
                                self.payment_method = data.get('payment_method', '')
                                self.booking_date = data.get('booking_date')

                                # Get provider info
                                try:
                                    from users.models import User
                                    self.provider = User.objects.get(id=data.get('provider_id'))
                                except:
                                    self.provider = None

                        booking = MockBooking(booking_data, self.request.user)
                        print(f"DEBUG: Found booking for success page: {booking.id}")

                except Exception as mongo_error:
                    print(f"DEBUG: MongoDB success query failed: {mongo_error}")

            # Second try: Django ORM
            if not booking:
                try:
                    booking = get_object_or_404(Booking, id=booking_id, customer=self.request.user)
                except Exception as orm_error:
                    print(f"DEBUG: Django ORM success query failed: {orm_error}")

            if booking:
                context['booking'] = booking

                # Extract service information from notes
                service_info = self.parse_service_info_from_notes(booking.notes)
                context.update(service_info)

                # Add payment details
                context['transaction_id'] = getattr(booking, 'transaction_id', 'N/A')
                context['payment_method'] = getattr(booking, 'payment_method', 'N/A')

        except Exception as e:
            print(f"DEBUG: Error in PaymentSuccessView: {e}")
            messages.error(self.request, f'Error loading payment details: {e}')

        return context

    def parse_service_info_from_notes(self, notes):
        """Parse service information from booking notes"""
        service_info = {
            'service_name': 'Home Service',
            'provider_name': 'Service Provider'
        }

        if not notes:
            return service_info

        try:
            # Parse notes format: "Booking for {service_name} - Provider: {provider_name}"
            if ' - Provider: ' in notes:
                parts = notes.split(' - Provider: ')
                if len(parts) == 2:
                    service_part = parts[0]
                    provider_part = parts[1]

                    # Extract service name
                    if service_part.startswith('Booking for '):
                        service_name = service_part.replace('Booking for ', '')
                        service_info['service_name'] = service_name

                    # Extract provider name
                    service_info['provider_name'] = provider_part

        except Exception as e:
            print(f"DEBUG: Error parsing service info: {e}")

        return service_info


class PaymentFailedView(LoginRequiredMixin, TemplateView):
    template_name = 'services/payment_failed.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking_id = kwargs.get('booking_id')

        try:
            # Handle MongoDB ObjectId issues - similar to other payment views
            booking = None

            # First try: direct MongoDB query
            if booking_id and len(booking_id) == 24:
                try:
                    import pymongo
                    from django.conf import settings
                    from bson import ObjectId

                    client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'])
                    db = client[settings.DATABASES['default']['NAME']]

                    # Query MongoDB directly
                    booking_data = db['services_booking'].find_one({
                        '_id': ObjectId(booking_id),
                        'customer_id': self.request.user.id
                    })

                    if booking_data:
                        # Create a mock booking object
                        class MockBooking:
                            def __init__(self, data, user):
                                self.id = str(data['_id'])
                                self.customer = user
                                self.total_amount = data.get('total_amount', 0)
                                self.notes = data.get('notes', '')
                                self.booking_date = data.get('booking_date')

                                # Get provider info
                                try:
                                    from users.models import User
                                    self.provider = User.objects.get(id=data.get('provider_id'))
                                except:
                                    self.provider = None

                        booking = MockBooking(booking_data, self.request.user)
                        print(f"DEBUG: Found booking for failed page: {booking.id}")

                except Exception as mongo_error:
                    print(f"DEBUG: MongoDB failed query failed: {mongo_error}")

            # Second try: Django ORM
            if not booking:
                try:
                    booking = get_object_or_404(Booking, id=booking_id, customer=self.request.user)
                except Exception as orm_error:
                    print(f"DEBUG: Django ORM failed query failed: {orm_error}")

            if booking:
                context['booking'] = booking

                # Extract service information from notes
                service_info = self.parse_service_info_from_notes(booking.notes)
                context.update(service_info)

        except Exception as e:
            print(f"DEBUG: Error in PaymentFailedView: {e}")
            messages.error(self.request, f'Error loading booking details: {e}')

        return context

    def parse_service_info_from_notes(self, notes):
        """Parse service information from booking notes"""
        service_info = {
            'service_name': 'Home Service',
            'provider_name': 'Service Provider'
        }

        if not notes:
            return service_info

        try:
            # Parse notes format: "Booking for {service_name} - Provider: {provider_name}"
            if ' - Provider: ' in notes:
                parts = notes.split(' - Provider: ')
                if len(parts) == 2:
                    service_part = parts[0]
                    provider_part = parts[1]

                    # Extract service name
                    if service_part.startswith('Booking for '):
                        service_name = service_part.replace('Booking for ', '')
                        service_info['service_name'] = service_name

                    # Extract provider name
                    service_info['provider_name'] = provider_part

        except Exception as e:
            print(f"DEBUG: Error parsing service info: {e}")

        return service_info


# Invoice Views
class InvoiceView(LoginRequiredMixin, TemplateView):
    template_name = 'services/invoice.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking_id = kwargs.get('booking_id')

        try:
            booking = get_object_or_404(Booking, id=booking_id, customer=self.request.user)

            # Check if booking is approved and paid
            if booking.status != 'confirmed' or not booking.is_paid:
                messages.error(self.request, 'Invoice is only available for approved and paid bookings.')
                return context

            # Get or create invoice
            from .models import Invoice
            invoice, created = Invoice.objects.get_or_create(
                booking=booking,
                defaults={
                    'subtotal': booking.total_amount,
                    'tax_amount': booking.total_amount * 0.18,
                    'total_amount': booking.total_amount * 1.18,
                }
            )

            if created:
                # Generate QR code for service access
                self.generate_qr_code(invoice)

            context['booking'] = booking
            context['invoice'] = invoice

        except Exception as e:
            messages.error(self.request, f'Error loading invoice: {e}')

        return context

    def generate_qr_code(self, invoice):
        """Generate QR code for service access"""
        try:
            import qrcode
            from io import BytesIO
            from django.core.files import File

            # Create QR code data
            qr_data = f"HomeService Invoice: {invoice.invoice_number}\nBooking ID: {invoice.booking.id}\nAmount: ₹{invoice.total_amount}\nAccess Code: {invoice.invoice_number[-8:]}"

            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)

            # Create QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")

            # Save to BytesIO
            buffer = BytesIO()
            qr_img.save(buffer, format='PNG')
            buffer.seek(0)

            # Save to model
            filename = f"qr_{invoice.invoice_number}.png"
            invoice.qr_code.save(filename, File(buffer), save=True)

        except Exception as e:
            print(f"Error generating QR code: {e}")


class InvoiceDownloadView(LoginRequiredMixin, View):
    def get(self, request, booking_id):
        try:
            booking = get_object_or_404(Booking, id=booking_id, customer=request.user)

            # Check if booking is approved and paid
            if booking.status != 'confirmed' or not booking.is_paid:
                messages.error(request, 'Invoice download is only available for approved and paid bookings.')
                return redirect('services:booking_detail', pk=booking_id)

            # Get invoice
            from .models import Invoice
            invoice = get_object_or_404(Invoice, booking=booking)

            # Generate PDF if not exists
            if not invoice.pdf_file:
                self.generate_pdf(invoice)

            # Return PDF response
            from django.http import HttpResponse
            response = HttpResponse(invoice.pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
            return response

        except Exception as e:
            messages.error(request, f'Error downloading invoice: {e}')
            return redirect('services:booking_detail', pk=booking_id)

    def generate_pdf(self, invoice):
        """Generate PDF invoice"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from io import BytesIO
            from django.core.files import File

            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)

            # Add content to PDF
            p.drawString(100, 750, f"INVOICE - {invoice.invoice_number}")
            p.drawString(100, 720, f"Date: {invoice.generated_at.strftime('%Y-%m-%d')}")
            p.drawString(100, 690, f"Service: {invoice.booking.service.name}")
            p.drawString(100, 660, f"Customer: {invoice.booking.customer.get_full_name()}")
            p.drawString(100, 630, f"Provider: {invoice.booking.provider.get_full_name()}")
            p.drawString(100, 600, f"Subtotal: ₹{invoice.subtotal}")
            p.drawString(100, 570, f"Tax (18%): ₹{invoice.tax_amount}")
            p.drawString(100, 540, f"Total: ₹{invoice.total_amount}")

            p.showPage()
            p.save()

            buffer.seek(0)
            filename = f"invoice_{invoice.invoice_number}.pdf"
            invoice.pdf_file.save(filename, File(buffer), save=True)

        except Exception as e:
            print(f"Error generating PDF: {e}")


def service_cards_demo(request):
    """Demo view for service assignment cards"""
    return render(request, 'dashboards/service_cards_demo.html')
