from .models import * 
from django.forms import ModelForm, TextInput, Textarea
from django import forms


class TestForm(ModelForm):
    class Meta:
        model = Test
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
        }