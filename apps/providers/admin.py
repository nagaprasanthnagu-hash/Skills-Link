from django.contrib import admin

from apps.providers.models import ProviderProfile, ProviderTag, WorkPhoto


@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'experience_years', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('user__username', 'user__email')


@admin.register(ProviderTag)
class ProviderTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'provider__user__username')


@admin.register(WorkPhoto)
class WorkPhotoAdmin(admin.ModelAdmin):
    list_display = ('provider', 'booking', 'caption', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('provider__user__username', 'caption')
