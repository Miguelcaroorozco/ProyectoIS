from django import forms

from core.usuarios.models import Facultad, Programa


class FormCrearPrograma(forms.ModelForm):
    facultad = forms.ModelChoiceField(
        queryset=Facultad.objects.order_by('nombre'),
        widget=forms.Select(attrs={'class': 'select'}),
    )

    class Meta:
        model = Programa
        fields = ['facultad', 'codigo', 'nombre', 'descripcion']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'input'}),
            'nombre': forms.TextInput(attrs={'class': 'input'}),
            'descripcion': forms.TextInput(attrs={'class': 'input'}),
        }
