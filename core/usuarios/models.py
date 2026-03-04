from django.conf import settings
from django.db import models


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

