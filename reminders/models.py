"""
Reminder models for JK Scholar backend.
Supports automatic and manual reminders for CATs, Assignments, and standalone
"Other" notifications.

Enforces limit: 1 automatic + max 2 additional = max 3 reminders per assessment.
Standalone (OTHER category) reminders have no limit other than good sense.
"""

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class Reminder(models.Model):
    """
    Reminder model.

    - CAT_REMINDER / ASSIGNMENT_REMINDER: linked to an assessment.
    - OTHER: standalone notification (not tied to any assessment).

    Limit: At most 3 reminders per CAT or Assignment.
    OTHER reminders have no such limit.
    """
    class ReminderType(models.TextChoices):
        AUTOMATIC = 'AUTOMATIC', 'Automatic'
        MANUAL = 'MANUAL', 'Manual'

    class Category(models.TextChoices):
        CAT_REMINDER = 'CAT_REMINDER', 'CAT Reminder'
        ASSIGNMENT_REMINDER = 'ASSIGNMENT_REMINDER', 'Assignment Reminder'
        OTHER = 'OTHER', 'Other Notification'

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
    # Category makes the type explicit for filtering in the app
    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.OTHER,
        db_index=True
    )
    title = models.CharField(max_length=255)
    note = models.TextField(blank=True, default='', help_text='Optional note / description for this reminder')
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

    def clean(self):
        super().clean()

        # A reminder must not be linked to BOTH a CAT and an Assignment
        if self.cat and self.assignment:
            raise ValidationError({"detail": "A reminder cannot be associated with both a CAT and an Assignment."})

        # Auto-derive category from FK links if not set manually
        if self.cat and self.category not in (self.Category.CAT_REMINDER,):
            self.category = self.Category.CAT_REMINDER
        elif self.assignment and self.category not in (self.Category.ASSIGNMENT_REMINDER,):
            self.category = self.Category.ASSIGNMENT_REMINDER

        # Enforce max 3 reminders per assessment on creation
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
            source = "Other"
        return f"{self.title} ({source})"
