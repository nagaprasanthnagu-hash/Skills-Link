from django.urls import path

from apps.dashboard import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.AdminDashboardView.as_view(), name='index'),
    path('users/', views.UserManagementView.as_view(), name='users'),
    path('providers/', views.ProviderManagementView.as_view(), name='providers'),
]
