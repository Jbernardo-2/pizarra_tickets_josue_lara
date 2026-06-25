from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    class Role(models.TextChoices):
        USER = 'user', 'Usuario'
        TECHNICIAN = 'technician', 'Tecnico'
        SUPERVISOR = 'supervisor', 'Supervisor'
        ADMIN = 'admin', 'Administrador'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'perfil'
        verbose_name_plural = 'perfiles'

    def __str__(self):
        return f'{self.user.get_username()} - {self.get_role_display()}'


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    elif not hasattr(instance, 'profile'):
        Profile.objects.create(user=instance)
