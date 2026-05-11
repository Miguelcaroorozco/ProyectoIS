from django import forms

from apps.actividades.models import Actividad
from core.usuarios.models import Programa


def _choices_distintos_desde_bd(valores, *, empty_value='', empty_label='Todos'):
    vistos = set()
    resultado = [(empty_value, empty_label)]
    for valor in valores:
        texto = ('' if valor is None else str(valor)).strip()
        if not texto:
            continue
        key = texto.casefold()
        if key in vistos:
            continue
        vistos.add(key)
        resultado.append((texto, texto))
    return resultado


def _choices_por_choices_base(valores_bd, choices_base, *, empty_value='', empty_label='Todos'):
    """Devuelve choices en el orden de choices_base, pero solo los presentes en BD.

    Soporta BD con códigos o con etiquetas (ej. 'enero' o 'Enero').
    El value final será el código del choice (para evitar duplicados).
    """

    mapping = {}
    for codigo, etiqueta in choices_base:
        mapping[str(codigo).casefold()] = codigo
        mapping[str(etiqueta).casefold()] = codigo

    presentes = set()
    for valor in valores_bd:
        texto = ('' if valor is None else str(valor)).strip()
        if not texto:
            continue
        codigo = mapping.get(texto.casefold())
        if codigo is not None:
            presentes.add(codigo)

    resultado = [(empty_value, empty_label)]
    for codigo, etiqueta in choices_base:
        if codigo in presentes:
            resultado.append((codigo, etiqueta))
    return resultado


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
        # Tipología puede venir de BD con valores libres (por ejemplo cargados vía SQL).
        self.fields['tipologia'].choices = _choices_distintos_desde_bd(
            tipologias_disponibles,
            empty_label='Todas',
        )
        self.fields['programa'].choices = [
            ('', 'Todos'),
            *[(nombre, nombre) for nombre in programas],
        ]
        self.fields['mes'].choices = _choices_por_choices_base(
            meses_disponibles,
            Actividad.MESES,
            empty_label='Todos',
        )
