from django.urls import path

from apps.categories import views

app_name = 'categories'

urlpatterns = [
    path('', views.CategoryListView.as_view(), name='list'),
    path('<int:pk>/', views.CategoryDetailView.as_view(), name='detail'),
    path('manage/', views.CategoryManageListView.as_view(), name='manage_list'),
    path('manage/create/', views.CategoryCreateView.as_view(), name='create'),
    path('manage/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='edit'),
    path('manage/<int:pk>/deactivate/', views.CategoryDeactivateView.as_view(), name='deactivate'),
]
