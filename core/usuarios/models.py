from django.conf import settings
from django.db import models


class Facultad(models.Model):
	codigo = models.SlugField(max_length=40, unique=True)
	nombre = models.CharField(max_length=120, unique=True)
	descripcion = models.CharField(max_length=200, blank=True)

	class Meta:
		ordering = ['nombre']

	def __str__(self):
		return self.nombre


class Programa(models.Model):
	facultad = models.ForeignKey(Facultad, on_delete=models.PROTECT, related_name='programas')
	codigo = models.SlugField(max_length=40, unique=True)
	nombre = models.CharField(max_length=150)
	descripcion = models.CharField(max_length=200, blank=True)

	def __str__(self):
		return self.nombre


class Rol(models.Model):
	codigo = models.SlugField(max_length=40, unique=True)
	nombre = models.CharField(max_length=80)
	descripcion = models.CharField(max_length=200, blank=True)


class Usuario(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	rol = models.ForeignKey(Rol, on_delete=models.PROTECT, null=True, blank=True)

	primer_nombre = models.CharField(max_length=80, blank=True)
	segundo_nombre = models.CharField(max_length=80, blank=True, null=True)

	primer_apellido = models.CharField(max_length=80, blank=True)
	segundo_apellido = models.CharField(max_length=80, blank=True, null=True)

	facultad = models.CharField(max_length=150, blank=True)
	foto = models.ImageField(upload_to='fotos_usuarios/', blank=True, null=True)

	correo = models.EmailField(blank=True)

