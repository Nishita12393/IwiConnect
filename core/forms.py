from django import forms
from .models import CustomUser, Iwi, Hapu

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    citizenship_document = forms.FileField(required=True, help_text='Max size: 2MB')

    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'password', 'iwi', 'hapu', 'citizenship_document']

    def clean_citizenship_document(self):
        doc = self.cleaned_data.get('citizenship_document')
        if doc and doc.size > 2 * 1024 * 1024:
            raise forms.ValidationError('File size must be under 2MB.')
        return doc

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput) 