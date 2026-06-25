from django import forms
from django.contrib.auth import get_user_model

from accounts.models import Profile

from .models import Ticket, TicketComment, TicketFile


class BootstrapFormMixin:
    def _apply_bootstrap(self):
        for field in self.fields.values():
            widget = field.widget
            css_class = 'form-select' if isinstance(widget, forms.Select) else 'form-control'
            if isinstance(widget, forms.CheckboxInput):
                css_class = 'form-check-input'
            widget.attrs['class'] = f"{widget.attrs.get('class', '')} {css_class}".strip()


class TicketCreateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ('title', 'description', 'category', 'priority', 'due_date')
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class TicketUpdateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ('title', 'description', 'category', 'priority', 'due_date', 'is_active')
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class AssignTicketForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ('assigned_to',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        User = get_user_model()
        self.fields['assigned_to'].queryset = User.objects.filter(
            profile__role=Profile.Role.TECHNICIAN,
            is_active=True,
        ).order_by('first_name', 'username')
        self._apply_bootstrap()


class TicketWorkForm(BootstrapFormMixin, forms.ModelForm):
    progress = forms.IntegerField(required=False, min_value=0, max_value=100)

    class Meta:
        model = Ticket
        fields = ('status', 'progress')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
        self.fields['progress'].help_text = 'Dejalo vacio para usar el progreso automatico del estado.'


class TicketCommentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = ('comment',)
        widgets = {'comment': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class TicketFileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = TicketFile
        fields = ('file',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
