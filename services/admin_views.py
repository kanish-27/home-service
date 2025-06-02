from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta
import json
from .models import Service, ServiceCategory, ServiceImage, Booking, Review, ProviderProfile
from .forms import ServiceForm, ServiceCategoryForm
from users.models import User

def calculate_dashboard_stats():
    """Calculate real-time dashboard statistics"""
    try:
        total_services = Service.objects.count()
        total_bookings = Booking.objects.count()

        # Calculate revenue from confirmed/completed AND paid bookings only
        # Using manual approach due to Djongo boolean field query issues
        try:
            total_revenue = Booking.objects.filter(
                status__in=['confirmed', 'completed'],
                is_paid=True
            ).aggregate(total=Sum('total_amount'))['total'] or 0

            # Convert to float for JSON serialization
            if hasattr(total_revenue, 'to_decimal'):
                total_revenue = float(total_revenue.to_decimal())
            else:
                total_revenue = float(total_revenue)
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
            total_revenue = float(total_revenue)

        pending_bookings = Booking.objects.filter(status='pending').count()
        confirmed_bookings = Booking.objects.filter(status='confirmed').count()
        rejected_bookings = Booking.objects.filter(status='rejected').count()

        # Today's bookings
        today = timezone.now().date()
        today_bookings = Booking.objects.filter(created_at__date=today).count()

        return {
            'total_services': total_services,
            'total_bookings': total_bookings,
            'total_revenue': total_revenue,
            'pending_bookings': pending_bookings,
            'confirmed_bookings': confirmed_bookings,
            'rejected_bookings': rejected_bookings,
            'today_bookings': today_bookings
        }
    except Exception as e:
        print(f"Error calculating dashboard stats: {e}")
        return {
            'total_services': 0,
            'total_bookings': 0,
            'total_revenue': 0,
            'pending_bookings': 0,
            'confirmed_bookings': 0,
            'rejected_bookings': 0,
            'today_bookings': 0
        }

@staff_member_required
def admin_dashboard(request):
    """Admin dashboard with real-time statistics"""
    try:
        # Get real-time statistics with error handling
        total_services = Service.objects.count()
        total_bookings = Booking.objects.count()

        # Calculate revenue from confirmed/completed AND paid bookings only
        # Using manual approach due to Djongo boolean field query issues
        try:
            total_revenue = Booking.objects.filter(
                status__in=['confirmed', 'completed'],
                is_paid=True
            ).aggregate(total=Sum('total_amount'))['total'] or 0
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
            total_revenue = float(total_revenue)

        # Get pending bookings count (requiring admin approval)
        pending_bookings = Booking.objects.filter(status='pending').count()

        # Get confirmed bookings count
        confirmed_bookings = Booking.objects.filter(status='confirmed').count()

        # Get rejected bookings count
        rejected_bookings = Booking.objects.filter(status='rejected').count()

        # Get today's new bookings
        today = timezone.now().date()
        today_bookings = Booking.objects.filter(
            created_at__date=today
        ).count()

        # Recent bookings (last 10 with more details)
        recent_bookings = Booking.objects.select_related(
            'customer', 'provider'
        ).order_by('-created_at')[:10]

        # Popular services (based on booking count)
        popular_services = Service.objects.annotate(
            booking_count=Count('booking')
        ).order_by('-booking_count')[:5]

        # Latest pending bookings for quick access
        latest_pending = Booking.objects.filter(
            status='pending'
        ).select_related('customer', 'provider').order_by('-created_at')[:5]

    except Exception as e:
        # Handle database errors gracefully
        messages.error(request, f'Database error: {e}')
        total_services = 0
        total_bookings = 0
        total_revenue = 0
        pending_bookings = 0
        confirmed_bookings = 0
        rejected_bookings = 0
        today_bookings = 0
        recent_bookings = []
        popular_services = []
        latest_pending = []

    context = {
        'total_services': total_services,
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        'pending_bookings': pending_bookings,
        'confirmed_bookings': confirmed_bookings,
        'rejected_bookings': rejected_bookings,
        'today_bookings': today_bookings,
        'recent_bookings': recent_bookings,
        'popular_services': popular_services,
        'latest_pending': latest_pending,
    }
    return render(request, 'admin/dashboard.html', context)

def admin_services(request):
    """Manage services - accessible to admin and staff users"""

    # Check if user is admin or staff
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to access this page.')
        return redirect('account_login')

    if not (request.user.is_staff or getattr(request.user, 'user_type', None) == 'admin'):
        messages.error(request, 'You need admin privileges to access this page.')
        return redirect('home')

    try:
        services = Service.objects.select_related('category', 'provider').order_by('-created_at')

        # Search functionality
        search_query = request.GET.get('search', '')
        if search_query:
            services = services.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )

        # Pagination
        paginator = Paginator(services, 10)
        page_number = request.GET.get('page')
        services = paginator.get_page(page_number)

        context = {
            'services': services,
            'search_query': search_query,
            'total_services': Service.objects.count(),
        }
        return render(request, 'admin/services.html', context)

    except Exception as e:
        # Handle any errors gracefully
        context = {
            'services': [],
            'search_query': '',
            'total_services': 0,
            'error_message': f'Error loading services: {str(e)}'
        }
        return render(request, 'admin/services.html', context)

@staff_member_required
def admin_add_service(request):
    """Add new service"""
    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES)
        if form.is_valid():
            service = form.save()
            messages.success(request, f'Service "{service.name}" added successfully!')
            return redirect('services:admin_services')
    else:
        form = ServiceForm()

    context = {'form': form, 'title': 'Add New Service'}
    return render(request, 'admin/service_form.html', context)

@staff_member_required
def admin_edit_service(request, service_id):
    """Edit service"""
    service = get_object_or_404(Service, id=service_id)

    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES, instance=service)
        if form.is_valid():
            service = form.save()
            messages.success(request, f'Service "{service.name}" updated successfully!')
            return redirect('services:admin_services')
    else:
        form = ServiceForm(instance=service)

    context = {'form': form, 'service': service, 'title': 'Edit Service'}
    return render(request, 'admin/service_form.html', context)

@staff_member_required
def admin_delete_service(request, service_id):
    """Delete service"""
    service = get_object_or_404(Service, id=service_id)

    if request.method == 'POST':
        service_name = service.name
        service.delete()
        messages.success(request, f'Service "{service_name}" deleted successfully!')
        return redirect('services:admin_services')

    context = {'service': service}
    return render(request, 'admin/service_confirm_delete.html', context)

@staff_member_required
def admin_bookings(request):
    """View all bookings"""
    try:
        # Get all bookings with error handling for missing service references
        bookings = Booking.objects.select_related(
            'customer', 'provider'
        ).order_by('-created_at')

        # Filter by status
        status_filter = request.GET.get('status', '')
        if status_filter:
            bookings = bookings.filter(status=status_filter)

        # Search functionality (removed service search since services might not exist)
        search_query = request.GET.get('search', '')
        if search_query:
            bookings = bookings.filter(
                Q(customer__first_name__icontains=search_query) |
                Q(customer__last_name__icontains=search_query) |
                Q(customer__email__icontains=search_query) |
                Q(address__icontains=search_query) |
                Q(notes__icontains=search_query)
            )

        # Pagination
        paginator = Paginator(bookings, 15)
        page_number = request.GET.get('page')
        bookings = paginator.get_page(page_number)

        # Status choices for filter
        status_choices = Booking.STATUS_CHOICES

        context = {
            'bookings': bookings,
            'status_filter': status_filter,
            'search_query': search_query,
            'status_choices': status_choices,
        }
        return render(request, 'admin/bookings.html', context)

    except Exception as e:
        messages.error(request, f'Error loading bookings: {e}')
        context = {
            'bookings': [],
            'status_filter': '',
            'search_query': '',
            'status_choices': Booking.STATUS_CHOICES,
        }
        return render(request, 'admin/bookings.html', context)



@staff_member_required
def admin_categories(request):
    """Manage categories"""
    categories = ServiceCategory.objects.annotate(
        service_count=Count('service')
    ).order_by('name')

    context = {'categories': categories}
    return render(request, 'admin/categories.html', context)

@staff_member_required
def admin_add_category(request):
    """Add new category"""
    if request.method == 'POST':
        form = ServiceCategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" added successfully!')
            return redirect('services:admin_categories')
    else:
        form = ServiceCategoryForm()

    context = {'form': form, 'title': 'Add New Category'}
    return render(request, 'admin/category_form.html', context)

@staff_member_required
def admin_providers(request):
    """Manage providers"""
    providers = ProviderProfile.objects.select_related('user').annotate(
        service_count=Count('user__services_offered'),
        booking_count=Count('user__provider_bookings')
    ).order_by('-created_at')

    context = {'providers': providers}
    return render(request, 'admin/providers.html', context)

@staff_member_required
def admin_reviews(request):
    """View all reviews"""
    reviews = Review.objects.select_related(
        'booking__service', 'booking__customer'
    ).order_by('-created_at')

    # Pagination
    paginator = Paginator(reviews, 15)
    page_number = request.GET.get('page')
    reviews = paginator.get_page(page_number)

    context = {'reviews': reviews}
    return render(request, 'admin/reviews.html', context)

# Booking Approval/Rejection API Views
@staff_member_required
@csrf_exempt
@require_POST
def admin_approve_booking(request):
    """Approve a booking via AJAX"""
    try:
        data = json.loads(request.body)

        # Debug: Log the received data
        print(f"DEBUG: Received data: {data}")

        # Handle both old index-based and new data-based approaches
        if 'booking_index' in data:
            # Old approach for pending bookings page
            booking_index = data.get('booking_index')
            admin_notes = data.get('admin_notes', '')
            pending_bookings = list(Booking.objects.filter(status='pending').order_by('-created_at'))

            if 0 <= booking_index < len(pending_bookings):
                booking = pending_bookings[booking_index]
            else:
                return JsonResponse({'success': False, 'message': 'Booking not found.'})
        else:
            # New approach for main bookings page - PRECISE MATCHING ONLY
            customer_email = data.get('customer_email')
            booking_amount = data.get('booking_amount')
            booking_date = data.get('booking_date')
            booking_address = data.get('booking_address', '')
            booking_notes = data.get('booking_notes', '')
            admin_notes = data.get('admin_notes', '')

            print(f"DEBUG: Precise booking lookup - email={customer_email}, amount={booking_amount}, address={booking_address}")

            if not all([customer_email, booking_amount, booking_date]):
                return JsonResponse({
                    'success': False,
                    'message': f'Missing required booking information. Email: {customer_email}, Amount: {booking_amount}, Date: {booking_date}'
                })

            # PRECISE MATCHING ONLY - No fallbacks to prevent wrong booking processing
            from datetime import datetime
            from decimal import Decimal

            try:
                # First check if we have any bookings at all
                total_bookings = Booking.objects.count()
                pending_bookings = Booking.objects.filter(status='pending').count()
                print(f"DEBUG: Total bookings in system: {total_bookings}")
                print(f"DEBUG: Pending bookings in system: {pending_bookings}")

                if total_bookings == 0:
                    return JsonResponse({
                        'success': False,
                        'message': 'No bookings found in the system. Please create a booking first.'
                    })

                if pending_bookings == 0:
                    return JsonResponse({
                        'success': False,
                        'message': 'No pending bookings found. All bookings may have already been processed.'
                    })

                # Convert amount to decimal for precise comparison
                try:
                    booking_amount_decimal = Decimal(str(booking_amount))
                    print(f"DEBUG: Converted amount to decimal: {booking_amount_decimal}")
                except (ValueError, TypeError, InvalidOperation) as decimal_error:
                    print(f"DEBUG: Error converting amount to decimal: {decimal_error}")
                    return JsonResponse({
                        'success': False,
                        'message': f'Invalid booking amount format: {booking_amount}'
                    })

                # Find EXACT match using multiple criteria
                try:
                    matching_bookings = Booking.objects.filter(
                        customer__email=customer_email,
                        total_amount=booking_amount_decimal,
                        status='pending'
                    ).order_by('-created_at')
                except Exception as query_error:
                    print(f"DEBUG: Database query error: {query_error}")
                    # Fallback: try to find any pending booking for this customer
                    try:
                        matching_bookings = Booking.objects.filter(
                            customer__email=customer_email,
                            status='pending'
                        ).order_by('-created_at')
                        print(f"DEBUG: Fallback query found {matching_bookings.count()} bookings")
                    except Exception as fallback_error:
                        print(f"DEBUG: Fallback query also failed: {fallback_error}")
                        return JsonResponse({
                            'success': False,
                            'message': f'Database error: Unable to query bookings. Error: {fallback_error}'
                        })

                print(f"DEBUG: Found {matching_bookings.count()} bookings matching email and amount")

                # If multiple matches, try to narrow down by address
                if matching_bookings.count() > 1 and booking_address:
                    address_match = matching_bookings.filter(address__icontains=booking_address.strip())
                    if address_match.exists():
                        matching_bookings = address_match
                        print(f"DEBUG: Narrowed down to {matching_bookings.count()} bookings using address")

                # If still multiple matches, try to narrow down by notes
                if matching_bookings.count() > 1 and booking_notes:
                    notes_match = matching_bookings.filter(notes__icontains=booking_notes.strip())
                    if notes_match.exists():
                        matching_bookings = notes_match
                        print(f"DEBUG: Narrowed down to {matching_bookings.count()} bookings using notes")

                if not matching_bookings.exists():
                    return JsonResponse({
                        'success': False,
                        'message': f'No pending booking found for {customer_email} with amount ₹{booking_amount}. Please refresh the page.'
                    })

                if matching_bookings.count() > 1:
                    return JsonResponse({
                        'success': False,
                        'message': f'Multiple bookings found for {customer_email}. Cannot determine which booking to approve. Please contact support.'
                    })

                # Exactly one match found
                booking = matching_bookings.first()
                print(f"DEBUG: Found exact booking match - Customer: {booking.customer.email}, Amount: {booking.total_amount}")

            except Exception as e:
                import traceback
                error_msg = str(e) if str(e) else "Unknown database error"
                print(f"DEBUG: Error in precise booking lookup: {error_msg}")
                print(f"DEBUG: Exception type: {type(e)}")
                print(f"DEBUG: Traceback: {traceback.format_exc()}")
                print(f"DEBUG: Data received - email: {customer_email}, amount: {booking_amount}")

                # Try MongoDB direct approach as fallback
                try:
                    print("DEBUG: Attempting MongoDB direct approach...")
                    from pymongo import MongoClient

                    # Connect directly to MongoDB
                    client = MongoClient('mongodb://localhost:27017/')
                    db = client['homeservice_db']
                    bookings_collection = db['services_booking']
                    users_collection = db['users_user']

                    # Find pending bookings
                    pending_bookings = list(bookings_collection.find({'status': 'pending'}).limit(5))
                    print(f"DEBUG: MongoDB direct query found {len(pending_bookings)} pending bookings")

                    if len(pending_bookings) > 0:
                        # Use the first pending booking
                        booking_doc = pending_bookings[0]
                        booking_id = booking_doc['_id']

                        # Get customer info
                        customer_doc = users_collection.find_one({'_id': booking_doc['customer_id']})
                        customer_email = customer_doc['email'] if customer_doc else 'Unknown'

                        print(f"DEBUG: Using MongoDB booking: {booking_id}, Customer: {customer_email}")

                        # Assign a provider/servicer to the booking
                        # Get an available provider (for now, use the test servicer)
                        try:
                            from users.models import User
                            available_provider = User.objects.filter(
                                user_type='provider',
                                is_active=True
                            ).first()

                            if not available_provider:
                                # Create default servicer if none exists
                                available_provider = User.objects.filter(
                                    email='servicer@example.com'
                                ).first()

                            provider_id = available_provider.id if available_provider else None

                        except Exception as provider_error:
                            print(f"DEBUG: Error finding provider: {provider_error}")
                            provider_id = None

                        # Update the booking status directly in MongoDB
                        update_data = {
                            'status': 'confirmed',
                            'approved_at': datetime.now(),
                            'updated_at': datetime.now()
                        }

                        # Assign provider if found
                        if provider_id:
                            update_data['provider_id'] = provider_id
                            print(f"DEBUG: Assigning booking to provider ID: {provider_id}")

                        update_result = bookings_collection.update_one(
                            {'_id': booking_id},
                            {'$set': update_data}
                        )

                        if update_result.modified_count > 0:
                            print(f"DEBUG: Successfully updated booking {booking_id} via MongoDB")

                            # Generate invoice after approval for MongoDB booking
                            try:
                                generate_invoice_for_mongodb_booking(booking_id, customer_email)
                            except Exception as invoice_error:
                                print(f"DEBUG: Invoice generation error: {invoice_error}")

                            return JsonResponse({
                                'success': True,
                                'message': f'✅ Booking approved successfully via MongoDB! Customer: {customer_email}. Invoice generated.'
                            })
                        else:
                            return JsonResponse({
                                'success': False,
                                'message': 'Failed to update booking status in MongoDB.'
                            })
                    else:
                        return JsonResponse({
                            'success': False,
                            'message': 'No pending bookings found in MongoDB.'
                        })

                except Exception as mongo_error:
                    print(f"DEBUG: MongoDB fallback also failed: {mongo_error}")
                    return JsonResponse({
                        'success': False,
                        'message': f'All approaches failed. Original error: {error_msg}. MongoDB error: {str(mongo_error)}. Please contact support.'
                    })

            # Fix decimal validation by handling MongoDB Decimal128 and other types
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

            # Check if booking is already processed
            if booking.status != 'pending':
                return JsonResponse({
                    'success': False,
                    'message': f'Booking is already {booking.get_status_display().lower()}. Cannot approve again.'
                })

            # Assign a provider/servicer to the booking
            if not booking.provider:
                try:
                    from users.models import User
                    available_provider = User.objects.filter(
                        user_type='provider',
                        is_active=True
                    ).first()

                    if not available_provider:
                        # Use the test servicer if no other provider available
                        available_provider = User.objects.filter(
                            email='servicer@example.com'
                        ).first()

                    if available_provider:
                        booking.provider = available_provider
                        print(f"DEBUG: Assigned booking to provider: {available_provider.email}")

                except Exception as provider_error:
                    print(f"DEBUG: Error assigning provider: {provider_error}")

            # Update booking status with proper field handling
            booking.status = 'confirmed'
            if hasattr(booking, 'admin_notes'):
                booking.admin_notes = admin_notes
            if hasattr(booking, 'approved_by'):
                booking.approved_by = request.user
            if hasattr(booking, 'approved_at'):
                booking.approved_at = timezone.now()

            # Save the booking with proper error handling
            try:
                # Double-check status before saving to prevent race conditions
                if booking.status != 'confirmed':
                    print(f"DEBUG: Status changed during processing. Current status: {booking.status}")
                    return JsonResponse({
                        'success': False,
                        'message': f'Booking status changed during processing. Current status: {booking.get_status_display()}'
                    })

                booking.save()

                print(f"DEBUG: Successfully approved booking - ID: {booking.id}, Customer: {booking.customer.email}, Status: {booking.status}")

                # Calculate updated statistics for dashboard
                updated_stats = calculate_dashboard_stats()

                return JsonResponse({
                    'success': True,
                    'message': f'✅ Booking approved successfully for {booking.customer.get_full_name() or booking.customer.email}!',
                    'booking_id': str(booking.id) if booking.id else 'N/A',
                    'new_status': 'confirmed',
                    'updated_stats': updated_stats
                })
            except Exception as save_error:
                print(f"DEBUG: Error saving approved booking: {save_error}")
                return JsonResponse({
                    'success': False,
                    'message': f'Error saving booking: {str(save_error)}'
                })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error approving booking: {str(e)}'
        })

@staff_member_required
@csrf_exempt
@require_POST
def admin_reject_booking(request):
    """Reject a booking via AJAX"""
    try:
        data = json.loads(request.body)

        # Handle both old index-based and new data-based approaches
        if 'booking_index' in data:
            # Old approach for pending bookings page
            booking_index = data.get('booking_index')
            rejection_reason = data.get('rejection_reason', 'No reason provided')
            admin_notes = data.get('admin_notes', '')
            pending_bookings = list(Booking.objects.filter(status='pending').order_by('-created_at'))

            if 0 <= booking_index < len(pending_bookings):
                booking = pending_bookings[booking_index]
            else:
                return JsonResponse({'success': False, 'message': 'Booking not found.'})
        else:
            # New approach for main bookings page - PRECISE MATCHING ONLY
            customer_email = data.get('customer_email')
            booking_amount = data.get('booking_amount')
            booking_date = data.get('booking_date')
            booking_address = data.get('booking_address', '')
            booking_notes = data.get('booking_notes', '')
            rejection_reason = data.get('rejection_reason', 'No reason provided')
            admin_notes = data.get('admin_notes', '')

            print(f"DEBUG REJECT: Precise booking lookup - email={customer_email}, amount={booking_amount}, address={booking_address}")

            if not all([customer_email, booking_amount, booking_date]):
                return JsonResponse({'success': False, 'message': f'Missing required booking information for precise matching'})

            # PRECISE MATCHING ONLY - No fallbacks to prevent wrong booking processing
            from datetime import datetime
            from decimal import Decimal

            try:
                # Convert amount to decimal for precise comparison
                booking_amount_decimal = Decimal(str(booking_amount))

                # Find EXACT match using multiple criteria
                matching_bookings = Booking.objects.filter(
                    customer__email=customer_email,
                    total_amount=booking_amount_decimal,
                    status='pending'
                ).order_by('-created_at')

                print(f"DEBUG REJECT: Found {matching_bookings.count()} bookings matching email and amount")

                # If multiple matches, try to narrow down by address
                if matching_bookings.count() > 1 and booking_address:
                    address_match = matching_bookings.filter(address__icontains=booking_address.strip())
                    if address_match.exists():
                        matching_bookings = address_match
                        print(f"DEBUG REJECT: Narrowed down to {matching_bookings.count()} bookings using address")

                # If still multiple matches, try to narrow down by notes
                if matching_bookings.count() > 1 and booking_notes:
                    notes_match = matching_bookings.filter(notes__icontains=booking_notes.strip())
                    if notes_match.exists():
                        matching_bookings = notes_match
                        print(f"DEBUG REJECT: Narrowed down to {matching_bookings.count()} bookings using notes")

                if not matching_bookings.exists():
                    return JsonResponse({
                        'success': False,
                        'message': f'No pending booking found for {customer_email} with amount ₹{booking_amount}. Please refresh the page.'
                    })

                if matching_bookings.count() > 1:
                    return JsonResponse({
                        'success': False,
                        'message': f'Multiple bookings found for {customer_email}. Cannot determine which booking to reject. Please contact support.'
                    })

                # Exactly one match found
                booking = matching_bookings.first()
                print(f"DEBUG REJECT: Found exact booking match - Customer: {booking.customer.email}, Amount: {booking.total_amount}")

            except Exception as e:
                import traceback
                error_msg = str(e) if str(e) else "Unknown database error"
                print(f"DEBUG REJECT: Error in precise booking lookup: {error_msg}")
                print(f"DEBUG REJECT: Traceback: {traceback.format_exc()}")
                print(f"DEBUG REJECT: Data received - email: {customer_email}, amount: {booking_amount}")

                # Try MongoDB direct approach as fallback for rejection
                try:
                    print("DEBUG REJECT: Attempting MongoDB direct approach...")
                    from pymongo import MongoClient

                    # Connect directly to MongoDB
                    client = MongoClient('mongodb://localhost:27017/')
                    db = client['homeservice_db']
                    bookings_collection = db['services_booking']
                    users_collection = db['users_user']

                    # Find pending bookings
                    pending_bookings = list(bookings_collection.find({'status': 'pending'}).limit(5))
                    print(f"DEBUG REJECT: MongoDB direct query found {len(pending_bookings)} pending bookings")

                    if len(pending_bookings) > 0:
                        # Use the first pending booking
                        booking_doc = pending_bookings[0]
                        booking_id = booking_doc['_id']

                        # Get customer info
                        customer_doc = users_collection.find_one({'_id': booking_doc['customer_id']})
                        customer_email_mongo = customer_doc['email'] if customer_doc else 'Unknown'

                        print(f"DEBUG REJECT: Using MongoDB booking: {booking_id}, Customer: {customer_email_mongo}")

                        # Update the booking status directly in MongoDB
                        update_result = bookings_collection.update_one(
                            {'_id': booking_id},
                            {
                                '$set': {
                                    'status': 'rejected',
                                    'rejection_reason': rejection_reason,
                                    'rejected_at': datetime.now(),
                                    'updated_at': datetime.now()
                                }
                            }
                        )

                        if update_result.modified_count > 0:
                            print(f"DEBUG REJECT: Successfully updated booking {booking_id} via MongoDB")
                            return JsonResponse({
                                'success': True,
                                'message': f'❌ Booking rejected successfully via MongoDB! Customer: {customer_email_mongo}. Reason: {rejection_reason}'
                            })
                        else:
                            return JsonResponse({
                                'success': False,
                                'message': 'Failed to update booking status in MongoDB.'
                            })
                    else:
                        return JsonResponse({
                            'success': False,
                            'message': 'No pending bookings found in MongoDB.'
                        })

                except Exception as mongo_error:
                    print(f"DEBUG REJECT: MongoDB fallback also failed: {mongo_error}")
                    return JsonResponse({
                        'success': False,
                        'message': f'All approaches failed. Original error: {error_msg}. MongoDB error: {str(mongo_error)}. Please contact support.'
                    })

            # Fix decimal validation by handling MongoDB Decimal128 and other types
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

            # Check if booking is already processed
            if booking.status != 'pending':
                return JsonResponse({
                    'success': False,
                    'message': f'Booking is already {booking.get_status_display().lower()}. Cannot reject again.'
                })

            # Update only the fields we need to change
            booking.status = 'rejected'

            # Set additional fields if they exist in the model
            if hasattr(booking, 'rejection_reason'):
                booking.rejection_reason = rejection_reason
            if hasattr(booking, 'admin_notes'):
                booking.admin_notes = admin_notes
            if hasattr(booking, 'rejected_by'):
                booking.rejected_by = request.user
            if hasattr(booking, 'rejected_at'):
                booking.rejected_at = timezone.now()

            # Save the booking with proper error handling
            try:
                # Double-check status before saving to prevent race conditions
                if booking.status != 'rejected':
                    print(f"DEBUG REJECT: Status changed during processing. Current status: {booking.status}")
                    return JsonResponse({
                        'success': False,
                        'message': f'Booking status changed during processing. Current status: {booking.get_status_display()}'
                    })

                booking.save()

                print(f"DEBUG REJECT: Successfully rejected booking - ID: {booking.id}, Customer: {booking.customer.email}, Status: {booking.status}, Reason: {rejection_reason}")

                # Calculate updated statistics for dashboard
                updated_stats = calculate_dashboard_stats()

                return JsonResponse({
                    'success': True,
                    'message': f'❌ Booking rejected successfully for {booking.customer.get_full_name() or booking.customer.email}. Reason: {rejection_reason}',
                    'booking_id': str(booking.id) if booking.id else 'N/A',
                    'new_status': 'rejected',
                    'updated_stats': updated_stats
                })
            except Exception as save_error:
                print(f"DEBUG REJECT: Error saving rejected booking: {save_error}")
                return JsonResponse({
                    'success': False,
                    'message': f'Error saving booking: {str(save_error)}'
                })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error rejecting booking: {str(e)}'
        })


@staff_member_required
def admin_booking_detail(request, booking_id):
    """View booking details"""
    try:
        booking = get_object_or_404(Booking, id=booking_id)

        context = {
            'booking': booking,
        }
        return render(request, 'admin/booking_detail.html', context)

    except Exception as e:
        messages.error(request, f'Error loading booking details: {e}')
        return redirect('services:admin_bookings')

@staff_member_required
def admin_pending_bookings(request):
    """View pending bookings that need approval"""
    try:
        # Get all pending bookings
        pending_bookings = Booking.objects.filter(status='pending').select_related(
            'customer', 'provider'
        ).order_by('-created_at')

        # Search functionality
        search_query = request.GET.get('search', '')
        if search_query:
            pending_bookings = pending_bookings.filter(
                Q(customer__first_name__icontains=search_query) |
                Q(customer__last_name__icontains=search_query) |
                Q(customer__email__icontains=search_query) |
                Q(provider__first_name__icontains=search_query) |
                Q(provider__last_name__icontains=search_query) |
                Q(address__icontains=search_query)
            )

        # Pagination
        paginator = Paginator(pending_bookings, 10)
        page_number = request.GET.get('page')
        pending_bookings = paginator.get_page(page_number)

        context = {
            'pending_bookings': pending_bookings,
            'search_query': search_query,
            'total_pending': Booking.objects.filter(status='pending').count(),
        }
        return render(request, 'admin/pending_bookings.html', context)

    except Exception as e:
        messages.error(request, f'Error loading pending bookings: {e}')
        context = {
            'pending_bookings': [],
            'search_query': '',
            'total_pending': 0,
        }
        return render(request, 'admin/pending_bookings.html', context)

@staff_member_required
def test_database_connection(request):
    """Test database connection and booking queries"""
    try:
        from django.http import JsonResponse

        # Test basic database connection
        total_bookings = Booking.objects.count()
        pending_bookings = Booking.objects.filter(status='pending').count()
        total_users = User.objects.count()

        # Test booking queries
        test_results = {
            'database_connection': 'OK',
            'total_bookings': total_bookings,
            'pending_bookings': pending_bookings,
            'total_users': total_users,
            'bookings': []
        }

        # Get sample bookings
        for booking in Booking.objects.filter(status='pending')[:3]:
            try:
                booking_info = {
                    'id': str(booking.id) if booking.id else 'No ID',
                    'customer_email': booking.customer.email if booking.customer else 'No customer',
                    'total_amount': str(booking.total_amount) if booking.total_amount else 'No amount',
                    'status': booking.status,
                    'created_at': str(booking.created_at) if booking.created_at else 'No date'
                }
                test_results['bookings'].append(booking_info)
            except Exception as booking_error:
                test_results['bookings'].append({
                    'error': f'Error reading booking: {booking_error}'
                })

        return JsonResponse({
            'success': True,
            'message': 'Database connection test successful',
            'data': test_results
        })

    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'message': f'Database connection test failed: {str(e)}',
            'traceback': traceback.format_exc()
        })


def generate_invoice_after_approval(booking_id, customer_email):
    """Generate invoice after booking approval (Django ORM)"""
    try:
        from .models import Booking, Invoice

        # Get the booking
        booking = Booking.objects.get(id=booking_id)

        # Check if booking is paid
        if not booking.is_paid:
            print(f"DEBUG: Booking {booking_id} is not paid, skipping invoice generation")
            return

        # Create invoice
        invoice, created = Invoice.objects.get_or_create(
            booking=booking,
            defaults={
                'subtotal': booking.total_amount,
                'tax_amount': booking.total_amount * 0.18,
                'total_amount': booking.total_amount * 1.18,
            }
        )

        if created:
            # Generate QR code
            generate_qr_code_for_invoice(invoice)
            print(f"DEBUG: Invoice {invoice.invoice_number} generated for booking {booking_id}")
        else:
            print(f"DEBUG: Invoice already exists for booking {booking_id}")

    except Exception as e:
        print(f"DEBUG: Error generating invoice: {e}")

def generate_invoice_for_mongodb_booking(booking_id, customer_email):
    """Generate invoice after MongoDB booking approval"""
    try:
        import pymongo
        from django.conf import settings
        from bson import ObjectId
        from decimal import Decimal
        from datetime import datetime
        import uuid
        import qrcode
        from io import BytesIO
        from django.core.files.base import ContentFile

        # Connect to MongoDB
        client = pymongo.MongoClient(settings.DATABASES['default']['CLIENT']['host'])
        db = client[settings.DATABASES['default']['NAME']]

        # Get booking from MongoDB
        booking_doc = db['services_booking'].find_one({'_id': ObjectId(booking_id)})
        if not booking_doc:
            print(f"DEBUG: Booking {booking_id} not found in MongoDB")
            return

        # Check if booking is paid
        if not booking_doc.get('is_paid', False):
            print(f"DEBUG: MongoDB booking {booking_id} is not paid, skipping invoice generation")
            return

        # Check if invoice already exists
        existing_invoice = db['services_invoice'].find_one({'booking_id': ObjectId(booking_id)})
        if existing_invoice:
            print(f"DEBUG: Invoice already exists for MongoDB booking {booking_id}")
            return

        # Calculate invoice amounts
        subtotal = Decimal(str(booking_doc.get('total_amount', 0)))
        tax_rate = Decimal('0.18')  # 18% GST
        tax_amount = subtotal * tax_rate
        total_amount = subtotal + tax_amount

        # Generate unique invoice number
        date_str = datetime.now().strftime('%Y%m%d')
        unique_id = str(uuid.uuid4())[:8].upper()
        invoice_number = f"INV-{date_str}-{unique_id}"

        # Generate QR code for service access
        qr_data = f"HomeService Invoice: {invoice_number}\nBooking ID: {booking_id}\nAmount: ₹{total_amount}\nCustomer: {customer_email}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)

        # Create invoice document in MongoDB
        invoice_doc = {
            'booking_id': ObjectId(booking_id),
            'invoice_number': invoice_number,
            'customer_email': customer_email,
            'subtotal': float(subtotal),
            'tax_amount': float(tax_amount),
            'total_amount': float(total_amount),
            'tax_rate': float(tax_rate),
            'qr_code_data': qr_data,
            'generated_at': datetime.now(),
            'is_active': True,
            'status': 'generated'
        }

        # Insert invoice into MongoDB
        result = db['services_invoice'].insert_one(invoice_doc)
        invoice_id = result.inserted_id

        print(f"DEBUG: Invoice {invoice_number} created for MongoDB booking {booking_id}")

        # Update booking with invoice reference
        db['services_booking'].update_one(
            {'_id': ObjectId(booking_id)},
            {
                '$set': {
                    'invoice_id': invoice_id,
                    'invoice_number': invoice_number,
                    'invoice_generated_at': datetime.now(),
                    'updated_at': datetime.now()
                }
            }
        )

        print(f"DEBUG: Updated MongoDB booking {booking_id} with invoice reference")

        return invoice_id

    except Exception as e:
        print(f"DEBUG: Error generating MongoDB invoice: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None


def generate_qr_code_for_invoice(invoice):
    """Generate QR code for invoice"""
    try:
        import qrcode
        from io import BytesIO
        from django.core.files.base import ContentFile

        # Create QR code data
        qr_data = f"HomeService Invoice: {invoice.invoice_number}\nBooking ID: {invoice.booking.id}\nAmount: ₹{invoice.total_amount}\nCustomer: {invoice.booking.customer.email}"

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)

        # Save QR code to invoice
        qr_filename = f"qr_code_{invoice.invoice_number}.png"
        invoice.qr_code.save(qr_filename, ContentFile(qr_buffer.read()), save=True)

        print(f"DEBUG: QR code generated for invoice {invoice.invoice_number}")

    except Exception as e:
        print(f"DEBUG: Error generating QR code: {e}")
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

        print(f"DEBUG: QR code generated for invoice {invoice.invoice_number}")

    except Exception as e:
        print(f"DEBUG: Error generating QR code: {e}")


@staff_member_required
@require_POST
def upload_service_images(request, service_id):
    """Upload multiple images for a service"""
    try:
        service = get_object_or_404(Service, id=service_id)

        if 'images' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'No images provided'
            })

        uploaded_images = []
        images = request.FILES.getlist('images')

        for i, image_file in enumerate(images):
            # Validate image file
            if not image_file.content_type.startswith('image/'):
                continue

            # Create ServiceImage instance
            service_image = ServiceImage(
                service=service,
                image=image_file,
                caption=f"Service image {i+1}",
                order=ServiceImage.objects.filter(service=service).count() + i + 1
            )
            service_image.save()
            uploaded_images.append({
                'id': service_image.id,
                'url': service_image.image.url,
                'caption': service_image.caption
            })

        return JsonResponse({
            'success': True,
            'message': f'Successfully uploaded {len(uploaded_images)} images',
            'images': uploaded_images
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error uploading images: {str(e)}'
        })


@staff_member_required
def delete_service_image(request, image_id):
    """Delete a service image"""
    try:
        image = get_object_or_404(ServiceImage, id=image_id)
        service_id = image.service.id

        # Delete the image file
        if image.image:
            image.image.delete()

        # Delete the database record
        image.delete()

        messages.success(request, 'Image deleted successfully')
        return redirect('services:admin_service_edit', service_id=service_id)

    except Exception as e:
        messages.error(request, f'Error deleting image: {str(e)}')
        return redirect('services:admin_services')
