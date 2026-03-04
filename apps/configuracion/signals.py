from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PreferenciasNotificaciones


User = get_user_model()


@receiver(post_save, sender=User)
def asegurar_perfil_existe(sender, instance, created, **kwargs):
    if created:
        PreferenciasNotificaciones.objects.create(user=instance)
    else:
        PreferenciasNotificaciones.objects.get_or_create(user=instance)
