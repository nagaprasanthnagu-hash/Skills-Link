from django import forms

from apps.customers.models import CustomerProfile


class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = CustomerProfile
        fields = ['phone', 'default_address']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 9876543210'}),
            'default_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Default service address (optional)'}),
        }
        error_messages = {
            'phone': {'invalid': 'Please enter a valid phone number.'},
        }
