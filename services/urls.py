from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views, admin_views, invoice_views

app_name = 'services'

urlpatterns = [
    # Service URLs
    path('', views.CategoriesView.as_view(), name='categories'),
    path('list/', views.ServiceListView.as_view(), name='service_list'),
    path('category/<slug:category_slug>/', views.ServiceListView.as_view(), name='category'),
    path('service/<int:pk>/', views.ServiceDetailView.as_view(), name='service_detail'),

    # Provider URLs
    path('provider/dashboard/', login_required(views.ProviderDashboardView.as_view()), name='provider_dashboard'),
    path('provider/services/', login_required(views.ServiceListView.as_view(template_name='services/provider/service_list.html')),
         name='provider_service_list'),
    path('provider/service/add/', login_required(views.ServiceCreateView.as_view()), name='service_add'),
    path('provider/service/<int:pk>/edit/', login_required(views.ServiceUpdateView.as_view()), name='service_edit'),
    path('provider/service/<int:pk>/delete/', login_required(views.ServiceDeleteView.as_view()), name='service_delete'),

    # MongoDB connection check URL
    path('check-mongodb/', views.check_mongodb_connection, name='check_mongodb'),
    path('mongodb-status/', views.mongodb_status, name='mongodb_status'),

    # Booking URLs (updated to accept string IDs for MongoDB ObjectId compatibility)
    path('book/<int:service_id>/', login_required(views.ServiceBookingView.as_view()), name='book_service'),
    path('bookings/', login_required(views.BookingListView.as_view()), name='booking_list'),
    path('bookings/<str:pk>/', login_required(views.BookingDetailView.as_view()), name='booking_detail'),
    path('bookings/<str:pk>/cancel/', login_required(views.BookingCancelViewOriginal.as_view()), name='booking_cancel'),
    path('bookings/<str:pk>/reschedule/', login_required(views.BookingRescheduleView.as_view()), name='booking_reschedule'),

    # Payment URLs (updated to accept string IDs for MongoDB ObjectId compatibility)
    path('payment/<str:booking_id>/', login_required(views.PaymentView.as_view()), name='payment'),
    path('payment/<str:booking_id>/process/', login_required(views.ProcessPaymentView.as_view()), name='process_payment'),
    path('payment/success/<str:booking_id>/', login_required(views.PaymentSuccessView.as_view()), name='payment_success'),
    path('payment/failed/<str:booking_id>/', login_required(views.PaymentFailedView.as_view()), name='payment_failed'),

    # Invoice URLs (updated to accept string IDs for MongoDB ObjectId compatibility)
    path('invoice/<str:booking_id>/', login_required(invoice_views.InvoiceDetailView.as_view()), name='invoice'),
    path('invoice/<str:booking_id>/download/', login_required(invoice_views.InvoiceDownloadView.as_view()), name='invoice_download'),
    path('api/invoice/<str:booking_id>/status/', invoice_views.check_invoice_status, name='invoice_status'),

    # New AJAX booking management URLs
    path('api/booking/update/', views.BookingUpdateView.as_view(), name='booking_update_api'),
    path('api/booking/cancel/', views.BookingCancelView.as_view(), name='booking_cancel_api'),

    # Review URLs
    path('reviews/add/<str:booking_id>/', views.add_review, name='add_review'),

    # Demo URLs
    path('service-cards-demo/', views.service_cards_demo, name='service_cards_demo'),

    # Admin URLs (Custom Admin Interface)
    path('admin-dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin-services/', admin_views.admin_services, name='admin_services'),
    path('admin-services/add/', admin_views.admin_add_service, name='admin_add_service'),
    path('admin-services/<int:service_id>/edit/', admin_views.admin_edit_service, name='admin_edit_service'),
    path('admin-services/<int:service_id>/delete/', admin_views.admin_delete_service, name='admin_delete_service'),
    path('admin-services/<int:service_id>/upload-images/', admin_views.upload_service_images, name='upload_service_images'),
    path('admin-service-images/<int:image_id>/delete/', admin_views.delete_service_image, name='delete_service_image'),
    path('admin-bookings/', admin_views.admin_bookings, name='admin_bookings'),
    path('admin-bookings/<str:booking_id>/', admin_views.admin_booking_detail, name='admin_booking_detail'),
    path('admin-pending-bookings/', admin_views.admin_pending_bookings, name='admin_pending_bookings'),
    path('admin-categories/', admin_views.admin_categories, name='admin_categories'),
    path('admin-categories/add/', admin_views.admin_add_category, name='admin_add_category'),
    path('admin-providers/', admin_views.admin_providers, name='admin_providers'),
    path('admin-reviews/', admin_views.admin_reviews, name='admin_reviews'),

    # Admin Booking Approval APIs
    path('api/admin/booking/approve/', admin_views.admin_approve_booking, name='admin_approve_booking'),
    path('api/admin/booking/reject/', admin_views.admin_reject_booking, name='admin_reject_booking'),
    path('api/admin/test-db/', admin_views.test_database_connection, name='test_database_connection'),
]
