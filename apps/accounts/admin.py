from django.contrib import admin

from apps.accounts.models import PasswordResetOTP, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'role', 'created_at')
    list_filter = ('role',)
    search_fields = ('full_name', 'user__username', 'user__email')


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at', 'is_used')
    list_filter = ('is_used',)
    readonly_fields = ('otp_code', 'created_at')
