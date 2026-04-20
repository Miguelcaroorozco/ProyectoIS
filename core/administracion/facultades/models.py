from django.db import models


class Facultad(models.Model):
    codigo = models.SlugField(max_length=40, unique=True)
    nombre = models.CharField(max_length=120, unique=True)
    descripcion = models.CharField(max_length=200, blank=True)

    class Meta:
        app_label = 'usuarios'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
