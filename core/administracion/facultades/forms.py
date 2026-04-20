from django import forms

from core.usuarios.models import Facultad


class FormCrearFacultad(forms.ModelForm):
    class Meta:
        model = Facultad
        fields = ['codigo', 'nombre', 'descripcion']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'input'}),
            'nombre': forms.TextInput(attrs={'class': 'input'}),
            'descripcion': forms.TextInput(attrs={'class': 'input'}),
        }
