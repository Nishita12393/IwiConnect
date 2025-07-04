from django import forms
from .models import CustomUser, Iwi, Hapu

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'required': True,
            'minlength': 8,
            'maxlength': 128,
            'class': 'form-control',
            'autocomplete': 'new-password',
        }),
        min_length=8,
        max_length=128,
        help_text='Password must be at least 8 characters.'
    )
    citizenship_document = forms.FileField(
        required=True,
        help_text='Upload a PDF, JPG, or PNG (max 2MB).',
        widget=forms.ClearableFileInput(attrs={
            'accept': '.pdf,.jpg,.jpeg,.png',
            'required': True,
            'class': 'form-control',
        })
    )

    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'password', 'iwi', 'hapu', 'citizenship_document']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'required': True,
                'minlength': 2,
                'maxlength': 100,
                'class': 'form-control',
            }),
            'email': forms.EmailInput(attrs={
                'required': True,
                'maxlength': 254,
                'class': 'form-control',
                'autocomplete': 'email',
            }),
            'iwi': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'hapu': forms.Select(attrs={'class': 'form-select'}),
        }
        help_texts = {
            'full_name': 'Enter your full name (2-100 characters).',
            'email': 'Enter a valid email address.',
        }

    def clean_citizenship_document(self):
        doc = self.cleaned_data.get('citizenship_document')
        if doc:
            if doc.size > 2 * 1024 * 1024:
                raise forms.ValidationError('File size must be under 2MB.')
            valid_types = ['application/pdf', 'image/jpeg', 'image/png']
            if hasattr(doc, 'content_type') and doc.content_type not in valid_types:
                raise forms.ValidationError('Only PDF, JPG, or PNG files are allowed.')
        return doc

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if len(email) > 254:
                raise forms.ValidationError('Email must be 254 characters or fewer.')
            if CustomUser.objects.filter(email=email).exists():
                raise forms.ValidationError('This email is already registered.')
        return email

    def clean_full_name(self):
        name = self.cleaned_data.get('full_name')
        if name:
            if len(name) < 2 or len(name) > 100:
                raise forms.ValidationError('Full name must be between 2 and 100 characters.')
        return name

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            if len(password) < 8 or len(password) > 128:
                raise forms.ValidationError('Password must be between 8 and 128 characters.')
        return password

class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'required': True,
            'maxlength': 254,
            'class': 'form-control',
            'autocomplete': 'email',
        }),
        max_length=254,
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'required': True,
            'minlength': 8,
            'maxlength': 128,
            'class': 'form-control',
            'autocomplete': 'current-password',
        }),
        min_length=8,
        max_length=128,
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and len(email) > 254:
            raise forms.ValidationError('Email must be 254 characters or fewer.')
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password and (len(password) < 8 or len(password) > 128):
            raise forms.ValidationError('Password must be between 8 and 128 characters.')
        return password

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email',
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if len(email) > 254:
                raise forms.ValidationError('Email must be 254 characters or fewer.')
            if not CustomUser.objects.filter(email=email, state='VERIFIED').exists():
                raise forms.ValidationError('No verified account found with this email address.')
        return email

class SetPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password',
            'autocomplete': 'new-password',
        }),
        min_length=8,
        max_length=128,
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password',
        }),
        min_length=8,
        max_length=128,
    )

    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        if password and (len(password) < 8 or len(password) > 128):
            raise forms.ValidationError('Password must be between 8 and 128 characters.')
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('The two password fields do not match.')
        return cleaned_data 