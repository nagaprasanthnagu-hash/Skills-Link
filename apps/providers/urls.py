from django.urls import path

from apps.providers import views

app_name = 'providers'

urlpatterns = [
    path('dashboard/', views.ProviderDashboardView.as_view(), name='dashboard'),
    path('profile/setup/', views.ProviderProfileSetupView.as_view(), name='profile_setup'),
    path('tags/', views.ProviderTagListView.as_view(), name='tags'),
    path('tags/<int:pk>/edit/', views.ProviderTagEditView.as_view(), name='tag_edit'),
    path('tags/<int:pk>/delete/', views.provider_tag_delete_view, name='tag_delete'),
    path('bookings/<int:booking_id>/work-photos/', views.WorkPhotoUploadView.as_view(), name='work_photo_upload'),
    path('work-photos/<int:pk>/delete/', views.work_photo_delete_view, name='work_photo_delete'),
]
