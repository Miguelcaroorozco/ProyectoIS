from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
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

    actividades_qs = actividades_qs.order_by('-fecha_inicio', '-id')

    paginator = Paginator(actividades_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'actividades': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'q': consulta,
    }

    if (request.GET.get('partial') or '').strip().lower() == 'tabla':
        return render(request, 'actividades/_tabla.html', context)

    return render(
        request,
        'actividades/actividades.html',
        context,
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
