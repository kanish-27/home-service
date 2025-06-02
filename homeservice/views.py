from django.shortcuts import render, redirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum
from services.models import Service, ServiceCategory, Booking
from users.models import User

def home(request):
    """Home page view - redirects based on user type if logged in"""
    if request.user.is_authenticated:
        if request.user.user_type == 'admin' or request.user.is_superuser:
            return redirect('admin_dashboard')
        elif request.user.user_type == 'provider':
            return redirect('servicer_dashboard')
        else:
            return redirect('user_dashboard')

    # For anonymous users, show the regular home page
    return render(request, 'home.html')

@login_required
def user_dashboard(request):
    """Dashboard for regular users to browse and book services"""

    # Get sample featured services (top 6 services)
    featured_services = [
        {
            'id': 1,
            'name': 'Electrical Installation',
            'description': 'Professional installation of electrical systems in your home or office. Includes wiring, outlets, switches, and circuit breakers.',
            'price': 2500,
            'duration': 3,
            'average_rating': 4.5,
            'review_count': 12,
            'category': {'name': 'Electrical'},
            'provider': {'user': {'get_full_name': 'Rajesh Kumar'}},
            'image': None
        },
        {
            'id': 4,
            'name': 'Pipe Repair',
            'description': 'Professional repair of leaking or damaged pipes. Includes copper, PVC, and PEX pipe repairs.',
            'price': 1200,
            'duration': 2,
            'average_rating': 4.6,
            'review_count': 10,
            'category': {'name': 'Plumbing'},
            'provider': {'user': {'get_full_name': 'Suresh Patel'}},
            'image': None
        },
        {
            'id': 7,
            'name': 'Deep Cleaning',
            'description': 'Comprehensive deep cleaning service for your entire home. Includes all rooms and surfaces.',
            'price': 3500,
            'duration': 4,
            'average_rating': 4.8,
            'review_count': 22,
            'category': {'name': 'Cleaning'},
            'provider': {'user': {'get_full_name': 'Sunita Joshi'}},
            'image': None
        },
        {
            'id': 10,
            'name': 'Furniture Repair',
            'description': 'Professional furniture repair and restoration services.',
            'price': 1800,
            'duration': 3,
            'average_rating': 4.7,
            'review_count': 11,
            'category': {'name': 'Carpentry'},
            'provider': {'user': {'get_full_name': 'Manoj Kumar'}},
            'image': None
        },
        {
            'id': 14,
            'name': 'AC Repair',
            'description': 'Professional air conditioning repair and maintenance services.',
            'price': 2500,
            'duration': 2,
            'average_rating': 4.8,
            'review_count': 19,
            'category': {'name': 'Appliance Repair'},
            'provider': {'user': {'get_full_name': 'Rohit Sharma'}},
            'image': None
        },
        {
            'id': 20,
            'name': 'CCTV Installation',
            'description': 'Professional CCTV camera installation and setup.',
            'price': 5500,
            'duration': 4,
            'average_rating': 4.7,
            'review_count': 12,
            'category': {'name': 'Security'},
            'provider': {'user': {'get_full_name': 'Ajay Kumar'}},
            'image': None
        }
    ]

    # Get sample categories
    categories = [
        {'name': 'Electrical', 'slug': 'electrical'},
        {'name': 'Plumbing', 'slug': 'plumbing'},
        {'name': 'Cleaning', 'slug': 'cleaning'},
        {'name': 'Carpentry', 'slug': 'carpentry'},
        {'name': 'Painting', 'slug': 'painting'},
        {'name': 'Appliance Repair', 'slug': 'appliance-repair'},
    ]

    context = {
        'featured_services': featured_services,
        'categories': categories,
        'user_bookings': [],
        'is_user_dashboard': True,
        'dashboard_message': 'Welcome to your dashboard! Browse our featured services below.'
    }

    # Try to get real user bookings from database if available
    try:
        from services.models import Booking
        if request.user.is_authenticated:
            # Get all user bookings for recent bookings display
            try:
                all_bookings = list(Booking.objects.filter(customer=request.user).order_by('-booking_date')[:3])
            except:
                try:
                    all_bookings = list(Booking.objects.filter(customer=request.user).order_by('-id')[:3])
                except:
                    all_bookings = list(Booking.objects.filter(customer=request.user)[:3])

            # Get confirmed bookings count for the dashboard counter
            try:
                confirmed_bookings_count = Booking.objects.filter(
                    customer=request.user,
                    status='confirmed'
                ).count()
            except:
                confirmed_bookings_count = 0

            context['user_bookings'] = all_bookings
            context['confirmed_bookings_count'] = confirmed_bookings_count

            if all_bookings:
                print(f"Found {len(all_bookings)} total bookings for user {request.user.email}")
            print(f"Found {confirmed_bookings_count} confirmed bookings for user {request.user.email}")
    except Exception as e:
        # Continue with empty bookings if database error
        print(f"Bookings data error (non-critical): {e}")
        context['confirmed_bookings_count'] = 0
        import traceback
        traceback.print_exc()

    return render(request, 'dashboards/user_dashboard.html', context)

@login_required
def admin_dashboard(request):
    """Dashboard for admins to manage services and view bookings"""
    if not (request.user.user_type == 'admin' or request.user.is_superuser):
        return redirect('user_dashboard')

    try:
        # Get statistics
        total_services = Service.objects.count()
        total_bookings = Booking.objects.count()

        # Calculate total revenue from confirmed/completed AND paid bookings only
        # Using manual approach due to Djongo boolean field query issues
        try:
            revenue_data = Booking.objects.filter(
                status__in=['confirmed', 'completed'],
                is_paid=True
            ).aggregate(total=Sum('total_amount'))
            total_revenue = revenue_data['total'] if revenue_data['total'] is not None else 0
        except Exception as e:
            # Fallback: Manual calculation for MongoDB/Djongo compatibility
            print(f"DEBUG: Using manual revenue calculation due to query error: {e}")
            confirmed_bookings = Booking.objects.filter(status__in=['confirmed', 'completed'])
            total_revenue = 0
            for booking in confirmed_bookings:
                try:
                    if hasattr(booking, 'is_paid') and booking.is_paid:
                        total_revenue += float(booking.total_amount or 0)
                except Exception:
                    continue

        # If no total_amount, calculate from service prices for confirmed+paid bookings
        if total_revenue == 0:
            try:
                paid_confirmed_bookings = Booking.objects.filter(
                    status__in=['confirmed', 'completed'],
                    is_paid=True
                ).select_related('service')
                total_revenue = sum(booking.service.price for booking in paid_confirmed_bookings)
            except Exception:
                # Manual fallback for service price calculation
                confirmed_bookings = Booking.objects.filter(status__in=['confirmed', 'completed']).select_related('service')
                for booking in confirmed_bookings:
                    try:
                        if hasattr(booking, 'is_paid') and booking.is_paid:
                            total_revenue += float(booking.service.price or 0)
                    except Exception:
                        continue

        pending_bookings = Booking.objects.filter(status='pending').count()

        # Recent bookings - MongoDB compatible approach
        try:
            # Try MongoDB first for better compatibility
            import pymongo
            from django.conf import settings
            from bson import ObjectId

            client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'])
            db = client[settings.DATABASES['default']['NAME']]

            # Get recent bookings from MongoDB
            recent_booking_docs = list(db['services_booking'].find().sort('created_at', -1).limit(5))

            recent_bookings = []
            for booking_doc in recent_booking_docs:
                try:
                    # Get customer info
                    customer = User.objects.get(id=booking_doc['customer_id'])

                    # Create a mock booking object for template compatibility
                    class MockRecentBooking:
                        def __init__(self, doc, customer_obj):
                            self.id = str(doc['_id'])
                            self.customer = customer_obj
                            self.booking_date = doc.get('booking_date')
                            self.total_amount = doc.get('total_amount', 0)
                            self.status = doc.get('status', 'pending')
                            self.created_at = doc.get('created_at')
                            self.notes = doc.get('notes', 'Service Booking')

                            # Mock service object with better service name detection
                            service_name = doc.get('notes', 'Home Service')
                            if 'plumbing' in service_name.lower():
                                service_name = 'Plumbing Service'
                            elif 'electrical' in service_name.lower():
                                service_name = 'Electrical Service'
                            elif 'cleaning' in service_name.lower():
                                service_name = 'Cleaning Service'
                            elif 'repair' in service_name.lower():
                                service_name = 'Repair Service'
                            elif 'installation' in service_name.lower():
                                service_name = 'Installation Service'

                            self.service = type('MockService', (), {
                                'name': service_name,
                                'price': doc.get('total_amount', 0)
                            })()

                        def get_status_display(self):
                            status_map = {
                                'pending': 'Pending',
                                'confirmed': 'Confirmed',
                                'rejected': 'Rejected',
                                'completed': 'Completed',
                                'cancelled': 'Cancelled'
                            }
                            return status_map.get(self.status, self.status.title())

                    mock_booking = MockRecentBooking(booking_doc, customer)
                    recent_bookings.append(mock_booking)

                except Exception as booking_error:
                    print(f"Error processing booking {booking_doc.get('_id')}: {booking_error}")
                    continue

        except Exception as mongo_error:
            print(f"MongoDB query failed, using Django ORM: {mongo_error}")

            # Fallback to Django ORM
            try:
                recent_bookings = list(Booking.objects.all().order_by('-created_at')[:5])
            except Exception as orm_error:
                print(f"Django ORM also failed: {orm_error}")
                recent_bookings = []

        # Popular services - create sample services with booking counts
        try:
            # Try to get real services first
            try:
                popular_services = list(Service.objects.all()[:5])
                if not popular_services:
                    raise Exception("No services found")
            except:
                # Create sample popular services if none exist
                popular_services = [
                    {
                        'name': 'Plumbing Repair',
                        'price': 1500,
                        'booking_count': 25,
                        'category': 'Plumbing',
                        'description': 'Professional plumbing repair services'
                    },
                    {
                        'name': 'Electrical Installation',
                        'price': 2500,
                        'booking_count': 18,
                        'category': 'Electrical',
                        'description': 'Expert electrical installation and wiring'
                    },
                    {
                        'name': 'Deep House Cleaning',
                        'price': 3500,
                        'booking_count': 32,
                        'category': 'Cleaning',
                        'description': 'Complete home deep cleaning service'
                    },
                    {
                        'name': 'AC Repair & Service',
                        'price': 2200,
                        'booking_count': 15,
                        'category': 'Appliance Repair',
                        'description': 'Air conditioning repair and maintenance'
                    },
                    {
                        'name': 'Furniture Assembly',
                        'price': 1800,
                        'booking_count': 12,
                        'category': 'Carpentry',
                        'description': 'Professional furniture assembly service'
                    }
                ]

                # Convert to mock service objects for template compatibility
                mock_services = []
                for service_data in popular_services:
                    class MockService:
                        def __init__(self, data):
                            self.name = data['name']
                            self.price = data['price']
                            self.booking_count = data['booking_count']
                            self.category = data['category']
                            self.description = data['description']

                    mock_services.append(MockService(service_data))

                popular_services = mock_services

        except Exception as service_error:
            print(f"Error fetching services: {service_error}")
            popular_services = []

    except Exception as e:
        # Handle database errors gracefully
        total_services = 0
        total_bookings = 0
        total_revenue = 0
        pending_bookings = 0
        recent_bookings = []
        popular_services = []

    context = {
        'total_services': total_services,
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        'pending_bookings': pending_bookings,
        'recent_bookings': recent_bookings,
        'popular_services': popular_services,
        'is_admin_dashboard': True,
    }
    return render(request, 'dashboards/admin_dashboard.html', context)

@login_required
def provider_dashboard(request):
    """Dashboard for service providers"""
    if request.user.user_type != 'provider':
        return redirect('user_dashboard')

    # Get provider's services
    provider_services = Service.objects.filter(
        provider=request.user
    ).select_related('category')

    # Get provider's bookings
    provider_bookings = Booking.objects.filter(
        provider=request.user
    ).select_related('service', 'customer').order_by('-created_at')[:5]

    # Get statistics
    total_bookings = Booking.objects.filter(provider=request.user).count()
    total_earnings = Booking.objects.filter(
        provider=request.user,
        is_paid=True
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    context = {
        'provider_services': provider_services,
        'provider_bookings': provider_bookings,
        'total_bookings': total_bookings,
        'total_earnings': total_earnings,
        'is_provider_dashboard': True,
    }
    return render(request, 'dashboards/provider_dashboard.html', context)

@login_required
def servicer_dashboard(request):
    """Dashboard for servicers to manage service completion using invoice ID"""
    if request.user.user_type != 'provider':
        return redirect('user_dashboard')

    try:
        # Get confirmed bookings assigned to this provider that need service completion
        confirmed_bookings = []

        # Try MongoDB first for better compatibility
        try:
            import pymongo
            from django.conf import settings
            from bson import ObjectId

            client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'])
            db = client[settings.DATABASES['default']['NAME']]

            # Get all admin-approved bookings (ready for service completion by any servicer)
            booking_docs = db['services_booking'].find({
                'status': 'confirmed'  # All admin approved bookings
            }).sort('booking_date', -1)

            for booking_doc in booking_docs:
                # Get invoice for this booking
                invoice_doc = db['services_invoice'].find_one({
                    'booking_id': booking_doc['_id']
                })

                if not invoice_doc:
                    # Create invoice if doesn't exist
                    from datetime import datetime
                    invoice_doc = {
                        'booking_id': booking_doc['_id'],
                        'invoice_number': f"INV-{str(booking_doc['_id'])[:8].upper()}",
                        'generated_at': datetime.now(),
                        'subtotal': float(booking_doc.get('total_amount', 0)),
                        'tax_amount': float(booking_doc.get('total_amount', 0)) * 0.18,
                        'total_amount': float(booking_doc.get('total_amount', 0)) * 1.18
                    }
                    db['services_invoice'].insert_one(invoice_doc)

                # Get customer info
                customer = User.objects.get(id=booking_doc['customer_id'])

                confirmed_bookings.append({
                    'booking_id': str(booking_doc['_id']),
                    'invoice_number': invoice_doc['invoice_number'],
                    'customer_name': customer.get_full_name(),
                    'customer_email': customer.email,
                    'customer_phone': booking_doc.get('phone_number', ''),
                    'service_name': booking_doc.get('notes', 'Service'),
                    'booking_date': booking_doc.get('booking_date'),
                    'address': booking_doc.get('address', ''),
                    'total_amount': booking_doc.get('total_amount', 0),
                    'status': booking_doc.get('status', 'confirmed'),
                    'special_instructions': booking_doc.get('special_instructions', ''),
                })

        except Exception as mongo_error:
            print(f"MongoDB query failed, using Django ORM: {mongo_error}")

            # Fallback to Django ORM - Get all admin-approved bookings
            bookings = Booking.objects.filter(
                status='confirmed'  # All admin approved bookings
            ).select_related('customer').order_by('-booking_date')

            for booking in bookings:
                # Get or create invoice
                from services.models import Invoice
                invoice, created = Invoice.objects.get_or_create(
                    booking=booking,
                    defaults={
                        'subtotal': booking.total_amount,
                        'tax_amount': booking.total_amount * 0.18,
                        'total_amount': booking.total_amount * 1.18,
                    }
                )

                confirmed_bookings.append({
                    'booking_id': str(booking.id),
                    'invoice_number': invoice.invoice_number,
                    'customer_name': booking.customer.get_full_name(),
                    'customer_email': booking.customer.email,
                    'customer_phone': booking.phone_number,
                    'service_name': getattr(booking.service, 'name', 'Service'),
                    'booking_date': booking.booking_date,
                    'address': booking.address,
                    'total_amount': booking.total_amount,
                    'status': booking.status,
                    'special_instructions': getattr(booking, 'special_instructions', ''),
                })

        # Get statistics
        total_assigned = len(confirmed_bookings)

        # Count completed services (try MongoDB first, then Django ORM)
        try:
            import pymongo
            client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'])
            db = client[settings.DATABASES['default']['NAME']]
            completed_count = db['services_booking'].count_documents({'status': 'completed'})
        except:
            completed_count = Booking.objects.filter(status='completed').count()

        context = {
            'confirmed_bookings': confirmed_bookings,
            'total_assigned': total_assigned,
            'completed_count': completed_count,
            'is_servicer_dashboard': True,
            'provider_name': request.user.get_full_name(),
        }

    except Exception as e:
        print(f"Error in servicer dashboard: {e}")
        context = {
            'confirmed_bookings': [],
            'total_assigned': 0,
            'completed_count': 0,
            'is_servicer_dashboard': True,
            'provider_name': request.user.get_full_name(),
            'error_message': 'Unable to load bookings at this time.'
        }

    return render(request, 'dashboards/servicer_dashboard.html', context)

@login_required
def update_service_status(request):
    """Update service status using invoice ID"""
    if request.method != 'POST':
        return redirect('servicer_dashboard')

    if request.user.user_type != 'provider':
        return redirect('user_dashboard')

    invoice_id = request.POST.get('invoice_id')
    new_status = request.POST.get('status')

    if not invoice_id or new_status not in ['completed', 'rejected']:
        messages.error(request, 'Invalid request parameters.')
        return redirect('servicer_dashboard')

    try:
        # Try MongoDB first
        try:
            import pymongo
            from django.conf import settings
            from bson import ObjectId
            from datetime import datetime

            client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'])
            db = client[settings.DATABASES['default']['NAME']]

            # Find invoice by invoice number
            invoice_doc = db['services_invoice'].find_one({
                'invoice_number': invoice_id
            })

            if not invoice_doc:
                messages.error(request, f'Invoice {invoice_id} not found.')
                return redirect('servicer_dashboard')

            # Get booking (any servicer can update any confirmed booking)
            booking_doc = db['services_booking'].find_one({
                '_id': invoice_doc['booking_id'],
                'status': 'confirmed'  # Only allow updates to confirmed bookings
            })

            if not booking_doc:
                messages.error(request, 'Booking not found or not in confirmed status.')
                return redirect('servicer_dashboard')

            # Update booking status
            update_result = db['services_booking'].update_one(
                {'_id': invoice_doc['booking_id']},
                {
                    '$set': {
                        'status': new_status,
                        'updated_at': datetime.now(),
                        'service_completed_at': datetime.now() if new_status == 'completed' else None,
                        'service_completed_by': request.user.id if new_status == 'completed' else None
                    }
                }
            )

            if update_result.modified_count > 0:
                if new_status == 'completed':
                    messages.success(request, f'Service for invoice {invoice_id} marked as completed successfully!')
                else:
                    messages.success(request, f'Service for invoice {invoice_id} marked as rejected.')
            else:
                messages.error(request, 'Failed to update service status.')

        except Exception as mongo_error:
            print(f"MongoDB update failed, trying Django ORM: {mongo_error}")

            # Fallback to Django ORM
            from services.models import Invoice, Booking

            try:
                invoice = Invoice.objects.get(invoice_number=invoice_id)
                booking = invoice.booking

                if booking.status != 'confirmed':
                    messages.error(request, 'Only confirmed bookings can be updated.')
                    return redirect('servicer_dashboard')

                booking.status = new_status
                booking.save()

                if new_status == 'completed':
                    messages.success(request, f'Service for invoice {invoice_id} marked as completed successfully!')
                else:
                    messages.success(request, f'Service for invoice {invoice_id} marked as rejected.')

            except Invoice.DoesNotExist:
                messages.error(request, f'Invoice {invoice_id} not found.')
            except Exception as orm_error:
                messages.error(request, f'Error updating service status: {orm_error}')

    except Exception as e:
        messages.error(request, f'Error updating service status: {e}')

    return redirect('servicer_dashboard')

def about(request):
    """About page view"""
    context = {
        'page_title': 'About Us',
        'company_name': 'HomeService',
        'founded_year': '2024',
        'team_size': '50+',
        'services_count': '100+',
        'customers_served': '1000+',
    }
    return render(request, 'about.html', context)

def contact(request):
    """Contact page view with review submission"""
    context = {
        'page_title': 'Contact Us',
        'company_name': 'HomeService',
        'email': 'kanishkrishna.jp2024@cse.ac.in',
        'phone': '7708750455',
        'address': 'India',
        'success_message': None,
        'error_message': None,
    }

    if request.method == 'POST':
        # Handle review/feedback submission
        try:
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()
            subject = request.POST.get('subject', '').strip()
            message = request.POST.get('message', '').strip()
            rating = request.POST.get('rating', '5')

            if name and email and message:
                # Here you could save to database or send email
                # For now, we'll just show a success message
                context['success_message'] = f'Thank you {name}! Your message has been received. We will get back to you soon.'
                print(f"Contact form submission: {name} ({email}) - {subject}: {message} - Rating: {rating}")
            else:
                context['error_message'] = 'Please fill in all required fields.'

        except Exception as e:
            context['error_message'] = 'There was an error submitting your message. Please try again.'
            print(f"Contact form error: {e}")

    return render(request, 'contact.html', context)

def handler404(request, exception, template_name='404.html'):
    """
    Custom 404 error handler.
    """
    context = {'error': '404', 'message': 'Page Not Found'}
    return render(request, 'errors/404.html', context, status=404)

def handler500(request, template_name='500.html'):
    """
    Custom 500 error handler.
    """
    context = {'error': '500', 'message': 'Server Error'}
    return render(request, 'errors/500.html', context, status=500)
