from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.models import Profile

from .forms import (
    AssignTicketForm,
    TicketCommentForm,
    TicketCreateForm,
    TicketFileForm,
    TicketUpdateForm,
    TicketWorkForm,
)
from .models import Ticket
from .permissions import (
    can_comment_ticket,
    can_edit_ticket,
    can_update_work,
    can_upload_file,
    can_view_ticket,
    get_role,
    is_staff_manager,
)
from .services import add_history, assign_ticket, change_ticket_status


class TicketQuerysetMixin:
    def get_queryset(self):
        queryset = Ticket.objects.select_related('created_by', 'assigned_to')
        role = get_role(self.request.user)
        if role in {Profile.Role.SUPERVISOR, Profile.Role.ADMIN}:
            return queryset
        if role == Profile.Role.TECHNICIAN:
            return queryset.filter(assigned_to=self.request.user)
        return queryset.filter(created_by=self.request.user)


class TicketListView(LoginRequiredMixin, TicketQuerysetMixin, ListView):
    model = Ticket
    template_name = 'tickets/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 12

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        query = self.request.GET.get('q')
        if status:
            queryset = queryset.filter(status=status)
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(description__icontains=query) | Q(category__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = Ticket.Status.choices
        context['selected_status'] = self.request.GET.get('status', '')
        context['query'] = self.request.GET.get('q', '')
        return context


class TicketCreateView(LoginRequiredMixin, CreateView):
    model = Ticket
    form_class = TicketCreateForm
    template_name = 'tickets/ticket_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.status = Ticket.Status.PENDING
        form.instance.progress = Ticket.AUTO_PROGRESS[Ticket.Status.PENDING]
        response = super().form_valid(form)
        add_history(self.object, self.request.user, 'Ticket creado', '', self.object.title)
        messages.success(self.request, 'Ticket creado correctamente.')
        return response


class TicketDetailView(LoginRequiredMixin, DetailView):
    model = Ticket
    template_name = 'tickets/ticket_detail.html'
    context_object_name = 'ticket'

    def get_queryset(self):
        return Ticket.objects.select_related('created_by', 'assigned_to').prefetch_related('comments', 'files', 'history')

    def get_object(self, queryset=None):
        ticket = super().get_object(queryset)
        if not can_view_ticket(self.request.user, ticket):
            raise PermissionDenied
        return ticket

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ticket = self.object
        context['comment_form'] = TicketCommentForm()
        context['file_form'] = TicketFileForm()
        context['can_edit'] = can_edit_ticket(self.request.user, ticket)
        context['can_assign'] = is_staff_manager(self.request.user)
        context['can_work'] = can_update_work(self.request.user, ticket)
        context['can_upload'] = can_upload_file(self.request.user, ticket)
        context['can_close'] = is_staff_manager(self.request.user) and ticket.status == Ticket.Status.RESOLVED
        context['can_cancel'] = is_staff_manager(self.request.user) and ticket.status != Ticket.Status.CLOSED
        return context


class TicketUpdateView(LoginRequiredMixin, UpdateView):
    model = Ticket
    form_class = TicketUpdateForm
    template_name = 'tickets/ticket_form.html'

    def get_object(self, queryset=None):
        ticket = super().get_object(queryset)
        if not can_edit_ticket(self.request.user, ticket):
            raise PermissionDenied
        return ticket

    def form_valid(self, form):
        response = super().form_valid(form)
        add_history(self.object, self.request.user, 'Ticket editado', '', self.object.title)
        messages.success(self.request, 'Ticket actualizado correctamente.')
        return response


class TicketAssignView(LoginRequiredMixin, UpdateView):
    model = Ticket
    form_class = AssignTicketForm
    template_name = 'tickets/ticket_assign.html'

    def dispatch(self, request, *args, **kwargs):
        if not is_staff_manager(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = self.get_object()
        assign_ticket(self.object, form.cleaned_data['assigned_to'], self.request.user)
        messages.success(self.request, 'Ticket asignado correctamente.')
        return redirect(self.object)


class TicketWorkUpdateView(LoginRequiredMixin, UpdateView):
    model = Ticket
    form_class = TicketWorkForm
    template_name = 'tickets/ticket_work.html'

    def get_object(self, queryset=None):
        ticket = super().get_object(queryset)
        if not can_update_work(self.request.user, ticket):
            raise PermissionDenied
        return ticket

    def form_valid(self, form):
        ticket = self.get_object()
        change_ticket_status(
            ticket,
            form.cleaned_data['status'],
            form.cleaned_data.get('progress'),
            self.request.user,
        )
        messages.success(self.request, 'Estado y progreso actualizados.')
        return redirect(ticket)


@login_required
def add_comment(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if not can_comment_ticket(request.user, ticket):
        raise PermissionDenied
    form = TicketCommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.ticket = ticket
        comment.user = request.user
        comment.save()
        add_history(ticket, request.user, 'Comentario agregado', '', comment.comment[:80])
        messages.success(request, 'Comentario agregado.')
    else:
        messages.error(request, 'No se pudo agregar el comentario.')
    return redirect(ticket)


@login_required
def upload_file(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if not can_upload_file(request.user, ticket):
        raise PermissionDenied
    form = TicketFileForm(request.POST, request.FILES)
    if form.is_valid():
        ticket_file = form.save(commit=False)
        ticket_file.ticket = ticket
        ticket_file.uploaded_by = request.user
        ticket_file.save()
        add_history(ticket, request.user, 'Archivo adjuntado', '', ticket_file.file.name)
        messages.success(request, 'Archivo adjuntado.')
    else:
        messages.error(request, 'No se pudo subir el archivo.')
    return redirect(ticket)


@login_required
def close_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if not is_staff_manager(request.user):
        raise PermissionDenied
    if request.method == 'POST':
        change_ticket_status(ticket, Ticket.Status.CLOSED, 100, request.user)
        messages.success(request, 'Ticket cerrado correctamente.')
    return redirect(ticket)


@login_required
def cancel_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if not is_staff_manager(request.user):
        raise PermissionDenied
    if request.method == 'POST':
        change_ticket_status(ticket, Ticket.Status.CANCELED, 0, request.user)
        messages.success(request, 'Ticket cancelado.')
    return redirect(ticket)
