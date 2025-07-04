from django import forms
from .models import Notice
from core.models import Iwi, Hapu
from django.utils import timezone

class NoticeForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'required': True, 'minlength': 10, 'maxlength': 2000}),
        label='Content',
        min_length=10,
        max_length=2000,
    )
    expiry_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control', 'required': True}),
        required=True
    )
    attachment = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
        help_text='Upload a PDF, JPG, or PNG (max 2MB).'
    )

    def clean(self):
        cleaned_data = super().clean()
        audience = cleaned_data.get('audience')
        iwi = cleaned_data.get('iwi')
        hapu = cleaned_data.get('hapu')
        errors = {}
        if audience == 'ALL':
            if iwi or hapu:
                errors['iwi'] = 'Iwi must be empty when audience is All Users.'
                errors['hapu'] = 'Hapu must be empty when audience is All Users.'
        elif audience == 'IWI':
            if not iwi:
                errors['iwi'] = 'Iwi is required when audience is Specific Iwi.'
            if hapu:
                errors['hapu'] = 'Hapu must be empty when audience is Specific Iwi.'
        elif audience == 'HAPU':
            if not iwi:
                errors['iwi'] = 'Iwi is required when audience is Specific Hapu.'
            if not hapu:
                errors['hapu'] = 'Hapu is required when audience is Specific Hapu.'
        expiry = cleaned_data.get('expiry_date')
        if expiry and expiry <= timezone.now():
            errors['expiry_date'] = 'Expiry date must be in the future.'
        if errors:
            raise forms.ValidationError(errors)
        return cleaned_data

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title and (len(title) < 5 or len(title) > 200):
            raise forms.ValidationError('Title must be between 5 and 200 characters.')
        return title

    def clean_content(self):
        content = self.cleaned_data.get('content')
        if content and (len(content) < 10 or len(content) > 2000):
            raise forms.ValidationError('Content must be between 10 and 2000 characters.')
        return content

    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            if attachment.size > 2 * 1024 * 1024:
                raise forms.ValidationError('File size must be under 2MB.')
            valid_types = ['application/pdf', 'image/jpeg', 'image/png']
            if hasattr(attachment, 'content_type') and attachment.content_type not in valid_types:
                raise forms.ValidationError('Only PDF, JPG, or PNG files are allowed.')
        return attachment

    def clean_priority(self):
        priority = self.cleaned_data.get('priority')
        if priority is not None and (priority < 1 or priority > 10):
            raise forms.ValidationError('Priority must be between 1 and 10.')
        return priority

    class Meta:
        model = Notice
        fields = ['title', 'content', 'attachment', 'expiry_date', 'audience', 'iwi', 'hapu', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'minlength': 5, 'maxlength': 200}),
            'audience': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'iwi': forms.Select(attrs={'class': 'form-select'}),
            'hapu': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10, 'required': True}),
        }
        help_texts = {
            'title': 'Enter a title (5-200 characters).',
            'content': 'Enter the notice content (10-2000 characters).',
            'priority': 'Priority from 1 (lowest) to 10 (highest).',
        } 