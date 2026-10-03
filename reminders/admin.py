"""
Django admin configuration for reminders app.
"""

from django.contrib import admin
from .models import Reminder


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'title', 'user', 'reminder_type',
        'reminder_datetime', 'is_completed', 'is_read', 'created_at'
    )
    list_filter = ('reminder_type', 'is_completed', 'is_read', 'reminder_datetime', 'created_at')
    search_fields = ('title', 'user__username', 'cat__title', 'assignment__title')
    ordering = ('-reminder_datetime',)
