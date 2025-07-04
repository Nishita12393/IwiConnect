from django import forms
from .models import Event
from django.utils import timezone

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'start_datetime', 'end_datetime', 'location', 'visibility', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'minlength': 5, 'maxlength': 200}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'required': True, 'minlength': 10, 'maxlength': 2000}),
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control', 'required': True}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control', 'required': True}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'minlength': 2, 'maxlength': 200}),
            'visibility': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.jpg,.jpeg,.png'}),
        }
        help_texts = {
            'title': 'Enter a title (5-200 characters).',
            'description': 'Describe the event (10-2000 characters).',
            'location': 'Enter the event location (2-200 characters).',
        }

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title and (len(title) < 5 or len(title) > 200):
            raise forms.ValidationError('Title must be between 5 and 200 characters.')
        return title

    def clean_description(self):
        desc = self.cleaned_data.get('description')
        if desc and (len(desc) < 10 or len(desc) > 2000):
            raise forms.ValidationError('Description must be between 10 and 2000 characters.')
        return desc

    def clean_location(self):
        loc = self.cleaned_data.get('location')
        if loc and (len(loc) < 2 or len(loc) > 200):
            raise forms.ValidationError('Location must be between 2 and 200 characters.')
        return loc

    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            if not attachment.content_type.startswith('image/'):
                raise forms.ValidationError('Only image files are allowed.')
            if attachment.size > 2 * 1024 * 1024:
                raise forms.ValidationError('Image file size must be under 2MB.')
        return attachment

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_datetime')
        end = cleaned_data.get('end_datetime')
        if start and end:
            if end <= start:
                self.add_error('end_datetime', 'End date/time must be after start date/time.')
            if start < timezone.now():
                self.add_error('start_datetime', 'Start date/time cannot be in the past.')
        return cleaned_data 