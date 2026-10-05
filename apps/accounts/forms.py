import re

from django import forms
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

from apps.accounts.models import UserProfile
from apps.customers.models import PHONE_VALIDATOR

USERNAME_VALIDATOR = RegexValidator(
    regex=r'^[A-Za-z0-9_]{3,30}$',
    message='Username must be 3-30 characters and contain only letters, numbers, and underscores.',
)


class RegistrationForm(forms.Form):
    """Combined registration form with role selection (Section 62.2)."""
    ROLE_CHOICES = [
        (UserProfile.ROLE_CUSTOMER, 'Customer — I need a service'),
        (UserProfile.ROLE_PROVIDER, 'Service Provider — I offer a service'),
    ]

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect,
        error_messages={'required': 'Please select an account type.'},
    )
    category = forms.ModelChoiceField(
        queryset=None,
        required=False,
        error_messages={'required': 'Please select your service category.'},
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    full_name = forms.CharField(
        min_length=2, max_length=100,
        error_messages={'required': 'Please enter your full name.'},
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
    )
    username = forms.CharField(
        validators=[USERNAME_VALIDATOR],
        error_messages={'required': 'Please choose a username.'},
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
    )
    email = forms.EmailField(
        error_messages={'required': 'Please enter your email address.', 'invalid': 'Please enter a valid email address.'},
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
    )
    phone = forms.CharField(
        required=False,
        validators=[PHONE_VALIDATOR],
        error_messages={'invalid': 'Please enter a valid phone number.'},
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact number (optional)'}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        error_messages={'required': 'Please enter a password.'},
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
        error_messages={'required': 'Please confirm your password.'},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.categories.models import ServiceCategory
        self.fields['category'].queryset = ServiceCategory.objects.filter(is_active=True)

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def clean_password(self):
        password = self.cleaned_data['password']
        if len(password) < 8 or not re.search(r'\d', password):
            raise forms.ValidationError('Password must be at least 8 characters and include a number.')
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data


class LoginForm(forms.Form):
    """Login by username or registered email (Section 62.1)."""
    username_or_email = forms.CharField(
        label='Username or email',
        error_messages={'required': 'Please enter your username or email.'},
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username or email', 'autofocus': True}),
    )
    password = forms.CharField(
        error_messages={'required': 'Please enter your password.'},
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
    )
    remember_me = forms.BooleanField(required=False, label='Remember me')


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        error_messages={'required': 'Please enter your registered email address.'},
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Registered email address'}),
    )


class PasswordResetVerifyForm(forms.Form):
    otp_code = forms.CharField(
        label='OTP code', max_length=6, min_length=6,
        error_messages={'required': 'Please enter the OTP sent to your email.'},
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '6-digit OTP'}),
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New password'}),
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'}),
    )

    def clean_new_password(self):
        password = self.cleaned_data['new_password']
        if len(password) < 8 or not re.search(r'\d', password):
            raise forms.ValidationError('Password must be at least 8 characters and include a number.')
        return password

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('new_password') != cleaned_data.get('confirm_password'):
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data


class AccountProfileForm(forms.ModelForm):
    """Common profile fields shared by every role (Section 62.4)."""
    class Meta:
        model = UserProfile
        fields = ['full_name']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
        error_messages = {
            'full_name': {'required': 'Please enter your full name.'},
        }
