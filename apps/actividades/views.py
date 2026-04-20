from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render

from .forms import ActividadForm
from .models import Actividad

from core.usuarios.models import Programa


@login_required
def actividades(request):
    consulta = request.GET.get('q', '').strip()
    actividades_qs = Actividad.objects.all()

    if consulta:
        actividades_qs = actividades_qs.filter(
            Q(nombre__icontains=consulta)
            | Q(tipologia__icontains=consulta)
            | Q(programa__icontains=consulta)
            | Q(periodo__icontains=consulta)
            | Q(modalidad__icontains=consulta)
        )

    return render(
        request,
        'actividades/actividades.html',
        {
            'actividades': actividades_qs,
            'q': consulta,
        },
    )


@login_required
def nueva_actividad(request):
    if request.method == 'POST':
        form = ActividadForm(request.POST)
        if form.is_valid():
            actividad = form.save(commit=False)
            actividad.creado_por = request.user
            actividad.save()
            messages.success(request, 'Actividad registrada correctamente.')
            return redirect('actividades')
    else:
        form = ActividadForm()

    return render(
        request,
        'actividades/nueva-actividad.html',
        {
            'form': form,
        },
    )


@login_required
def programas_por_facultad(request):
    facultad_id = (request.GET.get('facultad_id') or '').strip()
    qs = Programa.objects.all()
    if facultad_id:
        qs = qs.filter(facultad_id=facultad_id)

    programas = list(qs.order_by('nombre').values('id', 'nombre'))

    return JsonResponse({'programas': programas})
