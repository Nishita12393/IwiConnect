from django import forms
from core.models import Iwi

class IwiForm(forms.ModelForm):
    """Form for creating and editing iwis"""
    
    class Meta:
        model = Iwi
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter iwi name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter iwi description (optional)'
            })
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        # Check for duplicate names, excluding the current instance if editing
        if self.instance.pk:
            if Iwi.objects.filter(name=name, is_archived=False).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError('An iwi with this name already exists.')
        else:
            if Iwi.objects.filter(name=name, is_archived=False).exists():
                raise forms.ValidationError('An iwi with this name already exists.')
        return name

class IwiArchiveForm(forms.Form):
    """Form for archiving/unarchiving iwis"""
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Reason for archiving (optional)'
        }),
        required=False,
        max_length=500
    ) 