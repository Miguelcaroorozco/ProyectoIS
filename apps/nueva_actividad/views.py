from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from core.usuarios.models import Usuario


def _puede_crear_actividades(request):
    if getattr(request.user, 'is_superuser', False):
        return True

    perfil = Usuario.objects.select_related('rol').filter(user_id=request.user.id).first()
    if perfil and perfil.rol and perfil.rol.codigo == 'administrador':
        return True

    messages.error(request, 'No tienes permisos para crear actividades.')
    return False


@login_required
def nueva_actividad(request):
    if not _puede_crear_actividades(request):
        return redirect('actividades')

    return render(request, 'nueva_actividad/nueva-actividad.html')
