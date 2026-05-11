from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from core.administracion.gestion_usuarios import views as gestion_usuarios_views

from core.usuarios.models import Facultad, Programa, Usuario

from .facultades.forms import FormCrearFacultad
from .programas.forms import FormCrearPrograma


def _usuario_es_admin(request):
    if getattr(request.user, 'is_superuser', False):
        return True

    perfil = Usuario.objects.select_related('rol').filter(user_id=request.user.id).first()
    return bool(perfil and perfil.rol and perfil.rol.codigo == 'administrador')


@login_required
def admin_inicio(request):
    if not _usuario_es_admin(request):
        messages.error(request, 'No tienes permisos para acceder al panel de administración.')
        return redirect('index')
    return redirect('admin_usuarios')


def _acceso_admin_o_redireccion(request):
    if not _usuario_es_admin(request):
        messages.error(request, 'No tienes permisos para acceder al panel de administración.')
        return redirect('index')
    return None


@login_required
def admin_usuarios(request):
    bloqueo = _acceso_admin_o_redireccion(request)
    if bloqueo:
        return bloqueo
    return gestion_usuarios_views.lista_usuarios_view(request)


@login_required
def admin_usuarios_nuevo(request):
    bloqueo = _acceso_admin_o_redireccion(request)
    if bloqueo:
        return bloqueo
    return gestion_usuarios_views.nuevo_usuario_view(request)


@login_required
def admin_usuarios_editar(request, usuario_id: int):
    bloqueo = _acceso_admin_o_redireccion(request)
    if bloqueo:
        return bloqueo
    return gestion_usuarios_views.editar_usuario_view(request, usuario_id)


@login_required
def admin_facultades(request):
    bloqueo = _acceso_admin_o_redireccion(request)
    if bloqueo:
        return bloqueo

    form_facultad = FormCrearFacultad()

    if request.method == 'POST':
        form_facultad = FormCrearFacultad(request.POST)
        if form_facultad.is_valid():
            form_facultad.save()
            messages.success(request, 'Facultad creada correctamente.')
            return redirect('admin_facultades')
        messages.error(request, 'No se pudo crear la facultad. Revisa los campos.')

    contexto = {
        'active': 'facultades',
        'active_admin': 'facultades',
        'form_facultad_admin': form_facultad,
        'facultades_registradas': Facultad.objects.order_by('nombre')[:50],
    }

    return render(request, 'facultades/facultades.html', contexto)


@login_required
def admin_programas(request):
    bloqueo = _acceso_admin_o_redireccion(request)
    if bloqueo:
        return bloqueo

    form_programa = FormCrearPrograma()

    if request.method == 'POST':
        form_programa = FormCrearPrograma(request.POST)
        if form_programa.is_valid():
            form_programa.save()
            messages.success(request, 'Programa creado correctamente.')
            return redirect('admin_programas')
        messages.error(request, 'No se pudo crear el programa. Revisa los campos.')

    contexto = {
        'active': 'programas',
        'active_admin': 'programas',
        'form_programa_admin': form_programa,
        'programas_registrados': Programa.objects.select_related('facultad').order_by('nombre')[:50],
    }

    return render(request, 'programas/programas.html', contexto)
