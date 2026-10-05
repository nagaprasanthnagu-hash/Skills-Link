from django.urls import path

from apps.customers import views

app_name = 'customers'

urlpatterns = [
    path('dashboard/', views.CustomerDashboardView.as_view(), name='dashboard'),
]
