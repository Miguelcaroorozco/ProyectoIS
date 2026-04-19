from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from apps.actividades.models import Actividad
from core.usuarios.models import Programa


@login_required
def busqueda_avanzada(request):
    q = request.GET.get('q', '').strip()
    modalidad = request.GET.get('modalidad', '').strip()
    tipologia = request.GET.get('tipologia', '').strip()
    programa = request.GET.get('programa', '').strip()

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

    programas_disponibles = Programa.objects.order_by('nombre').values_list('nombre', flat=True)

    return render(
        request,
        'busqueda_avanzada/busqueda-avanzada.html',
        {
            'actividades': actividades,
            'modalidades': Actividad.MODALIDADES,
            'tipologias': Actividad.TIPOLOGIAS,
            'programas_disponibles': programas_disponibles,
            'filtros': {
                'q': q,
                'modalidad': modalidad,
                'tipologia': tipologia,
                'programa': programa,
            },
            'busqueda_realizada': busqueda_realizada,
            'total_resultados': actividades.count(),
        },
    )
