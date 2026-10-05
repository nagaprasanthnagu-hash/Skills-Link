from django.urls import path

from apps.reviews import views

app_name = 'reviews'

urlpatterns = [
    path('<int:booking_id>/create/', views.ReviewCreateView.as_view(), name='create'),
    path('provider/<int:provider_id>/', views.ProviderReviewListView.as_view(), name='provider_reviews'),
]
