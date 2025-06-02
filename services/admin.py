from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Sum
from django.utils.safestring import mark_safe

from .models import ServiceCategory, Service, ServiceImage, Booking, Review, ProviderProfile

# Customize admin site headers
admin.site.site_header = "Home Service Admin"
admin.site.site_title = "Home Service Admin Portal"
admin.site.index_title = "Welcome to Home Service Administration"


class ReviewInline(admin.StackedInline):
    model = Review
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    fields = ('booking', 'rating', 'comment', 'created_at', 'updated_at')
    can_delete = False


class ServiceInline(admin.TabularInline):
    model = Service
    extra = 1
    fields = ('name', 'price', 'duration', 'provider')
    show_change_link = True


class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 1
    fields = ('image', 'caption', 'is_primary', 'order', 'image_preview')
    readonly_fields = ('image_preview',)
    ordering = ('order', 'created_at')

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'provider_name', 'price_display', 'duration', 'is_active', 'is_available', 'booking_count', 'created_at')
    list_filter = ('category', 'is_active', 'is_available', 'created_at')
    search_fields = ('name', 'description', 'provider__user__email', 'provider__user__first_name', 'provider__user__last_name')
    list_editable = ('is_active', 'is_available')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'booking_count')
    inlines = [ServiceImageInline]

    fieldsets = (
        ('Service Information', {
            'fields': ('name', 'description', 'category')
        }),
        ('Pricing & Duration', {
            'fields': ('price', 'duration')
        }),
        ('Provider', {
            'fields': ('provider',)
        }),
        ('Availability', {
            'fields': ('is_active', 'is_available')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Statistics', {
            'fields': ('booking_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def provider_name(self, obj):
        if obj.provider:
            return f"{obj.provider.user.get_full_name() or obj.provider.user.email}"
        return "No Provider"
    provider_name.short_description = 'Provider'

    def price_display(self, obj):
        return f"₹{obj.price}"
    price_display.short_description = 'Price'

    def booking_count(self, obj):
        return obj.bookings.count()
    booking_count.short_description = 'Total Bookings'


@admin.register(ServiceImage)
class ServiceImageAdmin(admin.ModelAdmin):
    list_display = ('service', 'caption', 'is_primary', 'order', 'image_preview', 'created_at')
    list_filter = ('is_primary', 'created_at', 'service__category')
    search_fields = ('service__name', 'caption')
    list_editable = ('is_primary', 'order')
    ordering = ('service', 'order', 'created_at')
    readonly_fields = ('created_at', 'image_preview')
    raw_id_fields = ('service',)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="150" height="150" style="object-fit: cover;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'


class BookingInline(admin.TabularInline):
    model = Booking
    extra = 0
    fields = ('service', 'customer', 'booking_date', 'status', 'total_amount', 'payment_status')
    readonly_fields = ('created_at', 'updated_at')
    show_change_link = True


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'service_name', 'customer_name', 'customer_email', 'booking_date', 'status', 'total_amount_display', 'payment_status', 'created_at')
    list_filter = ('status', 'is_paid', 'booking_date', 'created_at', 'service__category')
    search_fields = (
        'service__name',
        'customer__email',
        'customer__first_name',
        'customer__last_name',
        'provider__email',
        'provider__first_name',
        'provider__last_name',
        'address',
        'phone_number'
    )
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at', 'payment_intent_id', 'booking_id')
    date_hierarchy = 'booking_date'
    raw_id_fields = ('service', 'customer', 'provider')
    inlines = [ReviewInline]
    list_per_page = 25

    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_id', 'service', 'customer', 'provider')
        }),
        ('Schedule', {
            'fields': ('booking_date',)
        }),
        ('Contact Details', {
            'fields': ('address', 'phone_number', 'special_instructions')
        }),
        ('Status & Payment', {
            'fields': ('status', 'is_paid', 'payment_status', 'payment_intent_id')
        }),
        ('Pricing', {
            'fields': ('total_amount', 'additional_charges', 'discount_amount')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def booking_id(self, obj):
        return f"BK-{obj.id:06d}"
    booking_id.short_description = 'Booking ID'

    def service_name(self, obj):
        return obj.service.name
    service_name.short_description = 'Service'

    def customer_name(self, obj):
        return obj.customer.get_full_name() or obj.customer.email
    customer_name.short_description = 'Customer'

    def customer_email(self, obj):
        return obj.customer.email
    customer_email.short_description = 'Email'

    def status_display(self, obj):
        colors = {
            'pending': 'orange',
            'confirmed': 'blue',
            'in_progress': 'purple',
            'completed': 'green',
            'cancelled': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'

    def total_amount_display(self, obj):
        amount = obj.total_amount or obj.service.price
        return f"₹{amount}"
    total_amount_display.short_description = 'Amount'

    def payment_status(self, obj):
        if obj.is_paid:
            return format_html('<span style="color: green; font-weight: bold;">✓ Paid</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">✗ Unpaid</span>')
    payment_status.short_description = 'Payment'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('service', 'customer', 'provider', 'service__category')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('booking', 'rating', 'created_at', 'updated_at')
    list_filter = ('rating', 'created_at')
    search_fields = (
        'booking__service__name',
        'booking__customer__email',
        'booking__customer__first_name',
        'booking__customer__last_name',
        'comment',
    )
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    raw_id_fields = ('booking',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('booking__service', 'booking__customer')


@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'is_verified', 'is_available', 'created_at')
    list_filter = ('is_verified', 'is_available', 'created_at')
    search_fields = (
        'user__email',
        'user__first_name',
        'user__last_name',
        'company_name',
        'phone_number',
    )
    list_editable = ('is_verified', 'is_available')
    readonly_fields = ('created_at', 'updated_at', 'profile_picture_preview')
    raw_id_fields = ('user',)
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('user', 'company_name', 'description')
        }),
        ('Contact Information', {
            'fields': ('address', 'phone_number')
        }),
        ('Status', {
            'fields': ('is_verified', 'is_available')
        }),
        ('Media', {
            'fields': ('profile_picture', 'profile_picture_preview', 'banner_image')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return format_html(
                '<img src="{}" width="150" height="150" style="object-fit: cover;" />',
                obj.profile_picture.url
            )
        return "No image"
    profile_picture_preview.short_description = 'Preview'
