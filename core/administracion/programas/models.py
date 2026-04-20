from django.db import models

from core.administracion.facultades.models import Facultad


class Programa(models.Model):
    facultad = models.ForeignKey(Facultad, on_delete=models.PROTECT, related_name='programas')
    codigo = models.SlugField(max_length=40, unique=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.CharField(max_length=200, blank=True)

    class Meta:
        app_label = 'usuarios'

    def __str__(self):
        return self.nombre
