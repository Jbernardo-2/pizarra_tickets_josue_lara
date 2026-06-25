from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


class Ticket(models.Model):
    class Priority(models.TextChoices):
        LOW = 'low', 'Baja'
        MEDIUM = 'medium', 'Media'
        HIGH = 'high', 'Alta'
        URGENT = 'urgent', 'Urgente'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        ASSIGNED = 'assigned', 'Asignado'
        IN_PROGRESS = 'in_progress', 'En proceso'
        ON_HOLD = 'on_hold', 'En espera'
        RESOLVED = 'resolved', 'Resuelto'
        CLOSED = 'closed', 'Cerrado'
        CANCELED = 'canceled', 'Cancelado'

    AUTO_PROGRESS = {
        Status.PENDING: 0,
        Status.ASSIGNED: 20,
        Status.IN_PROGRESS: 50,
        Status.ON_HOLD: 60,
        Status.RESOLVED: 90,
        Status.CLOSED: 100,
        Status.CANCELED: 0,
    }

    title = models.CharField('titulo', max_length=180)
    description = models.TextField('descripcion')
    category = models.CharField('categoria', max_length=120)
    priority = models.CharField(
        'prioridad',
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    status = models.CharField(
        'estado',
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    progress = models.PositiveSmallIntegerField(
        'progreso',
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_tickets',
        verbose_name='creado por',
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_tickets',
        verbose_name='asignado a',
        blank=True,
        null=True,
    )
    due_date = models.DateField('fecha limite', blank=True, null=True)
    resolved_at = models.DateTimeField('fecha de resolucion', blank=True, null=True)
    closed_at = models.DateTimeField('fecha de cierre', blank=True, null=True)
    is_active = models.BooleanField('activo', default=True)
    created_at = models.DateTimeField('fecha de creacion', auto_now_add=True)
    updated_at = models.DateTimeField('ultima actualizacion', auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'ticket'
        verbose_name_plural = 'tickets'

    def __str__(self):
        return f'#{self.pk} - {self.title}'

    def get_absolute_url(self):
        return reverse('tickets:detail', kwargs={'pk': self.pk})

    def apply_status_defaults(self):
        if self.status in self.AUTO_PROGRESS:
            self.progress = self.AUTO_PROGRESS[self.status]

    @property
    def is_overdue(self):
        from django.utils import timezone

        return bool(
            self.due_date
            and self.due_date < timezone.localdate()
            and self.status not in {self.Status.RESOLVED, self.Status.CLOSED, self.Status.CANCELED}
        )


class TicketComment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    comment = models.TextField('comentario')
    created_at = models.DateTimeField('fecha de creacion', auto_now_add=True)

    class Meta:
        ordering = ('created_at',)
        verbose_name = 'comentario de ticket'
        verbose_name_plural = 'comentarios de ticket'

    def __str__(self):
        return f'Comentario de {self.user} en ticket #{self.ticket_id}'


class TicketHistory(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    action = models.CharField('accion', max_length=120)
    old_value = models.CharField('valor anterior', max_length=255, blank=True)
    new_value = models.CharField('valor nuevo', max_length=255, blank=True)
    created_at = models.DateTimeField('fecha', auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'historial de ticket'
        verbose_name_plural = 'historial de tickets'

    def __str__(self):
        return f'{self.action} - ticket #{self.ticket_id}'


class TicketFile(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='files')
    file = models.FileField('archivo', upload_to='tickets/%Y/%m/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField('fecha de subida', auto_now_add=True)

    class Meta:
        ordering = ('-uploaded_at',)
        verbose_name = 'archivo de ticket'
        verbose_name_plural = 'archivos de ticket'

    def __str__(self):
        return f'Archivo ticket #{self.ticket_id}'
