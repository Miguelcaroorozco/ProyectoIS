from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Usuario


User = get_user_model()


@receiver(post_save, sender=User)
def asegurar_usuario_existe(sender, instance, created, **kwargs):
    if created:
        Usuario.objects.create(user=instance, correo=getattr(instance, 'email', '') or '')
    else:
        Usuario.objects.get_or_create(user=instance)
