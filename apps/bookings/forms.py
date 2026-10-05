from django import forms
from django.utils import timezone

from apps.bookings.models import Booking
from apps.categories.models import ServiceCategory


class BookingForm(forms.ModelForm):
    """Booking creation form (Section 62.3)."""

    class Meta:
        model = Booking
        fields = ['category', 'preferred_datetime', 'address', 'description']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'preferred_datetime': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M',
            ),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Service address'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the issue (10-1000 characters)'}),
        }
        error_messages = {
            'category': {'required': 'Please select a valid service category.'},
            'preferred_datetime': {'required': 'Please choose a future date and time.'},
            'address': {'required': 'Please enter the service address.'},
            'description': {'required': 'Please describe the issue (10-1000 characters).'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = ServiceCategory.objects.filter(is_active=True)
        self.fields['preferred_datetime'].input_formats = ['%Y-%m-%dT%H:%M']

    def clean_preferred_datetime(self):
        value = self.cleaned_data['preferred_datetime']
        if value < timezone.now():
            raise forms.ValidationError('Please choose a future date and time.')
        return value

    def clean_address(self):
        address = self.cleaned_data['address'].strip()
        if len(address) < 5 or len(address) > 255:
            raise forms.ValidationError('Please enter the service address (5-255 characters).')
        return address

    def clean_description(self):
        description = self.cleaned_data['description'].strip()
        if len(description) < 10 or len(description) > 1000:
            raise forms.ValidationError('Please describe the issue (10-1000 characters).')
        return description
