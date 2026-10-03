"""
Django admin configuration for assessments app.
"""

from django.contrib import admin
from .models import CAT, Assignment


@admin.register(CAT)
class CATAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'unit', 'cat_date', 'deadline', 'created_at')
    list_filter = ('cat_date', 'created_at')
    search_fields = ('title', 'description', 'unit__name', 'unit__code', 'unit__semester__academic_year__user__username')
    ordering = ('cat_date',)


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'unit', 'deadline', 'status', 'submission_date', 'created_at')
    list_filter = ('status', 'deadline', 'created_at')
    search_fields = ('title', 'description', 'unit__name', 'unit__code', 'unit__semester__academic_year__user__username')
    ordering = ('deadline',)
