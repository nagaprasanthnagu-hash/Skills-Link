from django import forms

from apps.reviews.models import Review

RATING_CHOICES = [(i, f'{i} \u2605') for i in range(1, 6)]


class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        error_messages={'required': 'Please select a rating from 1 to 5.'},
    )

    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional comment (max 500 characters)'}),
        }
        error_messages = {
            'comment': {'max_length': 'Comment is too long (max 500 characters).'},
        }
