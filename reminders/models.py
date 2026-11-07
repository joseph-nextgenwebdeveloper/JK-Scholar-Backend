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
        CLASS_REMINDER = 'CLASS_REMINDER', 'Class / Event Reminder'

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
    # Set for reminders generated from a timetable class / event. Deleting the class
    # deletes its reminder, editing the class re-syncs it (see reminders/signals.py).
    planner_event = models.ForeignKey(
        'academics.PlannerEvent',
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
    reminder_datetime = models.DateTimeField(null=True, blank=True, db_index=True)
    reminder_type = models.CharField(
        max_length=20,
        choices=ReminderType.choices,
        default=ReminderType.MANUAL
    )
    repeat_days = models.CharField(
        max_length=20, blank=True, default='',
        help_text="Weekdays the alarm repeats on, comma-separated ISO numbers (1=Mon..7=Sun). Empty = one-time."
    )
    repeat_until = models.DateField(
        null=True, blank=True,
        help_text="Last date a repeating reminder may ring (e.g. the end of the semester). Empty = no end."
    )
    is_completed = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    # True once the student edited the time / title themselves. Automatic reminders that were
    # edited are no longer overwritten when the CAT / assignment is saved again.
    user_modified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ['reminder_datetime', 'created_at']
        verbose_name = 'Reminder'
        verbose_name_plural = 'Reminders'

    def clean(self):
        super().clean()

        # A reminder must not be linked to BOTH a CAT and an Assignment
        if self.planner_event_id:
            self.category = self.Category.CLASS_REMINDER
        elif self.cat and self.assignment:
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
