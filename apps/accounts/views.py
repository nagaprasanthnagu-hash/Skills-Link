import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View

from apps.accounts.forms import (
    AccountProfileForm,
    LoginForm,
    PasswordResetRequestForm,
    PasswordResetVerifyForm,
    RegistrationForm,
)
from apps.accounts.models import PasswordResetOTP, UserProfile
from apps.core.middleware import clear_failed_login, record_failed_login
from apps.core.mixins import dashboard_url_for_role

logger = logging.getLogger('apps.accounts')


class RegisterView(View):
    template_name = 'accounts/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:post_login_redirect')
        return render(request, self.template_name, {'form': RegistrationForm()})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        data = form.cleaned_data
        with transaction.atomic():
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                first_name=data['full_name'].split(' ')[0],
            )
            profile = UserProfile.objects.create(
                user=user, full_name=data['full_name'], role=data['role'],
            )
            if data['role'] == UserProfile.ROLE_CUSTOMER:
                from apps.customers.models import CustomerProfile
                CustomerProfile.objects.create(user=user, phone=data.get('phone', ''))
            else:
                from apps.providers.models import ProviderProfile
                ProviderProfile.objects.create(user=user, category=data.get('category'))

        logger.info('New %s account registered: %s', profile.role, user.username)
        messages.success(request, 'Account created successfully. Please log in to continue.')
        return redirect('accounts:login')


class LoginView(View):
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:post_login_redirect')
        return render(request, self.template_name, {'form': LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        data = form.cleaned_data
        user = authenticate(request, username=data['username_or_email'], password=data['password'])

        if user is None:
            record_failed_login(request)
            messages.error(request, 'Invalid username/email or password.')
            return render(request, self.template_name, {'form': form})

        if not user.is_active:
            messages.error(request, 'This account is inactive — contact support.')
            return render(request, self.template_name, {'form': form})

        clear_failed_login(request)
        login(request, user)

        if data.get('remember_me'):
            request.session.set_expiry(1209600)  # 14 days
        else:
            request.session.set_expiry(0)  # expires on browser close

        return redirect('accounts:post_login_redirect')


@login_required(login_url='accounts:login')
def post_login_redirect(request):
    """Role-based redirect to the correct post-login dashboard (FR-A3)."""
    profile = getattr(request.user, 'userprofile', None)
    role = profile.role if profile else None
    return redirect(dashboard_url_for_role(role))


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')


class PasswordResetRequestView(View):
    template_name = 'accounts/password_reset.html'

    def get(self, request):
        return render(request, self.template_name, {'form': PasswordResetRequestForm()})

    def post(self, request):
        form = PasswordResetRequestForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        email = form.cleaned_data['email']
        user = User.objects.filter(email__iexact=email).first()
        # Always show the same confirmation, whether or not the email is
        # registered, to avoid leaking which emails have accounts.
        if user is not None:
            otp = PasswordResetOTP.issue_for(user)
            send_mail(
                subject='Your password reset OTP',
                message=(
                    f'Your one-time password is {otp.otp_code}. '
                    f'It expires in {otp.expires_at.strftime("%H:%M")} IST.'
                ),
                from_email=None,
                recipient_list=[email],
                fail_silently=True,
            )
            request.session['password_reset_user_id'] = user.id

        messages.success(request, 'If that email is registered, an OTP has been sent to it.')
        return redirect('accounts:password_reset_verify')


class PasswordResetVerifyView(View):
    template_name = 'accounts/password_reset_verify.html'

    def get(self, request):
        return render(request, self.template_name, {'form': PasswordResetVerifyForm()})

    def post(self, request):
        form = PasswordResetVerifyForm(request.POST)
        user_id = request.session.get('password_reset_user_id')

        if not user_id:
            messages.error(request, 'Please request a new OTP.')
            return redirect('accounts:password_reset')

        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        otp_code = form.cleaned_data['otp_code']
        otp = PasswordResetOTP.objects.filter(
            user_id=user_id, otp_code=otp_code, is_used=False,
        ).order_by('-created_at').first()

        if otp is None or not otp.is_valid():
            messages.error(request, 'This OTP is invalid or has expired. Please request a new one.')
            return redirect('accounts:password_reset')

        user = User.objects.get(id=user_id)
        user.set_password(form.cleaned_data['new_password'])
        user.save()
        otp.is_used = True
        otp.save(update_fields=['is_used'])
        del request.session['password_reset_user_id']

        messages.success(request, 'Password reset successfully. Please log in with your new password.')
        return redirect('accounts:login')


@login_required(login_url='accounts:login')
def profile_view(request):
    profile = request.user.userprofile
    account_form = AccountProfileForm(instance=profile)
    role_form = None

    if profile.role == UserProfile.ROLE_CUSTOMER:
        from apps.customers.forms import CustomerProfileForm
        customer_profile = request.user.customer_profile
        role_form = CustomerProfileForm(instance=customer_profile)
    elif profile.role == UserProfile.ROLE_PROVIDER:
        from apps.providers.forms import ProviderProfileForm
        provider_profile = request.user.provider_profile
        role_form = ProviderProfileForm(instance=provider_profile)

    if request.method == 'POST':
        account_form = AccountProfileForm(request.POST, instance=profile)
        forms_valid = account_form.is_valid()

        if profile.role == UserProfile.ROLE_CUSTOMER:
            from apps.customers.forms import CustomerProfileForm
            role_form = CustomerProfileForm(request.POST, instance=request.user.customer_profile)
            forms_valid = forms_valid and role_form.is_valid()
        elif profile.role == UserProfile.ROLE_PROVIDER:
            from apps.providers.forms import ProviderProfileForm
            role_form = ProviderProfileForm(request.POST, request.FILES, instance=request.user.provider_profile)
            forms_valid = forms_valid and role_form.is_valid()

        if forms_valid:
            account_form.save()
            if role_form is not None:
                role_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {
        'account_form': account_form,
        'role_form': role_form,
        'profile': profile,
    })
