from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm

from usuarios.models import Usuario

from .models import PreferenciasNotificaciones


User = get_user_model()



class FormCorreoUsuario(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']




class FormUsuario(forms.ModelForm):
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


class FormPreferenciasNotificaciones(forms.ModelForm):
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



class FormContrasena(PasswordChangeForm):
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
