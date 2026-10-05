from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from apps.accounts import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('post-login-redirect/', views.post_login_redirect, name='post_login_redirect'),
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset/verify/', views.PasswordResetVerifyView.as_view(), name='password_reset_verify'),
    path('profile/', views.profile_view, name='profile'),
    # Authenticated "I know my current password and want to change it" flow —
    # separate from the OTP-based Forgot Password flow above, which is
    # untouched. Uses Django's own built-in auth views/form as-is (no
    # custom view/form needed): PasswordChangeView already enforces
    # login_required (via settings.LOGIN_URL), validates old_password
    # against the user's real hash, applies the project's configured
    # AUTH_PASSWORD_VALIDATORS to the new password, and keeps the user
    # logged in afterwards (update_session_auth_hash), which is Django's
    # standard, expected behavior for this flow.
    path(
        'profile/change-password/',
        auth_views.PasswordChangeView.as_view(
            template_name='accounts/change_password.html',
            success_url=reverse_lazy('accounts:change_password_done'),
        ),
        name='change_password',
    ),
    path(
        'profile/change-password/done/',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='accounts/change_password_done.html',
        ),
        name='change_password_done',
    ),
]
