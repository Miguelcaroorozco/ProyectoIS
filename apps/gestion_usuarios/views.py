from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from core.usuarios.models import Usuario

from .forms import FormCrearUsuario, FormEditarUsuario


@login_required
def lista_usuarios_view(request):
	User = get_user_model()
	usuarios_auth = User.objects.only('id', 'username', 'email').order_by('username')
	for usuario_auth in usuarios_auth:
		Usuario.objects.get_or_create(
			user_id=usuario_auth.id,
			defaults={'correo': usuario_auth.email or ''},
		)

	usuarios = Usuario.objects.select_related('user', 'rol').order_by('user__username')

	total_usuarios = usuarios.count()
	total_administradores = usuarios.filter(rol__codigo='administrador').count()
	total_docentes = usuarios.filter(rol__codigo='usuario').count()

	contexto = {
		'usuarios': usuarios,
		'total_usuarios': total_usuarios,
		'total_administradores': total_administradores,
		'total_docentes': total_docentes,
	}

	return render(request, 'gestion_usuarios/usuarios.html', contexto)


@login_required
def nuevo_usuario_view(request):
	if request.method == 'POST':
		form = FormCrearUsuario(request.POST)
		if form.is_valid():
			with transaction.atomic():
				form.save()
			messages.success(request, 'Usuario creado correctamente.')
			return redirect('usuarios')
		messages.error(request, 'Revisa los campos. No se pudo crear el usuario.')
	else:
		form = FormCrearUsuario()

	return render(
		request,
		'gestion_usuarios/usuario_form.html',
		{
			'titulo': 'Nuevo Usuario',
			'boton': 'Crear Usuario',
			'form': form,
			'active': 'usuarios',
		},
	)


@login_required
def editar_usuario_view(request, usuario_id: int):
	usuario = get_object_or_404(Usuario.objects.select_related('user', 'rol'), pk=usuario_id)

	if request.method == 'POST':
		form = FormEditarUsuario(request.POST, usuario=usuario)
		if form.is_valid():
			with transaction.atomic():
				form.save()
			messages.success(request, 'Usuario actualizado correctamente.')
			return redirect('usuarios')
		messages.error(request, 'Revisa los campos. No se pudo actualizar el usuario.')
	else:
		form = FormEditarUsuario(usuario=usuario)

	return render(
		request,
		'gestion_usuarios/usuario_form.html',
		{
			'titulo': 'Editar Usuario',
			'boton': 'Guardar Cambios',
			'form': form,
			'active': 'usuarios',
		},
	)
