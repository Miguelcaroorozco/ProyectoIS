from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from core.usuarios.models import Rol, Usuario


class FormCrearUsuario(forms.Form):
	correo = forms.EmailField()
	primer_nombre = forms.CharField(required=False)
	primer_apellido = forms.CharField(required=False)
	rol = forms.ModelChoiceField(queryset=Rol.objects.all(), required=False, empty_label='Sin rol')
	password1 = forms.CharField(widget=forms.PasswordInput)
	password2 = forms.CharField(widget=forms.PasswordInput)

	def clean_correo(self):
		correo = (self.cleaned_data.get('correo') or '').strip().lower()
		User = get_user_model()
		if User.objects.filter(username=correo).exists() or User.objects.filter(email=correo).exists():
			raise ValidationError('Ya existe un usuario con este correo.')
		return correo

	def clean(self):
		datos = super().clean()
		password1 = datos.get('password1')
		password2 = datos.get('password2')
		if password1 and password2 and password1 != password2:
			raise ValidationError('Las contraseñas no coinciden.')
		if password1:
			validate_password(password1)
		return datos

	def save(self):
		User = get_user_model()
		correo = self.cleaned_data['correo']
		primer_nombre = (self.cleaned_data.get('primer_nombre') or '').strip()
		primer_apellido = (self.cleaned_data.get('primer_apellido') or '').strip()
		rol = self.cleaned_data.get('rol')

		user = User.objects.create_user(
			username=correo,
			email=correo,
			password=self.cleaned_data['password1'],
			first_name=primer_nombre,
			last_name=primer_apellido,
		)

		usuario, _ = Usuario.objects.get_or_create(user=user)
		usuario.correo = correo
		if rol:
			usuario.rol = rol
		if primer_nombre:
			usuario.primer_nombre = primer_nombre
		if primer_apellido:
			usuario.primer_apellido = primer_apellido
		usuario.save()

		return usuario


class FormEditarUsuario(forms.Form):
	correo = forms.EmailField()
	primer_nombre = forms.CharField(required=False)
	primer_apellido = forms.CharField(required=False)
	rol = forms.ModelChoiceField(queryset=Rol.objects.all(), required=False, empty_label='Sin rol')

	def __init__(self, *args, usuario: Usuario, **kwargs):
		super().__init__(*args, **kwargs)
		self.usuario = usuario
		self.fields['correo'].initial = usuario.user.email or usuario.user.username
		self.fields['primer_nombre'].initial = usuario.primer_nombre
		self.fields['primer_apellido'].initial = usuario.primer_apellido
		self.fields['rol'].initial = usuario.rol

	def clean_correo(self):
		correo = (self.cleaned_data.get('correo') or '').strip().lower()
		User = get_user_model()

		existe_username = User.objects.filter(username=correo).exclude(pk=self.usuario.user_id).exists()
		existe_email = User.objects.filter(email=correo).exclude(pk=self.usuario.user_id).exists()
		if existe_username or existe_email:
			raise ValidationError('Ya existe otro usuario con este correo.')

		return correo

	def save(self):
		correo = self.cleaned_data['correo']
		primer_nombre = (self.cleaned_data.get('primer_nombre') or '').strip()
		primer_apellido = (self.cleaned_data.get('primer_apellido') or '').strip()
		rol = self.cleaned_data.get('rol')

		user = self.usuario.user
		user.username = correo
		user.email = correo
		user.first_name = primer_nombre
		user.last_name = primer_apellido
		user.save(update_fields=['username', 'email', 'first_name', 'last_name'])

		self.usuario.correo = correo
		self.usuario.primer_nombre = primer_nombre
		self.usuario.primer_apellido = primer_apellido
		self.usuario.rol = rol
		self.usuario.save(update_fields=['correo', 'primer_nombre', 'primer_apellido', 'rol'])

		return self.usuario
