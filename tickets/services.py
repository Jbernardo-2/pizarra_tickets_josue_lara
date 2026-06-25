from django.utils import timezone

from .models import TicketHistory


def add_history(ticket, user, action, old_value='', new_value=''):
    TicketHistory.objects.create(
        ticket=ticket,
        user=user if user and user.is_authenticated else None,
        action=action,
        old_value=str(old_value or ''),
        new_value=str(new_value or ''),
    )


def assign_ticket(ticket, technician, user):
    old_assignee = ticket.assigned_to.get_username() if ticket.assigned_to else 'Sin asignar'
    ticket.assigned_to = technician
    ticket.status = ticket.Status.ASSIGNED
    ticket.apply_status_defaults()
    ticket.save(update_fields=['assigned_to', 'status', 'progress', 'updated_at'])
    add_history(ticket, user, 'Ticket asignado', old_assignee, technician.get_username())


def change_ticket_status(ticket, status, progress, user):
    old_status = ticket.get_status_display()
    old_progress = ticket.progress
    ticket.status = status
    if progress is None:
        ticket.apply_status_defaults()
    else:
        ticket.progress = progress

    if status == ticket.Status.RESOLVED and not ticket.resolved_at:
        ticket.resolved_at = timezone.now()
    if status == ticket.Status.CLOSED and not ticket.closed_at:
        ticket.closed_at = timezone.now()
    if status == ticket.Status.CANCELED:
        ticket.is_active = False

    ticket.save()
    add_history(ticket, user, 'Cambio de estado', old_status, ticket.get_status_display())
    if old_progress != ticket.progress:
        add_history(ticket, user, 'Cambio de progreso', old_progress, ticket.progress)
