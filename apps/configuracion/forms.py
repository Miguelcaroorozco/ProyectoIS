from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm

from core.usuarios.models import Facultad, Usuario

from .models import PreferenciasNotificaciones


User = get_user_model()



class FormularioCorreoUsuario(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']




class FormularioUsuario(forms.ModelForm):
    facultad = forms.ChoiceField(required=False, widget=forms.Select(attrs={'class': 'select'}))

    class Meta:
        model = Usuario
        fields = [
            'primer_nombre',
            'segundo_nombre',
            'primer_apellido',
            'segundo_apellido',
            'facultad',
            'foto',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        facultades = Facultad.objects.order_by('nombre').values_list('nombre', flat=True)
        self.fields['facultad'].choices = [('', 'Seleccionar facultad'), *[(nombre, nombre) for nombre in facultades]]


class FormularioPreferenciasNotificaciones(forms.ModelForm):
    class Meta:
        model = PreferenciasNotificaciones
        fields = [
            'notificar_email',
            'alertas_actividades',
            'recordatorios',
        ]
        widgets = {
            'notificar_email': forms.CheckboxInput(),
            'alertas_actividades': forms.CheckboxInput(),
            'recordatorios': forms.CheckboxInput(),
        }



class FormularioContrasena(PasswordChangeForm):
    old_password = forms.CharField(
        label='Contraseña Actual',
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )
    new_password1 = forms.CharField(
        label='Nueva Contraseña',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    new_password2 = forms.CharField(
        label='Confirmar Contraseña',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
