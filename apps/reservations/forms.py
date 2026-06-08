from django import forms
from .models import Reservation


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['name', 'phone', 'email', 'visit_date', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'eden-input', 'placeholder': 'Votre nom complet'}),
            'phone': forms.TextInput(attrs={'class': 'eden-input', 'placeholder': '+237 6XX XXX XXX'}),
            'email': forms.EmailInput(attrs={'class': 'eden-input', 'placeholder': 'email@exemple.com'}),
            'visit_date': forms.DateInput(attrs={'class': 'eden-input', 'type': 'date'}),
            'message': forms.Textarea(attrs={'class': 'eden-input', 'rows': 4, 'placeholder': 'Précisez vos besoins...'}),
        }
        labels = {
            'name': 'Nom complet',
            'phone': 'Téléphone',
            'email': 'Email',
            'visit_date': 'Date souhaitée',
            'message': 'Message',
        }