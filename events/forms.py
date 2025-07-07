from django import forms
from .models import Event
from django.utils import timezone
from core.models import Iwi, Hapu
from django.db import models

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'start_datetime', 'end_datetime', 'location_type', 'location', 'online_url', 'visibility', 'iwi', 'hapu', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'minlength': 5, 'maxlength': 200}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'required': True, 'minlength': 10, 'maxlength': 2000}),
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control', 'required': True}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control', 'required': True}),
            'location_type': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'minlength': 2, 'maxlength': 200}),
            'online_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/meeting'}),
            'visibility': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'iwi': forms.Select(attrs={'class': 'form-select'}),
            'hapu': forms.Select(attrs={'class': 'form-select'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.jpg,.jpeg,.png'}),
        }
        help_texts = {
            'title': 'Enter a title (5-200 characters).',
            'description': 'Describe the event (10-2000 characters).',
            'location_type': 'Choose whether this is a physical or online event.',
            'location': 'Enter the physical address or venue name (required for physical events).',
            'online_url': 'Enter the URL for the online event (required for online events).',
            'visibility': 'Choose the visibility level for this event.',
            'iwi': 'Select a specific iwi for iwi-specific events.',
            'hapu': 'Select a specific hapu for hapu-specific events.',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Set up iwi and hapu querysets based on user permissions
            if user.is_staff:
                # Admin can select any iwi or hapu
                self.fields['iwi'].queryset = Iwi.objects.filter(is_archived=False)
                self.fields['hapu'].queryset = Hapu.objects.filter(is_archived=False)
            else:
                # Regular users can only select iwis/hapus they lead
                iwi_ids = list(user.iwi_leaderships.values_list('iwi_id', flat=True))
                hapu_ids = list(user.hapu_leaderships.values_list('hapu_id', flat=True))
                
                if iwi_ids:
                    self.fields['iwi'].queryset = Iwi.objects.filter(id__in=iwi_ids, is_archived=False)
                    # For hapu selection, include hapus from iwis they lead
                    self.fields['hapu'].queryset = Hapu.objects.filter(
                        models.Q(id__in=hapu_ids) | models.Q(iwi_id__in=iwi_ids),
                        is_archived=False
                    )
                elif hapu_ids:
                    # Only hapu leader
                    self.fields['iwi'].queryset = Iwi.objects.none()
                    self.fields['hapu'].queryset = Hapu.objects.filter(id__in=hapu_ids, is_archived=False)
                else:
                    # No leadership permissions
                    self.fields['iwi'].queryset = Iwi.objects.none()
                    self.fields['hapu'].queryset = Hapu.objects.none()

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
        location_type = self.cleaned_data.get('location_type')
        
        if location_type == 'PHYSICAL':
            if not loc or len(loc.strip()) == 0:
                raise forms.ValidationError('Location is required for physical events.')
            if len(loc) < 2 or len(loc) > 200:
                raise forms.ValidationError('Location must be between 2 and 200 characters.')
        return loc

    def clean_online_url(self):
        online_url = self.cleaned_data.get('online_url')
        location_type = self.cleaned_data.get('location_type')
        
        if location_type == 'ONLINE':
            if not online_url or len(online_url.strip()) == 0:
                raise forms.ValidationError('Online URL is required for online events.')
            if not online_url.startswith(('http://', 'https://')):
                raise forms.ValidationError('Please enter a valid URL starting with http:// or https://')
        return online_url

    def clean_visibility(self):
        visibility = self.cleaned_data.get('visibility')
        iwi = self.cleaned_data.get('iwi')
        hapu = self.cleaned_data.get('hapu')
        
        if visibility == 'IWI':
            if not iwi:
                raise forms.ValidationError('Iwi is required when visibility is Iwi-specific.')
            if hapu:
                raise forms.ValidationError('Hapu must be empty when visibility is Iwi-specific.')
        elif visibility == 'HAPU':
            if not hapu:
                raise forms.ValidationError('Hapu is required when visibility is Hapu-specific.')
            if not iwi:
                raise forms.ValidationError('Iwi is required when visibility is Hapu-specific.')
            if hapu.iwi != iwi:
                raise forms.ValidationError('Selected hapu must belong to the selected iwi.')
        elif visibility == 'PUBLIC':
            if iwi or hapu:
                raise forms.ValidationError('Iwi and hapu must be empty when visibility is Public.')
        
        return visibility

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