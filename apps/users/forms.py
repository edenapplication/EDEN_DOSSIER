from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Identifiant",
        widget=forms.TextInput(attrs={
            'class': 'eden-input',
            'placeholder': 'Votre identifiant'
        })
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'eden-input',
            'placeholder': '••••••••'
        })
    )


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'city']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'eden-input'}),
            'last_name': forms.TextInput(attrs={'class': 'eden-input'}),
            'email': forms.EmailInput(attrs={'class': 'eden-input'}),
            'phone': forms.TextInput(attrs={'class': 'eden-input'}),
            'city': forms.TextInput(attrs={'class': 'eden-input'}),
        }