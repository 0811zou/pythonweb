from django.contrib import admin
from .models import TraceEvent


@admin.register(TraceEvent)
class TraceEventAdmin(admin.ModelAdmin):
    list_display = ('batch', 'event_type', 'title', 'occurred_at', 'data_hash')
    readonly_fields = ('previous_hash', 'data_hash', 'created_at')
