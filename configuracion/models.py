from django.conf import settings
from django.db import models


class PreferenciasNotificaciones(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    notificar_email = models.BooleanField(default=False)
    alertas_actividades = models.BooleanField(default=False)
    recordatorios = models.BooleanField(default=True)
