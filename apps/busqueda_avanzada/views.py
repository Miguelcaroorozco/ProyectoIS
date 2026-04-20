from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from apps.actividades.models import Actividad
from .forms import BusquedaAvanzadaForm


@login_required
def busqueda_avanzada(request):
    form = BusquedaAvanzadaForm(request.GET or None)
    q = ''
    modalidad = ''
    tipologia = ''
    programa = ''

    if form.is_valid():
        q = (form.cleaned_data.get('q') or '').strip()
        modalidad = (form.cleaned_data.get('modalidad') or '').strip()
        tipologia = (form.cleaned_data.get('tipologia') or '').strip()
        programa = (form.cleaned_data.get('programa') or '').strip()

    busqueda_realizada = bool(request.GET)
    actividades = Actividad.objects.all()

    if q:
        actividades = actividades.filter(
            Q(nombre__icontains=q)
            | Q(descripcion__icontains=q)
            | Q(objetivo__icontains=q)
            | Q(programa__icontains=q)
            | Q(periodo__icontains=q)
        )

    if modalidad:
        actividades = actividades.filter(modalidad=modalidad)

    if tipologia:
        actividades = actividades.filter(tipologia=tipologia)

    if programa:
        actividades = actividades.filter(programa=programa)

    if not busqueda_realizada:
        actividades = Actividad.objects.none()

    return render(
        request,
        'busqueda_avanzada/busqueda-avanzada.html',
        {
            'form': form,
            'actividades': actividades,
            'busqueda_realizada': busqueda_realizada,
            'total_resultados': actividades.count(),
        },
    )
