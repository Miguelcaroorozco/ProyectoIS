from django import forms

from apps.actividades.models import Actividad
from core.importante.form_choices import choices_presentes
from core.usuarios.models import Programa


class BusquedaAvanzadaForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'input',
                'type': 'search',
                'placeholder': 'Buscar por nombre, descripción...',
                'aria-label': 'Término de búsqueda',
            }
        ),
    )

    modalidad = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'select', 'aria-label': 'Modalidad'}),
    )

    tipologia = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'select', 'aria-label': 'Tipología'}),
    )

    programa = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'select', 'aria-label': 'Programa'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        modalidades_disponibles = Actividad.objects.order_by().values_list('modalidad', flat=True).distinct()
        tipologias_disponibles = Actividad.objects.order_by().values_list('tipologia', flat=True).distinct()

        programas = Programa.objects.order_by('nombre').values_list('nombre', flat=True)

        self.fields['modalidad'].choices = [
            ('', 'Seleccionar modalidad'),
            *choices_presentes(modalidades_disponibles, Actividad.MODALIDADES),
        ]
        self.fields['tipologia'].choices = [
            ('', 'Seleccionar tipología'),
            *choices_presentes(tipologias_disponibles, Actividad.TIPOLOGIAS),
        ]
        self.fields['programa'].choices = [
            ('', 'Seleccionar programa'),
            *[(nombre, nombre) for nombre in programas],
        ]
