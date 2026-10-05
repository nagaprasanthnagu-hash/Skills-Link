from django import forms

from apps.categories.models import ServiceCategory
from apps.providers.models import ProviderProfile, ProviderTag, TAG_NAME_MAX_LENGTH, WorkPhoto, normalize_tag

# Generous input ceiling — a provider may type '#', spaces, or extra
# punctuation that normalize_tag() strips out, so the raw input allowance is
# larger than the 40-char stored/normalized limit.
_TAG_INPUT_MAX_LENGTH = 60


class ProviderProfileForm(forms.ModelForm):
    class Meta:
        model = ProviderProfile
        fields = ['category', 'experience_years', 'bio', 'profile_photo']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 60}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Tell customers about your experience (optional)'}),
            'profile_photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        error_messages = {
            'category': {'required': 'Please select your service category.'},
            'experience_years': {'invalid': 'Please enter a valid number of years.'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = ServiceCategory.objects.filter(is_active=True)
        self.fields['category'].required = True

    def clean_experience_years(self):
        years = self.cleaned_data['experience_years']
        if years < 0 or years > 60:
            raise forms.ValidationError('Please enter a valid number of years.')
        return years


class ProviderTagForm(forms.ModelForm):
    """Add/edit one provider service tag (Provider Service Tag / Hashtag
    Search System, Section 5/6). The provider may type '#fan', 'Fan',
    '#FAN', or 'fan' — normalize_tag() (server-side, in clean_name) decides
    the single canonical stored value, so all of those are treated as the
    same tag. `provider` must always be passed in by the view — it is never
    taken from the form/POST data, since a hidden/spoofed provider field
    must never be trusted for ownership (Section 7)."""
    name = forms.CharField(
        max_length=_TAG_INPUT_MAX_LENGTH,
        label='Service tag',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. #fanrepair'}),
        help_text="Letters and numbers only — the # is optional and case doesn't matter.",
    )

    class Meta:
        model = ProviderTag
        fields = ['name']

    def __init__(self, *args, provider=None, **kwargs):
        self.provider = provider
        super().__init__(*args, **kwargs)

    def clean_name(self):
        normalized = normalize_tag(self.cleaned_data.get('name', ''))
        if not normalized:
            raise forms.ValidationError('Please enter a valid tag using letters and numbers (e.g. "fan" or "#fanrepair").')
        if len(normalized) > TAG_NAME_MAX_LENGTH:
            raise forms.ValidationError(f'Tags must be {TAG_NAME_MAX_LENGTH} characters or fewer once normalized.')

        existing = ProviderTag.objects.filter(provider=self.provider, name=normalized)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise forms.ValidationError('You already have this tag.')
        return normalized

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.provider = self.provider
        if commit:
            instance.save()
        return instance


class WorkPhotoForm(forms.ModelForm):
    """One caption applies to the whole batch of images uploaded together
    (the view creates one WorkPhoto row per file — see WorkPhotoUploadView).
    The actual multi-file input is handled directly from request.FILES since
    a single ImageField can't natively accept more than one file."""
    class Meta:
        model = WorkPhoto
        fields = ['caption']
        widgets = {
            'caption': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Caption (optional) — e.g. "Kitchen pipe replacement"'}),
        }
