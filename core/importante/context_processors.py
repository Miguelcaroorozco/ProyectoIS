from core.usuarios.models import Usuario


def usuario_foto_contexto(request):
	foto_url = None

	try:
		usuario_auth = getattr(request, 'user', None)
		if usuario_auth and getattr(usuario_auth, 'is_authenticated', False):
			usuario = Usuario.objects.filter(user_id=usuario_auth.id).only('foto').first()
			if usuario and usuario.foto:
				try:
					foto_url = usuario.foto.url
				except Exception:
					foto_url = None
	except Exception:
		foto_url = None

	return {
		'usuario_foto_url': foto_url,
	}
