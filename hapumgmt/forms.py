from django import forms
from core.models import Hapu, Iwi

class HapuForm(forms.ModelForm):
    class Meta:
        model = Hapu
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.iwi_field_visible = False
        self.iwi = None
        if user:
            user_iwis = Iwi.objects.filter(leaders__user=user, is_archived=False)
            if user_iwis.count() > 1:
                self.fields['iwi'] = forms.ModelChoiceField(
                    queryset=user_iwis,
                    widget=forms.Select(attrs={'class': 'form-control'}),
                    empty_label="Select an Iwi"
                )
                self.iwi_field_visible = True
            elif user_iwis.count() == 1:
                self.iwi = user_iwis.first()
                if 'iwi' in self.fields:
                    del self.fields['iwi']

class HapuArchiveForm(forms.Form):
    confirm_archive = forms.BooleanField(
        required=True,
        label="I confirm that I want to archive this hapu",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class HapuTransferForm(forms.Form):
    new_iwi = forms.ModelChoiceField(
        queryset=Iwi.objects.filter(is_archived=False),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select a new Iwi",
        label="Transfer to Iwi"
    )
    confirm_transfer = forms.BooleanField(
        required=True,
        label="I confirm that I want to transfer this hapu to the selected iwi",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        current_iwi = kwargs.pop('current_iwi', None)
        super().__init__(*args, **kwargs)
        if current_iwi:
            # Exclude the current iwi from the choices
            self.fields['new_iwi'].queryset = Iwi.objects.filter(is_archived=False).exclude(pk=current_iwi.pk) 