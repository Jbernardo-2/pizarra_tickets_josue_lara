from django.contrib import admin

from .models import Ticket, TicketComment, TicketFile, TicketHistory


class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 0
    readonly_fields = ('created_at',)


class TicketFileInline(admin.TabularInline):
    model = TicketFile
    extra = 0
    readonly_fields = ('uploaded_at',)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'status', 'priority', 'progress', 'created_by', 'assigned_to', 'due_date')
    list_filter = ('status', 'priority', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'category', 'created_by__username', 'assigned_to__username')
    inlines = (TicketCommentInline, TicketFileInline)


@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'action', 'user', 'old_value', 'new_value', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('ticket__title', 'action', 'user__username')


admin.site.register(TicketComment)
admin.site.register(TicketFile)

# Register your models here.
