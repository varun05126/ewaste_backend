# ewaste_backend/core/forms.py

from django import forms
from .models import PickupRequest, ContactMessage

class PickupRequestForm(forms.ModelForm):
    class Meta:
        model = PickupRequest
        # Update fields to match the simplified model
        fields = ['name', 'email', 'phone', 'address'] # Removed specific address, date, time fields
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Your Email'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'address': forms.Textarea(attrs={'placeholder': 'Pickup Address', 'rows': 4}),
        }

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Your Email'}),
            'subject': forms.TextInput(attrs={'placeholder': 'Subject'}),
            'message': forms.Textarea(attrs={'placeholder': 'Your Message', 'rows': 5}),
        }
