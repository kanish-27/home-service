from django import forms
from django.forms import ModelForm
from .models import Service, ServiceImage, Booking, Review, ProviderSchedule, ServiceCategory
from users.models import User
from django.utils import timezone

class ServiceForm(ModelForm):
    provider = forms.ModelChoiceField(
        queryset=User.objects.filter(user_type='provider'),
        empty_label="Select Provider",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Service
        fields = ['name', 'category', 'provider', 'description', 'price', 'duration', 'image', 'is_active', 'is_available']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Service name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Service description'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price in ₹', 'min': 0}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Duration in hours', 'min': 1}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = ServiceCategory.objects.all()
        self.fields['category'].widget.attrs.update({'class': 'form-control'})

        # Add help text
        self.fields['price'].help_text = 'Enter price in Indian Rupees (₹)'
        self.fields['duration'].help_text = 'Expected service duration in hours (e.g., 2 for 2 hours)'


class ServiceCategoryForm(ModelForm):
    class Meta:
        model = ServiceCategory
        fields = ['name', 'slug', 'description', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category name'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'URL slug (e.g., electrical)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Category description'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].help_text = 'URL-friendly version of the name (lowercase, no spaces)'


class ServiceImageForm(forms.ModelForm):
    class Meta:
        model = ServiceImage
        fields = ['image', 'caption', 'is_primary', 'order']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'caption': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Image caption (optional)'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'Display order'}),
        }


# Note: MultipleImageUploadForm removed due to Django FileInput limitations
# We'll handle multiple image uploads directly in the template and view


class BookingForm(ModelForm):
    class Meta:
        model = Booking
        fields = ['booking_date', 'address', 'phone_number', 'special_instructions']
        widgets = {
            'booking_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Your address'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your phone number'}),
            'special_instructions': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Any special instructions'}),
        }

    def __init__(self, *args, **kwargs):
        self.service = kwargs.pop('service', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Set minimum date to today
        today = timezone.now().strftime('%Y-%m-%dT%H:%M')
        self.fields['booking_date'].widget.attrs['min'] = today

        # Set initial phone number from user's profile if available
        if self.user and hasattr(self.user, 'phone_number'):
            self.fields['phone_number'].initial = self.user.phone_number

    def clean_booking_date(self):
        booking_date = self.cleaned_data.get('booking_date')

        if not booking_date:
            raise forms.ValidationError("Please select a booking date and time.")


class RescheduleBookingForm(forms.Form):
    booking_date = forms.DateTimeField(
        label='New Booking Date & Time',
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control',
            'required': True
        }),
        help_text='Select a new date and time for your booking.'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set minimum date to today
        today = timezone.now().strftime('%Y-%m-%dT%H:%M')
        self.fields['booking_date'].widget.attrs['min'] = today

        # Add Bootstrap classes
        self.fields['booking_date'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Select date and time'
        })

    def clean_booking_date(self):
        booking_date = self.cleaned_data.get('booking_date')

        if booking_date:
            # Ensure the booking date is in the future
            if booking_date <= timezone.now():
                raise forms.ValidationError('Booking date must be in the future.')

            # Ensure booking is not too far in the future (e.g., 1 year)
            max_date = timezone.now() + timezone.timedelta(days=365)
            if booking_date > max_date:
                raise forms.ValidationError('Booking date cannot be more than 1 year in the future.')

        return booking_date


class ProviderScheduleForm(forms.ModelForm):
    """Form for managing provider's schedule."""
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    day_of_week = forms.ChoiceField(
        choices=DAYS_OF_WEEK,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )
    is_working_day = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = ProviderSchedule
        fields = ['day_of_week', 'start_time', 'end_time', 'is_working_day']

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        is_working_day = cleaned_data.get('is_working_day', True)

        if is_working_day and (not start_time or not end_time):
            raise forms.ValidationError("Start time and end time are required for working days.")

        if is_working_day and start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("End time must be after start time.")

        return cleaned_data


class ReviewForm(ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'step': 0.5}),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating < 0.5 or rating > 5:
            raise forms.ValidationError("Rating must be between 0.5 and 5.")
        return rating
