from core.usuarios.models import Usuario


def usuario_foto_contexto(request):
	foto_url = None
	usuario_rol_codigo = None

	try:
		usuario_auth = getattr(request, 'user', None)
		if usuario_auth and getattr(usuario_auth, 'is_authenticated', False):
			if getattr(usuario_auth, 'is_superuser', False):
				usuario_rol_codigo = 'administrador'

			usuario = Usuario.objects.select_related('rol').filter(user_id=usuario_auth.id).only('foto', 'rol__codigo').first()
			if usuario and usuario.foto:
				try:
					foto_url = usuario.foto.url
				except Exception:
					foto_url = None
			if usuario and usuario.rol:
				usuario_rol_codigo = usuario.rol.codigo
			elif usuario_rol_codigo is None:
				usuario_rol_codigo = 'usuario'
	except Exception:
		foto_url = None

	return {
		'usuario_foto_url': foto_url,
		'usuario_rol_codigo': usuario_rol_codigo,
	}
