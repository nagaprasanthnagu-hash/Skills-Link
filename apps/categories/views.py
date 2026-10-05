from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from apps.categories.forms import ServiceCategoryForm
from apps.categories.models import ServiceCategory
from apps.core.mixins import RoleRequiredMixin


class CategoryListView(ListView):
    """Category listing visible to everyone; only active categories."""
    model = ServiceCategory
    template_name = 'categories/list.html'
    context_object_name = 'categories'
    paginate_by = 12

    def get_queryset(self):
        return ServiceCategory.objects.filter(is_active=True)


class CategoryDetailView(DetailView):
    model = ServiceCategory
    template_name = 'categories/detail.html'
    context_object_name = 'category'

    def get_queryset(self):
        return ServiceCategory.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.providers.models import ProviderProfile
        context['providers'] = ProviderProfile.objects.filter(
            category=self.object, is_active=True,
        ).select_related('user')
        return context


class CategoryManageListView(RoleRequiredMixin, ListView):
    allowed_roles = ['admin']
    model = ServiceCategory
    template_name = 'categories/admin_list.html'
    context_object_name = 'categories'
    paginate_by = 20

    def get_queryset(self):
        return ServiceCategory.objects.all()


class CategoryCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ['admin']
    model = ServiceCategory
    form_class = ServiceCategoryForm
    template_name = 'categories/admin_form.html'
    success_url = reverse_lazy('categories:manage_list')

    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" created successfully.')
        return super().form_valid(form)


class CategoryUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = ['admin']
    model = ServiceCategory
    form_class = ServiceCategoryForm
    template_name = 'categories/admin_form.html'
    success_url = reverse_lazy('categories:manage_list')

    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" updated successfully.')
        return super().form_valid(form)


class CategoryDeactivateView(RoleRequiredMixin, View):
    allowed_roles = ['admin']

    def post(self, request, pk):
        category = get_object_or_404(ServiceCategory, pk=pk)
        category.is_active = not category.is_active
        category.save(update_fields=['is_active'])
        state = 'activated' if category.is_active else 'deactivated'
        messages.success(request, f'Category "{category.name}" {state}.')
        return redirect('categories:manage_list')
