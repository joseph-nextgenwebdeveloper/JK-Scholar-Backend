"""
Reminder models for Study Vault backend.
Supports automatic and manual reminders for CATs and Assignments.
Enforces limit: 1 automatic + max 2 additional = max 3 reminders per assessment.
"""

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q


class Reminder(models.Model):
    """
    Reminder model linked to either a CAT or an Assignment.
    Limit: At most 3 reminders per CAT or Assignment.
    """
    class ReminderType(models.TextChoices):
        AUTOMATIC = 'AUTOMATIC', 'Automatic'
        MANUAL = 'MANUAL', 'Manual'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reminders',
        db_index=True
    )
    cat = models.ForeignKey(
        'assessments.CAT',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='reminders',
        db_index=True
    )
    assignment = models.ForeignKey(
        'assessments.Assignment',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='reminders',
        db_index=True
    )
    title = models.CharField(max_length=255)
    reminder_datetime = models.DateTimeField(db_index=True)
    reminder_type = models.CharField(
        max_length=20,
        choices=ReminderType.choices,
        default=ReminderType.MANUAL
    )
    is_completed = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ['reminder_datetime', 'created_at']
        verbose_name = 'Reminder'
        verbose_name_plural = 'Reminders'
        constraints = [
            models.CheckConstraint(
                condition=~(models.Q(cat__isnull=False) & models.Q(assignment__isnull=False)),
                name='reminder_not_both_cat_and_assignment'
            )
        ]

    def clean(self):
        super().clean()
        if self.cat and self.assignment:
            raise ValidationError({"detail": "A reminder cannot be associated with both a CAT and an Assignment."})

        # Enforce maximum 3 reminders rule on creation for CAT / Assignment
        if not self.pk:
            if self.cat and Reminder.objects.filter(cat=self.cat).count() >= 3:
                raise ValidationError({"detail": "A CAT or Assignment can have a maximum of 3 reminders."})
            if self.assignment and Reminder.objects.filter(assignment=self.assignment).count() >= 3:
                raise ValidationError({"detail": "A CAT or Assignment can have a maximum of 3 reminders."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.cat:
            source = f"CAT: {self.cat.title}"
        elif self.assignment:
            source = f"Assignment: {self.assignment.title}"
        else:
            source = "Custom"
        return f"{self.title} ({source})"
