from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Rol, Usuario


User = get_user_model()


@receiver(post_migrate)
def asegurar_roles(sender, **kwargs):
    if getattr(sender, 'name', '') != 'core.usuarios':
        return

    Rol.objects.get_or_create(codigo='usuario', defaults={'nombre': 'Usuario'})
    Rol.objects.get_or_create(codigo='administrador', defaults={'nombre': 'Administrador'})


@receiver(post_save, sender=User)
def asegurar_usuario_existe(sender, instance, created, **kwargs):
    rol_por_defecto = None
    try:
        rol_por_defecto = Rol.objects.get(codigo='usuario')
    except Rol.DoesNotExist:
        pass

    if created:
        Usuario.objects.create(
            user=instance,
            correo=getattr(instance, 'email', '') or '',
            rol=rol_por_defecto,
        )
        return

    usuario, _ = Usuario.objects.get_or_create(user=instance)
    if usuario.rol_id is None and rol_por_defecto is not None:
        usuario.rol = rol_por_defecto
        usuario.save(update_fields=['rol'])
