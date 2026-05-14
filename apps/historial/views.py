from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.utils.timesince import timesince

from apps.actividades.models import Actividad

from core.usuarios.models import Usuario


def _usuario_es_admin(request) -> bool:
    if getattr(request.user, 'is_superuser', False):
        return True

    perfil = Usuario.objects.select_related('rol').filter(user_id=request.user.id).only('rol__codigo').first()
    return bool(perfil and perfil.rol and perfil.rol.codigo == 'administrador')


def _user_display_name(user) -> str:
    if not user:
        return 'Sistema'

    get_full_name = getattr(user, 'get_full_name', None)
    if callable(get_full_name):
        full_name = (get_full_name() or '').strip()
        if full_name:
            return full_name

    for attr in ('username', 'email'):
        value = (getattr(user, attr, '') or '').strip()
        if value:
            return value

    return str(user)


@login_required
def historial(request):
    now = timezone.now()
    # Para evitar que una creación cuente como edición, exigimos una diferencia mínima.
    umbral_edicion = timedelta(seconds=1)

    is_admin = _usuario_es_admin(request)

    actividades_qs = Actividad.objects.select_related('creado_por')
    if not is_admin:
        actividades_qs = actividades_qs.filter(creado_por=request.user)

    actividades = (
        actividades_qs.only(
            'id',
            'nombre',
            'creado_con_ia',
            'fecha_creacion',
            'fecha_actualizacion',
            'creado_por__id',
            'creado_por__username',
            'creado_por__email',
            'creado_por__first_name',
            'creado_por__last_name',
        )
        .order_by('-fecha_actualizacion')[:25]
    )

    eventos = []
    for actividad in actividades:
        if actividad.fecha_creacion:
            titulo = 'Actividad creada con IA' if getattr(actividad, 'creado_con_ia', False) else 'Actividad creada'
            eventos.append(
                {
                    'tipo': 'Creación',
                    'titulo': titulo,
                    'descripcion': f"Se registró la actividad: {actividad.nombre}",
                    'usuario': _user_display_name(actividad.creado_por),
                    'timestamp': actividad.fecha_creacion,
                }
            )

        if (
            actividad.fecha_actualizacion
            and actividad.fecha_creacion
            and actividad.fecha_actualizacion > actividad.fecha_creacion + umbral_edicion
        ):
            eventos.append(
                {
                    'tipo': 'Edición',
                    'titulo': 'Actividad modificada',
                    'descripcion': f"Se actualizó la actividad: {actividad.nombre}",
                    'usuario': _user_display_name(actividad.creado_por),
                    'timestamp': actividad.fecha_actualizacion,
                }
            )

    eventos.sort(key=lambda e: e['timestamp'], reverse=True)
    eventos = eventos[:10]
    for evento in eventos:
        hace = timesince(evento['timestamp'], now).split(',')[0]
        evento['hace'] = hace

    return render(request, 'historial/historial.html', {'eventos': eventos, 'is_admin': is_admin})
