from django import forms

from core.usuarios.models import Facultad, Programa
from core.importante.form_choices import choices_presentes

from .models import Actividad


class ActividadForm(forms.ModelForm):
    facultad = forms.ModelChoiceField(
        queryset=Facultad.objects.order_by('nombre'),
        widget=forms.Select(attrs={'class': 'select'}),
        empty_label='Seleccionar facultad',
    )

    programa = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'select'}),
    )

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
            'nombre': forms.TextInput(attrs={'class': 'input'}),
            'descripcion': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'objetivo': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'numero_participantes': forms.NumberInput(attrs={'class': 'input', 'min': 0}),
            'horas_dedicadas': forms.NumberInput(attrs={'class': 'input', 'min': 0}),
            'recursos_utilizados': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'resultados': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'observaciones': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        meses_disponibles = Actividad.objects.order_by().values_list('mes', flat=True).distinct()
        tipologias_disponibles = Actividad.objects.order_by().values_list('tipologia', flat=True).distinct()
        modalidades_disponibles = Actividad.objects.order_by().values_list('modalidad', flat=True).distinct()

        self.fields['mes'].choices = [
            ('', 'Seleccionar mes'),
            *(choices_presentes(meses_disponibles, Actividad.MESES) or Actividad.MESES),
        ]
        self.fields['tipologia'].choices = [
            ('', 'Seleccionar tipología'),
            *(choices_presentes(tipologias_disponibles, Actividad.TIPOLOGIAS) or Actividad.TIPOLOGIAS),
        ]
        self.fields['modalidad'].choices = [
            ('', 'Seleccionar modalidad'),
            *(choices_presentes(modalidades_disponibles, Actividad.MODALIDADES) or Actividad.MODALIDADES),
        ]

        selected_facultad_id = None
        if self.is_bound:
            selected_facultad_id = self.data.get(self.add_prefix('facultad'))
        else:
            initial_facultad = self.initial.get('facultad') if hasattr(self, 'initial') else None
            if initial_facultad:
                selected_facultad_id = getattr(initial_facultad, 'pk', initial_facultad)

        programas_qs = Programa.objects.order_by('nombre')
        if selected_facultad_id:
            programas_qs = programas_qs.filter(facultad_id=selected_facultad_id)

        self.fields['programa'].choices = [
            ('', 'Seleccionar programa'),
            *[(str(programa.pk), programa.nombre) for programa in programas_qs],
        ]

    def clean_programa(self):
        programa_id = (self.cleaned_data.get('programa') or '').strip()
        if not programa_id:
            return ''

        try:
            programa = Programa.objects.select_related('facultad').get(pk=programa_id)
        except (Programa.DoesNotExist, ValueError, TypeError):
            raise forms.ValidationError('Selecciona un programa válido.')

        facultad = self.cleaned_data.get('facultad')
        if facultad and programa.facultad_id != facultad.id:
            raise forms.ValidationError('El programa seleccionado no pertenece a la facultad.')

        return programa.nombre

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            self.add_error('fecha_fin', 'La fecha de fin no puede ser anterior a la fecha de inicio.')

        return cleaned_data
