from django import forms

from apps.categories.models import ServiceCategory


class ServiceCategoryForm(forms.ModelForm):
    class Meta:
        model = ServiceCategory
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Plumbing'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        error_messages = {
            'name': {
                'required': 'Please enter a category name.',
                'unique': 'A category with this name already exists.',
                'max_length': 'Category name is too long.',
            },
        }
