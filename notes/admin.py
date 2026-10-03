"""
Django admin configuration for notes app.
"""

from django.contrib import admin
from .models import Note


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'unit', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'content', 'unit__name', 'unit__code', 'unit__semester__academic_year__user__username')
    ordering = ('-updated_at',)
