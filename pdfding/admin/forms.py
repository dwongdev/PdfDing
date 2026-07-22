from allauth.account.adapter import get_adapter
from allauth.account.internal.flows.manage_email import email_already_exists
from django import forms
from django.utils.translation import gettext_lazy as _


class CreateUserForm(forms.Form):
    """The form for changing the email address."""

    email = forms.CharField(
        required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Email')})
    )
    password = forms.CharField(
        required=True, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Password')})
    )
    password2 = forms.CharField(
        required=True, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Password (again)')})
    )

    def __init__(self, *args, **kwargs):
        """Needed to be compatible with BaseAdd."""

        self.profile = kwargs.pop('profile', None)

        super().__init__(*args, **kwargs)

    def clean_email(self) -> str:
        email = self.cleaned_data['email'].lower()
        email = get_adapter().clean_email(email)
        if email:
            email, __ = email_already_exists(email)
        return email

    def clean_password2(self) -> str:
        password = self.cleaned_data['password']
        password2 = self.cleaned_data['password2']

        if password2 != password:
            raise forms.ValidationError(_('You must type the same password each time.'))

        return password2
