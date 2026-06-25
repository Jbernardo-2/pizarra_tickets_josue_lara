from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.views.generic import TemplateView

from accounts.models import Profile
from tickets.models import Ticket
from tickets.permissions import get_role


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_base_queryset(self):
        role = get_role(self.request.user)
        queryset = Ticket.objects.select_related('created_by', 'assigned_to')
        if role in {Profile.Role.SUPERVISOR, Profile.Role.ADMIN}:
            return queryset
        if role == Profile.Role.TECHNICIAN:
            return queryset.filter(assigned_to=self.request.user)
        return queryset.filter(created_by=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_base_queryset()
        role = get_role(self.request.user)
        context['role'] = role
        context['stats'] = {
            'total': queryset.count(),
            'pending': queryset.filter(status=Ticket.Status.PENDING).count(),
            'assigned': queryset.filter(status=Ticket.Status.ASSIGNED).count(),
            'in_progress': queryset.filter(status=Ticket.Status.IN_PROGRESS).count(),
            'on_hold': queryset.filter(status=Ticket.Status.ON_HOLD).count(),
            'resolved': queryset.filter(status=Ticket.Status.RESOLVED).count(),
            'closed': queryset.filter(status=Ticket.Status.CLOSED).count(),
            'overdue': sum(1 for ticket in queryset if ticket.is_overdue),
        }
        context['recent_tickets'] = queryset[:8]
        context['by_priority'] = queryset.values('priority').annotate(total=Count('id')).order_by('priority')
        context['by_technician'] = (
            queryset.filter(assigned_to__isnull=False)
            .values('assigned_to__username')
            .annotate(total=Count('id'))
            .order_by('assigned_to__username')
        )
        return context


class TicketBoardView(DashboardView):
    template_name = 'dashboard/board.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_base_queryset()
        rotations = ['rotate-left', 'rotate-soft-right', 'rotate-right', 'rotate-soft-left', 'rotate-flat']
        columns = []

        for status, label in Ticket.Status.choices:
            tickets = []
            for index, ticket in enumerate(queryset.filter(status=status)[:20]):
                ticket.card_rotation = rotations[index % len(rotations)]
                tickets.append(ticket)
            columns.append(
                {
                    'status': status,
                    'label': label,
                    'tickets': tickets,
                    'count': queryset.filter(status=status).count(),
                }
            )

        context['columns'] = columns
        return context
