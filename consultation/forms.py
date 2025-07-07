from django import forms
from .models import Proposal, VotingOption
from core.models import Iwi, Hapu, CustomUser
from django.utils import timezone
from datetime import timedelta

class ProposalForm(forms.ModelForm):
    voting_options = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'required': True,
            'minlength': 5,
            'maxlength': 500,
        }),
        help_text='Enter one voting option per line (e.g., Yes, No, Abstain)',
        min_length=5,
        max_length=500,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter out archived iwis and hapus
        self.fields['iwi'].queryset = Iwi.objects.filter(is_archived=False).order_by('name')
        self.fields['hapu'].queryset = Hapu.objects.filter(is_archived=False).order_by('name')
    class Meta:
        model = Proposal
        fields = [
            'title', 'description', 'consultation_type', 'iwi', 'hapu',
            'start_date', 'end_date', 'enable_comments', 'anonymous_feedback', 'is_draft'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True,
                'minlength': 5,
                'maxlength': 200,
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'required': True,
                'minlength': 10,
                'maxlength': 2000,
            }),
            'consultation_type': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'iwi': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'hapu': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control', 'required': True}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control', 'required': True}),
            'enable_comments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'anonymous_feedback': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_draft': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'title': 'Enter a title (5-200 characters).',
            'description': 'Describe the consultation (10-2000 characters).',
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

    def clean_voting_options(self):
        options = self.cleaned_data.get('voting_options', '')
        option_list = [opt.strip() for opt in options.splitlines() if opt.strip()]
        if len(option_list) < 2:
            raise forms.ValidationError('At least two voting options are required.')
        return options

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if start_date:
            now = timezone.now()
            # Add a small buffer (1 minute) to account for form submission time
            if start_date <= now:
                raise forms.ValidationError('Consultation start date and time must be in the future.')
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        if end_date:
            now = timezone.now()
            # Add a small buffer (1 minute) to account for form submission time
            if end_date <= now:
                raise forms.ValidationError('Consultation end date and time must be in the future.')
        return end_date

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        
        if start and end:
            if end <= start:
                self.add_error('end_date', 'End date must be after start date.')
            
            # Ensure minimum consultation duration (e.g., 1 hour)
            min_duration = timedelta(hours=1)
            if end - start < min_duration:
                self.add_error('end_date', 'Consultation must last at least 1 hour.')
        
        # Validate that selected iwi and hapu are not archived
        iwi = cleaned_data.get('iwi')
        hapu = cleaned_data.get('hapu')
        
        if iwi and iwi.is_archived:
            self.add_error('iwi', 'Cannot create consultations for archived iwis.')
        
        if hapu and hapu.is_archived:
            self.add_error('hapu', 'Cannot create consultations for archived hapus.')
        
        return cleaned_data 