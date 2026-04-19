from django import forms

from core.usuarios.models import Programa

from .models import Actividad


class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = [
            'mes',
            'periodo',
            'fecha_inicio',
            'fecha_fin',
            'tipologia',
            'modalidad',
            'programa',
            'nombre',
            'descripcion',
            'objetivo',
            'numero_participantes',
            'horas_dedicadas',
            'recursos_utilizados',
            'resultados',
            'observaciones',
        ]
        widgets = {
            'mes': forms.Select(attrs={'class': 'select'}),
            'periodo': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Ej. 2026-1'}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'tipologia': forms.Select(attrs={'class': 'select'}),
            'modalidad': forms.Select(attrs={'class': 'select'}),
            'programa': forms.Select(attrs={'class': 'select'}),
            'nombre': forms.TextInput(attrs={'class': 'input'}),
            'descripcion': forms.Textarea(attrs={'class': 'textarea'}),
            'objetivo': forms.Textarea(attrs={'class': 'textarea'}),
            'numero_participantes': forms.NumberInput(attrs={'class': 'input', 'min': 0}),
            'horas_dedicadas': forms.NumberInput(attrs={'class': 'input', 'min': 0}),
            'recursos_utilizados': forms.Textarea(attrs={'class': 'textarea'}),
            'resultados': forms.Textarea(attrs={'class': 'textarea'}),
            'observaciones': forms.Textarea(attrs={'class': 'textarea'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mes'].choices = [('', 'Seleccionar mes'), *Actividad.MESES]
        self.fields['tipologia'].choices = [('', 'Seleccionar tipología'), *Actividad.TIPOLOGIAS]
        self.fields['modalidad'].choices = [('', 'Seleccionar modalidad'), *Actividad.MODALIDADES]
        programas = Programa.objects.order_by('nombre').values_list('nombre', flat=True)
        self.fields['programa'].choices = [('', 'Seleccionar programa'), *[(nombre, nombre) for nombre in programas]]

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            self.add_error('fecha_fin', 'La fecha de fin no puede ser anterior a la fecha de inicio.')

        return cleaned_data
