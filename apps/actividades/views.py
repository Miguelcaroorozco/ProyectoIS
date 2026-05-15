from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Case, IntegerField, Q, Value, When
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ActividadForm
from .models import Actividad

from core.usuarios.models import Programa
from core.usuarios.models import Usuario


def _es_admin(user):
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'is_superuser', False):
        return True
    perfil = (
        Usuario.objects.select_related('rol')
        .filter(user_id=user.id)
        .only('rol__codigo')
        .first()
    )
    return bool(perfil and perfil.rol and perfil.rol.codigo == 'administrador')


def _puede_modificar(user, actividad: Actividad):
    if _es_admin(user):
        return True
    return bool(actividad.creado_por_id and actividad.creado_por_id == getattr(user, 'id', None))


@login_required
def actividades(request):
    consulta = request.GET.get('q', '').strip()
    es_admin = _es_admin(request.user)
    actividades_qs = Actividad.objects.select_related('creado_por').all()

    if consulta:
        actividades_qs = actividades_qs.filter(
            Q(nombre__icontains=consulta)
            | Q(tipologia__icontains=consulta)
            | Q(programa__icontains=consulta)
            | Q(periodo__icontains=consulta)
            | Q(modalidad__icontains=consulta)
        )

    # Usuarios normales: mostrar todas, pero priorizar las propias al inicio.
    if not es_admin:
        actividades_qs = actividades_qs.annotate(
            _own_first=Case(
                When(creado_por=request.user, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by('_own_first', '-fecha_inicio', '-id')
    else:
        actividades_qs = actividades_qs.order_by('-fecha_inicio', '-id')

    paginator = Paginator(actividades_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'actividades': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'q': consulta,
        'es_admin': es_admin,
    }

    if (request.GET.get('partial') or '').strip().lower() == 'tabla':
        return render(request, 'actividades/_tabla.html', context)

    return render(
        request,
        'actividades/actividades.html',
        context,
    )


@login_required
def editar_actividad(request, pk):
    actividad = get_object_or_404(Actividad, pk=pk)
    if not _puede_modificar(request.user, actividad):
        messages.error(request, 'No tienes permisos para editar esta actividad.')
        return redirect('actividades')

    if request.method == 'POST':
        form = ActividadForm(request.POST, instance=actividad)
        if form.is_valid():
            actividad_actualizada = form.save(commit=False)
            # No cambiar el creador en edición.
            actividad_actualizada.creado_por = actividad.creado_por
            actividad_actualizada.save()
            messages.success(request, 'Actividad actualizada correctamente.')
            return redirect('actividades')
    else:
        form = ActividadForm(instance=actividad)

    return render(
        request,
        'actividades/editar-actividad.html',
        {
            'form': form,
            'actividad': actividad,
        },
    )


@login_required
def eliminar_actividad(request, pk):
    actividad = get_object_or_404(Actividad, pk=pk)
    if not _puede_modificar(request.user, actividad):
        messages.error(request, 'No tienes permisos para eliminar esta actividad.')
        return redirect('actividades')

    if request.method != 'POST':
        return redirect('actividades')

    nombre = actividad.nombre
    actividad.delete()
    messages.success(request, f'Actividad "{nombre}" eliminada correctamente.')
    return redirect('actividades')


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
