from django.conf import settings
from django.db import models


class Usuario(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

	primer_nombre = models.CharField(max_length=80, blank=True)
	segundo_nombre = models.CharField(max_length=80, blank=True, null=True)

	primer_apellido = models.CharField(max_length=80, blank=True)
	segundo_apellido = models.CharField(max_length=80, blank=True, null=True)

	facultad = models.CharField(max_length=150, blank=True)
	foto = models.ImageField(upload_to='fotos_usuarios/', blank=True, null=True)

	correo = models.EmailField(blank=True)

