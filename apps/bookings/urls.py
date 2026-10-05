from django.urls import path

from apps.bookings import views

app_name = 'bookings'

urlpatterns = [
    path('create/', views.BookingCreateView.as_view(), name='create'),
    path('', views.BookingHistoryView.as_view(), name='history'),
    path('<int:pk>/', views.BookingDetailView.as_view(), name='detail'),
    path('<int:pk>/cancel/', views.booking_cancel_view, name='cancel'),
    path('<int:pk>/accept/', views.booking_accept_view, name='accept'),
    path('<int:pk>/status/', views.booking_status_update_view, name='status_update'),
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
]
