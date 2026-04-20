from django import forms

from apps.actividades.models import Actividad
from core.importante.form_choices import choices_presentes
from core.usuarios.models import Programa


class ReportesFiltroForm(forms.Form):
    tipo = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'select', 'aria-label': 'Tipo de reporte'}),
    )

    tipologia = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'select', 'aria-label': 'Tipología'}),
    )

    programa = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'select', 'aria-label': 'Programa'}),
    )

    mes = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'select', 'aria-label': 'Mes'}),
    )

    anio = forms.IntegerField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'Ej. 2026', 'list': 'anios-lista'}),
    )

    fecha_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
    )

    fecha_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
    )

    def __init__(self, *args, tipos_reporte=None, **kwargs):
        super().__init__(*args, **kwargs)

        tipos_reporte = tipos_reporte or {}

        tipologias_disponibles = Actividad.objects.order_by().values_list('tipologia', flat=True).distinct()
        meses_disponibles = Actividad.objects.order_by().values_list('mes', flat=True).distinct()
        programas = Programa.objects.order_by('nombre').values_list('nombre', flat=True)

        self.fields['tipo'].choices = [(codigo, nombre) for codigo, nombre in tipos_reporte.items()]
        self.fields['tipologia'].choices = [
            ('', 'Todas'),
            *choices_presentes(tipologias_disponibles, Actividad.TIPOLOGIAS),
        ]
        self.fields['programa'].choices = [
            ('', 'Todos'),
            *[(nombre, nombre) for nombre in programas],
        ]
        self.fields['mes'].choices = [
            ('', 'Todos'),
            *choices_presentes(meses_disponibles, Actividad.MESES),
        ]
