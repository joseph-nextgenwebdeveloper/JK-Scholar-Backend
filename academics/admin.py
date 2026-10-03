"""
Django admin configuration for academics app.
"""

from django.contrib import admin
from .models import AcademicYear, Semester, Unit


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'start_date', 'end_date', 'created_at')
    list_filter = ('start_date', 'end_date', 'created_at')
    search_fields = ('name', 'user__username', 'user__email')
    ordering = ('-created_at',)


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'academic_year', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'academic_year__name', 'academic_year__user__username')
    ordering = ('-created_at',)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name', 'semester', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('code', 'name', 'semester__name', 'semester__academic_year__user__username')
    ordering = ('-created_at',)
