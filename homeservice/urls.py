"""
URL configuration for homeservice project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Home page and dashboards
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('provider-dashboard/', views.provider_dashboard, name='provider_dashboard'),
    path('servicer-dashboard/', views.servicer_dashboard, name='servicer_dashboard'),
    path('update-service-status/', views.update_service_status, name='update_service_status'),

    # Test page for dropdown functionality
    path('test-dropdown/', TemplateView.as_view(template_name='test_dropdown.html'), name='test_dropdown'),

    # Authentication URLs (using allauth)
    path('accounts/', include('allauth.urls')),

    # Users app
    path('', include('users.urls')),

    # Services app
    path('services/', include('services.urls')),
]

# Serve static and media files in development
if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler404 = 'homeservice.views.handler404'
handler500 = 'homeservice.views.handler500'
