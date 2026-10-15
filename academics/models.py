"""
Academic hierarchy models: AcademicYear, Semester, and Unit.
Enforces hierarchy limits:
- Max 6 Academic Years per user
- Max 3 Semesters per Academic Year
- Max 10 Units per Semester
"""

from django.db import models, transaction
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError


class AcademicYear(models.Model):
    """
    Academic Year model representing one academic year for a student.
    Limit: A user can have at most 6 academic years.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='academic_years',
        db_index=True
    )
    name = models.CharField(max_length=100, help_text="e.g. 'Year 1' or '2025/2026'")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    cover = models.CharField(
        max_length=30, blank=True, default='',
        help_text="Slug of the cover picture shown in the app"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        unique_together = ('user', 'name')
        verbose_name = 'Academic Year'
        verbose_name_plural = 'Academic Years'

    def clean(self):
        super().clean()
        if not self.pk:
            current_count = AcademicYear.objects.filter(user=self.user).count()
            if current_count >= 6:
                raise ValidationError({"detail": "You can have a maximum of 6 academic years."})
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError({"detail": "Start date cannot be after end date."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class Semester(models.Model):
    """
    Semester model belonging to an Academic Year.
    Limit: An academic year can have at most 3 semesters.
    """
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='semesters',
        db_index=True
    )
    name = models.CharField(max_length=100, help_text="e.g. 'Semester 1' or 'Term 2'")
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        unique_together = ('academic_year', 'name')
        verbose_name = 'Semester'
        verbose_name_plural = 'Semesters'

    def clean(self):
        super().clean()
        if not self.pk:
            current_count = Semester.objects.filter(academic_year=self.academic_year).count()
            if current_count >= 3:
                raise ValidationError({"detail": "An academic year can contain a maximum of 3 semesters."})

    def save(self, *args, **kwargs):
        self.full_clean()
        with transaction.atomic():
            # The very first semester a student creates becomes the active one.
            if not self.pk and not self.is_active:
                has_active = Semester.objects.filter(
                    academic_year__user_id=self.academic_year.user_id, is_active=True
                ).exists()
                if not has_active:
                    self.is_active = True
            super().save(*args, **kwargs)
            if self.is_active:
                # Only ONE active semester per student, across all academic years.
                Semester.objects.filter(
                    academic_year__user_id=self.academic_year.user_id, is_active=True
                ).exclude(pk=self.pk).update(is_active=False, updated_at=timezone.now())

    def __str__(self):
        return f"{self.name} - {self.academic_year.name}"


class Unit(models.Model):
    """
    Unit / Subject / Course model belonging to a Semester.
    Limit: A semester can have at most 10 units.
    """
    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name='units',
        db_index=True
    )
    name = models.CharField(max_length=200, help_text="e.g. 'Programming for Internet'")
    code = models.CharField(max_length=50, help_text="e.g. 'CS101'")
    description = models.TextField(blank=True, default='')
    lecturer_name = models.CharField(max_length=200, blank=True, default='', help_text="Lecturer's full name")
    lecturer_phone = models.CharField(max_length=30, blank=True, default='', help_text="Lecturer's phone number (optional)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        unique_together = ('semester', 'code')
        verbose_name = 'Unit'
        verbose_name_plural = 'Units'

    def clean(self):
        super().clean()
        if not self.pk:
            current_count = Unit.objects.filter(semester=self.semester).count()
            if current_count >= 10:
                raise ValidationError({"detail": "A semester can contain a maximum of 10 units."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name}"



class PlannerEvent(models.Model):
    """A class (repeats weekly) or a non-academic event on the student's planner."""

    KIND_CLASS = 'CLASS'
    KIND_EVENT = 'EVENT'
    KIND_CHOICES = [(KIND_CLASS, 'Class'), (KIND_EVENT, 'Event')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='planner_events')
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default=KIND_CLASS)
    title = models.CharField(max_length=150)
    unit = models.ForeignKey('Unit', null=True, blank=True, on_delete=models.SET_NULL,
                             related_name='planner_events')
    location = models.CharField(max_length=150, blank=True, default='')
    note = models.TextField(blank=True, default='')
    # One-off events use `date`; weekly ones use `weekday` (1=Mon ... 7=Sun).
    date = models.DateField(null=True, blank=True)
    weekday = models.PositiveSmallIntegerField(null=True, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    repeat_until = models.DateField(null=True, blank=True)
    remind_minutes_before = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['weekday', 'date', 'start_time']

    def __str__(self):
        return f'{self.title} ({self.kind})'
