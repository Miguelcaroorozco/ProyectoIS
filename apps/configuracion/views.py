from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from core.usuarios.models import Usuario

from .forms import (
	FormContrasena,
	FormCorreoUsuario,
	FormPreferenciasNotificaciones,
	FormUsuario,
)
from .models import PreferenciasNotificaciones


@login_required
def configuracion_view(request):
	usuario, _ = Usuario.objects.get_or_create(user=request.user)
	preferencias, _ = PreferenciasNotificaciones.objects.get_or_create(user=request.user)

	if request.method == 'POST':
		accion = request.POST.get('action', 'perfil')

		if accion == 'perfil':
			form_usuario = FormUsuario(request.POST, request.FILES, instance=usuario)
			form_preferencias = FormPreferenciasNotificaciones(instance=preferencias)
			form_correo = FormCorreoUsuario(request.POST, instance=request.user)
			form_contrasena = FormContrasena(user=request.user)

			if form_usuario.is_valid() and form_correo.is_valid():
				form_usuario.save()
				form_correo.save()

				if usuario.correo != request.user.email:
					usuario.correo = request.user.email
					usuario.save(update_fields=['correo'])

				messages.success(request, 'Cambios guardados correctamente.')
				return redirect('configuracion')

			messages.error(request, 'Revisa los campos del perfil. No se pudieron guardar los cambios.')

		elif accion == 'notificaciones':
			form_usuario = FormUsuario(instance=usuario)
			form_preferencias = FormPreferenciasNotificaciones(request.POST, instance=preferencias)
			form_correo = FormCorreoUsuario(instance=request.user)
			form_contrasena = FormContrasena(user=request.user)

			if form_preferencias.is_valid():
				form_preferencias.save()
				messages.success(request, 'Preferencias de notificación guardadas correctamente.')
				return redirect('configuracion')

			messages.error(request, 'No se pudieron guardar las preferencias de notificación.')

		elif accion == 'contrasena':
			form_usuario = FormUsuario(instance=usuario)
			form_preferencias = FormPreferenciasNotificaciones(instance=preferencias)
			form_correo = FormCorreoUsuario(instance=request.user)
			form_contrasena = FormContrasena(user=request.user, data=request.POST)

			if form_contrasena.is_valid():
				usuario_auth = form_contrasena.save()
				update_session_auth_hash(request, usuario_auth)
				messages.success(request, 'Contraseña actualizada correctamente.')
				return redirect('configuracion')

			messages.error(request, 'No se pudo cambiar la contraseña. Verifica los campos.')

		else:
			return redirect('configuracion')

	else:
		form_usuario = FormUsuario(instance=usuario)
		form_preferencias = FormPreferenciasNotificaciones(instance=preferencias)
		form_correo = FormCorreoUsuario(instance=request.user)
		form_contrasena = FormContrasena(user=request.user)

	contexto = {
		'form_usuario': form_usuario,
		'form_preferencias': form_preferencias,
		'form_correo': form_correo,
		'form_contrasena': form_contrasena,
		'version': 'v1.0.0',
	}

	return render(request, 'configuracion/configuracion.html', contexto)
