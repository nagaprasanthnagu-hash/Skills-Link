from django.contrib import admin

from apps.bookings.models import Booking, BookingStatusLog


class BookingStatusLogInline(admin.TabularInline):
    model = BookingStatusLog
    extra = 0
    readonly_fields = ('old_status', 'new_status', 'changed_at')
    can_delete = False


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'provider', 'category', 'status', 'preferred_datetime', 'created_at')
    list_filter = ('status', 'category')
    search_fields = ('customer__user__username', 'provider__user__username', 'address')
    inlines = [BookingStatusLogInline]
    readonly_fields = ('created_at', 'updated_at')


@admin.register(BookingStatusLog)
class BookingStatusLogAdmin(admin.ModelAdmin):
    list_display = ('booking', 'old_status', 'new_status', 'changed_at')
    list_filter = ('new_status',)
